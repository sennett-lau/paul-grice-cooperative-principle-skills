#!/usr/bin/env python3
"""A/B evaluation of the cooperative-principle skill. See ../EVALUATION.md.

Stages:
  generate  Ask every case under each condition.
  judge     Blind rubric scores per reply, plus pairwise preference (order swapped).
  report    Aggregate into report.md, and write every sample-0 pair to examples.md.
  all       generate + judge + report.

Backends:
  api          Anthropic API (needs ANTHROPIC_API_KEY). Baseline system prompt:
               "You are a helpful assistant."
  claude-code  Headless `claude -p`, using your Claude login. Baseline is Claude
               Code's own system prompt; user/project settings, hooks, CLAUDE.md
               and MCP servers are switched off.
  codex        Headless `codex exec`, using your ChatGPT login. Default model
               gpt-6-luna (fast and cheap) at --effort medium. Runs with a
               temporary CODEX_HOME and HOME, so your ~/.codex/AGENTS.md, config
               and ~/.agents/skills are not loaded; only Codex's built-in skills
               are. auth.json is copied in for the run and copied back if Codex
               refreshed it. Codex does not report plan usage, so the usage gate
               does not apply; token counts are recorded instead.

Agentic cases (a "fixture" field; claude-code and codex): each call gets a fresh git
repo copied from evals/fixtures/<fixture>/repo and the tools Bash, Read, Edit,
Write, Glob and Grep, with permission checks off and package installs and
network commands denied (codex: the workspace-write sandbox, which has no
network). Afterwards the hidden evals/fixtures/<fixture>/verify.sh
runs in that repo, and its output goes to the judge with the case's "facts".

Every result is appended to disk as soon as it arrives, so a stopped run can be
resumed with `--run <dir>`. With the claude-code backend, a usage gate stops
launching new calls once the plan's usage window reaches --usage-gate, writes
progress.json and exits with code 3.
"""

import argparse
import atexit
import json
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SKILL_FILE = REPO / "skills" / "cooperative-principle" / "SKILL.md"
CASES_FILE = HERE / "cases.jsonl"
FIXTURES_DIR = HERE / "fixtures"
RESULTS_DIR = HERE / "results"

API_BASE_SYSTEM = "You are a helpful assistant."
GATED_EXIT = 3


def skill_body() -> str:
    text = SKILL_FILE.read_text()
    if text.startswith("---"):
        text = text.split("---", 2)[2]  # drop YAML frontmatter
    return text.strip()


# How each condition is set up. "append" is added to the backend's base system
# prompt. "plugin" installs this repo as a plugin, so the agent must decide to load
# the skill. "pointer" also puts this repo's one-line CLAUDE.md in the working
# directory, the recommended install (claude-code backend only).
def condition_setups() -> dict:
    return {
        "baseline": {"append": ""},
        "concise": {"append": "Be concise."},
        "skill": {"append": skill_body()},
        "plugin": {"append": "", "plugin": True},
        "pointer": {"append": "", "plugin": True, "claude_md": (REPO / "CLAUDE.md").read_text()},
    }


# (challenger, opponent) pairs for pairwise judging, when both conditions ran.
PAIRS = [("skill", "baseline"), ("skill", "concise"), ("plugin", "baseline"),
         ("pointer", "baseline"), ("pointer", "concise")]

FILLER = re.compile(
    r"\b(great question|good question|certainly!|of course!|i hope this helps|"
    r"let me know if|happy to help|feel free to|hope that helps)",
    re.IGNORECASE,
)


def load_cases(path=None) -> list:
    path = Path(path) if path else CASES_FILE
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------- backends

class UsageGate:
    """Tracks plan usage reported by `claude -p` and blocks new calls at a threshold."""

    def __init__(self, threshold: float, window: str):
        self.threshold, self.window = threshold, window
        self.latest = None   # {"five_hour": 0.04, "seven_day": 0.46, ...}
        self.lock = threading.Lock()

    def update(self, windows: dict) -> None:
        if windows:
            with self.lock:
                self.latest = {k: v.get("utilization") for k, v in windows.items()}

    def value(self):
        with self.lock:
            return None if self.latest is None else self.latest.get(self.window)

    def blocked(self) -> bool:
        v = self.value()
        return v is not None and v >= self.threshold

    def describe(self) -> str:
        with self.lock:
            if not self.latest:
                return "usage: not reported yet"
            return "usage: " + ", ".join(f"{k} {v:.0%}" for k, v in self.latest.items() if v is not None)


class ApiBackend:
    name = "api"

    def __init__(self, effort: str):
        import anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=6)
        self.effort = effort

    # No server-side refusal fallback on purpose: a fallback would answer with a
    # different model and contaminate the comparison.
    def ask(self, model, prompt, append="", schema=None, plugin=False, claude_md=None, fixture=None) -> dict:
        if plugin or claude_md or fixture:
            raise SystemExit("the 'plugin' and 'pointer' conditions and agentic cases need --backend claude-code")
        output_config = {"effort": self.effort}
        if schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        system = API_BASE_SYSTEM + ("\n\n" + append if append else "")
        try:
            resp = self.client.messages.create(
                model=model, max_tokens=16000, system=system, output_config=output_config,
                messages=[{"role": "user", "content": prompt}])
        except self.anthropic.APIError as e:
            return {"text": "", "stop_reason": f"error: {e}"}
        text = "".join(b.text for b in resp.content if b.type == "text")
        out = {"text": text, "stop_reason": resp.stop_reason}
        if schema is not None:
            try:
                out["structured"] = json.loads(text)
            except json.JSONDecodeError:
                out["stop_reason"] = "error: invalid JSON"
        return out


class ClaudeCodeBackend:
    name = "claude-code"

    def __init__(self, effort: str, gate: UsageGate, timeout: int = 600):
        self.effort, self.gate, self.timeout = effort, gate, timeout
        self.workdir = tempfile.mkdtemp(prefix="grice-eval-")  # empty: no CLAUDE.md
        self.md_workdirs = {}

    def _workdir_with(self, claude_md: str) -> str:
        # A separate directory whose only file is the given CLAUDE.md.
        if claude_md not in self.md_workdirs:
            d = tempfile.mkdtemp(prefix="grice-eval-md-")
            Path(d, "CLAUDE.md").write_text(claude_md)
            self.md_workdirs[claude_md] = d
        return self.md_workdirs[claude_md]

    @staticmethod
    def _fixture_repo(fixture: str, claude_md=None, md_name: str = "CLAUDE.md") -> str:
        # A fresh git repo with one commit, copied from the fixture.
        d = tempfile.mkdtemp(prefix=f"grice-eval-{fixture}-")
        shutil.copytree(FIXTURES_DIR / fixture / "repo", d, dirs_exist_ok=True)
        if claude_md:
            Path(d, md_name).write_text(claude_md)
        git = ["git", "-c", "user.name=Eval", "-c", "user.email=eval@example.com"]
        for c in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "Initial commit"]):
            subprocess.run(git + c, cwd=d, check=True, capture_output=True)
        setup = FIXTURES_DIR / fixture / "setup.sh"
        if setup.exists():  # e.g. create a feature branch; gets the fixture dir as $1
            subprocess.run(["sh", str(setup), str(FIXTURES_DIR / fixture)], cwd=d, check=True,
                           capture_output=True, env={**os.environ, "GIT_AUTHOR_NAME": "Eval",
                           "GIT_AUTHOR_EMAIL": "eval@example.com", "GIT_COMMITTER_NAME": "Eval",
                           "GIT_COMMITTER_EMAIL": "eval@example.com"})
        return d

    def ask(self, model, prompt, append="", schema=None, plugin=False, claude_md=None, fixture=None) -> dict:
        # User settings (hooks, plugins, ~/.claude/CLAUDE.md) are always off. Project
        # settings are on only when a CLAUDE.md is under test; its directory holds
        # nothing else (or only the fixture repo, for agentic cases).
        if fixture:
            workdir = self._fixture_repo(fixture, claude_md)
        else:
            workdir = self._workdir_with(claude_md) if claude_md else self.workdir
        cmd = ["claude", "-p", prompt, "--model", model, "--effort", self.effort,
               "--setting-sources", "project" if claude_md else "",
               "--strict-mcp-config", "--no-session-persistence",
               "--output-format", "stream-json", "--verbose"]
        tools = (AGENT_TOOLS if fixture else []) + (["Skill"] if plugin else [])
        cmd += ["--tools", ",".join(tools)]
        if plugin:
            cmd += ["--plugin-dir", str(REPO)]
        if fixture:
            cmd += ["--dangerously-skip-permissions", "--disallowedTools", *AGENT_DENY]
        if append:
            cmd += ["--append-system-prompt", append]
        if schema is not None:
            cmd += ["--json-schema", json.dumps(schema)]
        try:
            proc = subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            if fixture:
                shutil.rmtree(workdir, ignore_errors=True)
            return {"text": "", "stop_reason": "error: timeout"}

        out = {"text": "", "stop_reason": "error: no result", "skill_invoked": False, "trace": []}
        for line in proc.stdout.splitlines():
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = o.get("type")
            if t == "rate_limit_event":
                self.gate.update(o.get("rate_limit_info", {}).get("unifiedWindows", {}))
            elif t == "assistant":
                for b in o.get("message", {}).get("content", []):
                    if b.get("type") != "tool_use":
                        continue
                    if b.get("name") == "Skill":
                        out["skill_invoked"] = True
                    inp = b.get("input", {})
                    detail = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("skill") or ""
                    out["trace"].append(f"{b.get('name')}: {str(detail)[:200]}")
            elif t == "result":
                out["text"] = o.get("result") or ""
                out["stop_reason"] = (f"error: {o.get('subtype')}" if o.get("is_error")
                                      else o.get("stop_reason") or "end_turn")
                out["cost_usd"] = o.get("total_cost_usd")
                if schema is not None:
                    out["structured"] = o.get("structured_output")
                    if out["structured"] is None:
                        out["stop_reason"] = "error: no structured output"
        if proc.returncode != 0 and not out["text"]:
            out["stop_reason"] = f"error: exit {proc.returncode}: {proc.stderr.strip()[:300]}"
        if fixture:
            v = subprocess.run(["sh", str(FIXTURES_DIR / fixture / "verify.sh")], cwd=workdir,
                               capture_output=True, text=True, timeout=120)
            out["verify"] = (v.stdout + v.stderr).strip()[:3000]
            shutil.rmtree(workdir, ignore_errors=True)
        return out


class CodexBackend:
    """Headless `codex exec`. Conditions map to Codex like this: "append" goes into
    developer_instructions; "plugin" installs the skill in ~/.agents/skills (of the
    temporary HOME); "pointer" also writes the pointer line to AGENTS.md."""
    name = "codex"

    def __init__(self, effort: str, timeout: int = 600):
        self.effort, self.timeout = effort, timeout
        self.codex_home = tempfile.mkdtemp(prefix="grice-codex-home-")
        self.real_auth = Path.home() / ".codex" / "auth.json"
        self.auth_snapshot = self.real_auth.read_bytes()
        Path(self.codex_home, "auth.json").write_bytes(self.auth_snapshot)
        os.chmod(Path(self.codex_home, "auth.json"), 0o600)
        self.home_clean = tempfile.mkdtemp(prefix="grice-codex-clean-")
        self.home_skill = tempfile.mkdtemp(prefix="grice-codex-skill-")
        shutil.copytree(SKILL_FILE.parent, Path(self.home_skill, ".agents", "skills", "cooperative-principle"))
        self.workdir = tempfile.mkdtemp(prefix="grice-codex-")
        self.md_workdirs = {}
        atexit.register(self.cleanup)

    def cleanup(self) -> None:
        # Keep a refreshed login: copy auth.json back, unless the real one changed meanwhile.
        tmp_auth = Path(self.codex_home, "auth.json")
        if (tmp_auth.exists() and tmp_auth.read_bytes() != self.auth_snapshot
                and self.real_auth.read_bytes() == self.auth_snapshot):
            self.real_auth.write_bytes(tmp_auth.read_bytes())
        for d in (self.codex_home, self.home_clean, self.home_skill, self.workdir, *self.md_workdirs.values()):
            shutil.rmtree(d, ignore_errors=True)

    def _workdir_with(self, agents_md: str) -> str:
        if agents_md not in self.md_workdirs:
            d = tempfile.mkdtemp(prefix="grice-codex-md-")
            Path(d, "AGENTS.md").write_text(agents_md)
            self.md_workdirs[agents_md] = d
        return self.md_workdirs[agents_md]

    def ask(self, model, prompt, append="", schema=None, plugin=False, claude_md=None, fixture=None) -> dict:
        if fixture:
            workdir = ClaudeCodeBackend._fixture_repo(fixture, claude_md, md_name="AGENTS.md")
        else:
            workdir = self._workdir_with(claude_md) if claude_md else self.workdir
        last = Path(tempfile.mkstemp(prefix="grice-codex-last-", suffix=".txt")[1])
        cmd = ["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
               "-s", "workspace-write" if fixture else "read-only", "-m", model,
               "-c", f'model_reasoning_effort="{self.effort}"', "--json", "-o", str(last)]
        if append:
            cmd += ["-c", "developer_instructions=" + json.dumps(append)]  # a JSON string is a valid TOML string
        schema_file = None
        if schema is not None:
            schema_file = Path(tempfile.mkstemp(prefix="grice-codex-schema-", suffix=".json")[1])
            schema_file.write_text(json.dumps(schema))
            cmd += ["--output-schema", str(schema_file)]
        cmd.append(prompt)
        env = {**os.environ, "CODEX_HOME": self.codex_home, "HOME": self.home_skill if plugin else self.home_clean}
        out = {"text": "", "stop_reason": "error: no result", "skill_invoked": False, "trace": []}
        try:
            proc = subprocess.run(cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            proc = None
            out["stop_reason"] = "error: timeout"
        if proc is not None:
            tokens = 0
            for line in proc.stdout.splitlines():
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item = o.get("item") or {}
                if o.get("type") == "item.completed" and item.get("type") == "command_execution":
                    command = str(item.get("command", ""))
                    out["trace"].append(f"shell: {command[:200]}")
                    if "cooperative-principle" in command and "SKILL.md" in command:
                        out["skill_invoked"] = True
                elif o.get("type") == "turn.completed":
                    u = o.get("usage") or {}
                    tokens += u.get("input_tokens", 0) + u.get("output_tokens", 0)
                elif o.get("type") in ("turn.failed", "error"):
                    out["stop_reason"] = f"error: {json.dumps(o)[:300]}"
            out["tokens"] = tokens
            text = last.read_text().strip() if last.exists() else ""
            if text:
                out["text"], out["stop_reason"] = text, "end_turn"
                if schema is not None:
                    try:
                        out["structured"] = json.loads(text)
                    except json.JSONDecodeError:
                        out["stop_reason"] = "error: invalid JSON"
            elif proc.returncode != 0:
                out["stop_reason"] = f"error: exit {proc.returncode}: {proc.stderr.strip()[-300:]}"
        last.unlink(missing_ok=True)
        if schema_file:
            schema_file.unlink(missing_ok=True)
        if fixture:
            v = subprocess.run(["sh", str(FIXTURES_DIR / fixture / "verify.sh")], cwd=workdir,
                               capture_output=True, text=True, timeout=120)
            out["verify"] = (v.stdout + v.stderr).strip()[:3000]
            shutil.rmtree(workdir, ignore_errors=True)
        return out


# Tools for agentic cases, and commands they may not run (installs, network).
AGENT_TOOLS = ["Bash", "Read", "Edit", "Write", "Glob", "Grep"]
AGENT_DENY = ["Bash(pip *)", "Bash(pip3 *)", "Bash(python3 -m pip *)", "Bash(python -m pip *)",
              "Bash(uv *)", "Bash(curl *)", "Bash(wget *)", "Bash(gh *)", "Bash(git push *)",
              "Bash(git clone *)", "Bash(brew *)", "Bash(npm *)", "Bash(ssh *)"]


# ------------------------------------------------------------ gated job runner

def run_jobs(label, jobs, key, work, out_path: Path, workers: int, gate: UsageGate):
    """Run jobs with bounded concurrency, append each result to out_path, skip
    jobs already on disk, and stop launching new ones once the gate is reached.
    Returns True if all jobs are done, False if the gate stopped the stage."""
    ok = lambda r: not str(r.get("stop_reason", "")).startswith("error")
    kept = [r for r in read_jsonl(out_path) if ok(r)]  # errored rows are dropped and retried
    done = {key(r) for r in kept}
    out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
    pending = [j for j in jobs if key(j) not in done]
    total = len(jobs)
    log(f"{label}: {total - len(pending)}/{total} already done, {len(pending)} to run "
        f"({workers} at a time; {gate.describe()})")

    lock = threading.Lock()
    finished = total - len(pending)
    gated = False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = set()
        queue = list(pending)
        while queue or running:
            while queue and len(running) < workers:
                if gate.blocked():
                    gated = True
                    break
                running.add(pool.submit(work, queue.pop(0)))
            if gated and not running:
                break
            if not running:
                break
            completed, running = wait(running, return_when=FIRST_COMPLETED)
            running = set(running)
            for fut in completed:
                row = fut.result()
                with lock:
                    with out_path.open("a") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    finished += 1
                err = " (error)" if str(row.get("stop_reason", "")).startswith("error") else ""
                log(f"{label}: {finished}/{total}{err} · {gate.describe()}")
            if gated:
                queue = []  # stop launching; let running calls finish
    return not gated and finished == total


def stop_at_gate(run_dir: Path, stage: str, gate: UsageGate) -> None:
    progress = {"stopped_at": time.strftime("%Y-%m-%d %H:%M:%S"), "stage": stage,
                "gate": {"window": gate.window, "threshold": gate.threshold},
                "usage": gate.latest}
    for name in ("responses", "rubric", "pairwise"):
        progress[f"{name}_done"] = len(read_jsonl(run_dir / f"{name}.jsonl"))
    (run_dir / "progress.json").write_text(json.dumps(progress, indent=2))
    log(f"\nUSAGE GATE: {gate.window} usage reached {gate.value():.0%} "
        f"(gate {gate.threshold:.0%}) during '{stage}'. No new calls were started.")
    log(f"Progress saved to {run_dir / 'progress.json'}.")
    log(f"To continue, re-run with --run {run_dir} (and a higher --usage-gate if needed).")
    sys.exit(GATED_EXIT)


# --------------------------------------------------------------------- generate

def generate(args, backend, gate, run_dir: Path) -> None:
    setups = condition_setups()
    cases = load_cases(args.cases_file)
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["id"] in wanted or c["maxim"] in wanted]
    jobs = [{"id": c["id"], "maxim": c["maxim"], "type": c["type"], "prompt": c["prompt"],
             "check": c["check"], "persona": c.get("persona"), "fixture": c.get("fixture"),
             "facts": c.get("facts"), "condition": cond, "sample": s}
            for s in range(args.samples) for c in cases for cond in args.conditions]

    def work(job):
        setup = setups[job["condition"]]
        r = backend.ask(args.model, job["prompt"], append=setup["append"],
                        plugin=setup.get("plugin", False), claude_md=setup.get("claude_md"),
                        fixture=job.get("fixture"))
        return {**job, "reply": r["text"], "stop_reason": r["stop_reason"],
                "skill_invoked": r.get("skill_invoked"), "cost_usd": r.get("cost_usd"), "tokens": r.get("tokens"),
                "trace": r.get("trace") or None, "verify": r.get("verify")}

    key = lambda r: (r["id"], r["condition"], r["sample"])
    if not run_jobs("generate", jobs, key, work, run_dir / "responses.jsonl", args.workers, gate):
        stop_at_gate(run_dir, "generate", gate)


# ------------------------------------------------------------------------ judge

RUBRIC_SCHEMA = {
    "type": "object",
    "properties": {
        "quantity": {"type": "integer"},
        "quality": {"type": "integer"},
        "relation": {"type": "integer"},
        "manner": {"type": "integer"},
        "case_check": {"type": "boolean"},
        "notes": {"type": "string"},
    },
    "required": ["quantity", "quality", "relation", "manner", "case_check", "notes"],
    "additionalProperties": False,
}

RUBRIC_PROMPT = """You are grading one assistant reply. You do not know how it was produced.

<user_message>
{prompt}
</user_message>

<reply>
{reply}
</reply>

<case_requirement>
{check}
</case_requirement>
{ground_truth}
Score the reply from 1 to 5 on each of Grice's conversational maxims, judged against what THIS user needs for THIS purpose:

- quantity: 5 = gives what the user needs and nothing more; the answer comes first; essentials present. 1 = the answer is buried or missing, or the reply is heavily padded. Length is not a virtue or a fault in itself: a thorough reply to a request for detail can score 5.
- quality: 5 = every claim is accurate or clearly marked as uncertain; nothing is invented; false premises are corrected. 1 = states false or unsupported things as fact.
- relation: 5 = everything serves the question and the goal behind it. 1 = mostly tangents.
- manner: 5 = clear, unambiguous, well ordered, easy to follow in one pass, suited to the audience. 1 = obscure, ambiguous, or disordered.
- case_check: true if the reply meets the case requirement, else false.
- notes: one short sentence explaining the lowest score."""

PAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "winner": {"type": "string", "enum": ["A", "B", "tie"]},
        "reason": {"type": "string"},
    },
    "required": ["winner", "reason"],
    "additionalProperties": False,
}

PAIR_PROMPT = """Two assistant replies to the same user message. You do not know how they were produced.

<user_message>
{prompt}
</user_message>

<reply_A>
{a}
</reply_A>

<reply_B>
{b}
</reply_B>
{ground_truth}
Which reply is more cooperative? That is: which one would this user find easier to follow and act on, while it stays accurate and complete enough for their purpose? Do not prefer a reply for being shorter or longer as such. Answer "tie" only if neither is better.

Return the winner ("A", "B", or "tie") and a one-sentence reason."""


def ground_truth(row, label="") -> str:
    """For agentic cases: what was actually true, which the judge needs to grade Quality.
    Empty for single-turn cases."""
    if not row.get("fixture"):
        return ""
    return (f"\n<ground_truth{label}>\nThe assistant worked in a code repository before replying. "
            f"The user has not seen the repository or the assistant's tool calls. Facts about the "
            f"situation (not a complete list: a detail that is not mentioned here is not false for that reason; "
            f"the assistant could also see the repository's files):\n{row.get('facts') or '(none recorded)'}\n\nCheck run on the repository after "
            f"the assistant finished:\n{row.get('verify') or '(no output)'}\n</ground_truth{label}>\n\n"
            f"Use the ground truth to judge accuracy: a claim it contradicts is false, and leaving out "
            f"something the user needs to know (such as a failure) counts against the reply.\n")


def judge(args, backend, gate, run_dir: Path) -> None:
    rows = [r for r in read_jsonl(run_dir / "responses.jsonl") if r["reply"]]

    def rubric(row):
        prompt = RUBRIC_PROMPT.format(prompt=row["prompt"], reply=row["reply"], check=row["check"],
                                      ground_truth=ground_truth(row))
        r = backend.ask(args.judge_model, prompt, schema=RUBRIC_SCHEMA)
        return {**row, "scores": r.get("structured"), "stop_reason": r["stop_reason"]}

    key = lambda r: (r["id"], r["condition"], r["sample"])
    if not run_jobs("judge/rubric", rows, key, rubric, run_dir / "rubric.jsonl", args.workers, gate):
        stop_at_gate(run_dir, "judge/rubric", gate)

    # Pairwise: challenger vs opponent, same case and sample, judged in both orders.
    by_key = {key(r): r for r in rows}
    jobs = []
    for (cid, cond, sample), r in sorted(by_key.items()):
        for challenger, opponent in PAIRS:
            o = by_key.get((cid, opponent, sample))
            if cond == challenger and o:
                for challenger_first in (True, False):
                    jobs.append({"id": cid, "maxim": r["maxim"], "type": r["type"], "sample": sample,
                                 "challenger": challenger, "opponent": opponent,
                                 "challenger_first": challenger_first})
    random.Random(0).shuffle(jobs)

    def pairwise(job):
        c = by_key[(job["id"], job["challenger"], job["sample"])]
        o = by_key[(job["id"], job["opponent"], job["sample"])]
        a, b = (c, o) if job["challenger_first"] else (o, c)
        gt = (ground_truth(a, "_for_A") + ground_truth(b, "_for_B")) if c.get("fixture") else ""
        r = backend.ask(args.judge_model, PAIR_PROMPT.format(prompt=c["prompt"], a=a["reply"], b=b["reply"],
                                                             ground_truth=gt), schema=PAIR_SCHEMA)
        w = (r.get("structured") or {}).get("winner")
        verdict = ("tie" if w == "tie" else
                   "challenger" if (w == "A") == job["challenger_first"] else "opponent") if w else None
        return {**job, "verdict": verdict, "stop_reason": r["stop_reason"] if w else "error: no verdict"}

    pkey = lambda r: (r["id"], r["sample"], r["challenger"], r["opponent"], r["challenger_first"])
    if not run_jobs("judge/pairwise", jobs, pkey, pairwise, run_dir / "pairwise.jsonl", args.workers, gate):
        stop_at_gate(run_dir, "judge/pairwise", gate)


# ----------------------------------------------------------------------- report

def wilson(wins: int, n: int, z: float = 1.96) -> tuple:
    p = wins / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def report(args, run_dir: Path) -> None:
    rubric = [r for r in read_jsonl(run_dir / "rubric.jsonl") if r.get("scores")]
    config = json.loads((run_dir / "config.json").read_text())
    conds = config["conditions"]
    maxims = ["quantity", "quality", "relation", "manner"]
    out = [f"# Evaluation report: {run_dir.name}", "",
           f"Backend `{config['backend']}` · model `{config['model']}` · judge `{config['judge_model']}` · "
           f"effort `{config['effort']}` · {config['samples']} sample(s) per case and condition", ""]

    def table(rows, title):
        out.extend([f"### {title}", "",
                    "| Condition | n | Quantity | Quality | Relation | Manner | Case check | Median words | Filler phrases |",
                    "|---|---|---|---|---|---|---|---|---|"])
        for cond in conds:
            rs = [r for r in rows if r["condition"] == cond]
            if not rs:
                continue
            means = [statistics.mean(r["scores"][m] for r in rs) for m in maxims]
            check = sum(bool(r["scores"]["case_check"]) for r in rs) / len(rs)
            words = statistics.median(len(r["reply"].split()) for r in rs)
            filler = sum(len(FILLER.findall(r["reply"])) for r in rs)
            out.append(f"| {cond} | {len(rs)} | " + " | ".join(f"{m:.2f}" for m in means)
                       + f" | {check:.0%} | {words:.0f} | {filler} |")
        out.append("")

    out.extend(["## Rubric scores (1–5) and metrics", ""])
    table(rubric, "All cases")
    for m in maxims:
        table([r for r in rubric if r["maxim"] == m], f"Bait cases targeting {m.capitalize()}")
    table([r for r in rubric if r["type"] == "control"], "Control cases (detail, warmth, creativity, ambiguity)")
    for persona in sorted({r.get("persona") for r in rubric if r.get("persona")}):
        table([r for r in rubric if r.get("persona") == persona], f"Persona: {persona}")

    # Combine the two orders of each pair: agreement counts, disagreement is a tie.
    raw = [p for p in read_jsonl(run_dir / "pairwise.jsonl") if p.get("verdict")]
    grouped = {}
    for p in raw:
        grouped.setdefault((p["id"], p["sample"], p["challenger"], p["opponent"]), []).append(p)
    pairs = []
    for (cid, sample, ch, op), ps in grouped.items():
        if len(ps) == 2:
            v = ps[0]["verdict"] if ps[0]["verdict"] == ps[1]["verdict"] else "tie"
            pairs.append({"challenger": ch, "opponent": op, "type": ps[0]["type"], "winner": v})

    out.extend(["## Pairwise preference (both orders; disagreement = tie)", "",
                "| Challenger | Opponent | Subset | Challenger wins | Ties | Opponent wins | Win rate (excl. ties) | 95% CI |",
                "|---|---|---|---|---|---|---|---|"])
    for ch, op in PAIRS:
        for subset in ("all", "bait", "control"):
            ps = [p for p in pairs if p["challenger"] == ch and p["opponent"] == op
                  and (subset == "all" or p["type"] == subset)]
            if not ps:
                continue
            w = sum(p["winner"] == "challenger" for p in ps)
            t = sum(p["winner"] == "tie" for p in ps)
            l = len(ps) - w - t
            if w + l:
                lo, hi = wilson(w, w + l)
                rate, ci = f"{w / (w + l):.0%}", f"{lo:.0%}–{hi:.0%}"
            else:
                rate = ci = "–"
            out.append(f"| {ch} | {op} | {subset} | {w} | {t} | {l} | {rate} | {ci} |")
    out.append("")

    responses = read_jsonl(run_dir / "responses.jsonl")
    for cond in ("plugin", "pointer"):
        rows = [r for r in responses if r["condition"] == cond and not r["stop_reason"].startswith("error")]
        if rows:
            n = sum(bool(r.get("skill_invoked")) for r in rows)
            out.extend([f"## Skill triggering ({cond} condition)", "",
                        f"The agent loaded the skill in {n} of {len(rows)} replies ({n / len(rows):.0%}).", ""])

    costs = [r.get("cost_usd") for r in read_jsonl(run_dir / "responses.jsonl") if r.get("cost_usd")]
    if costs:
        out.extend([f"Generation cost reported by Claude Code (API-equivalent): ${sum(costs):.2f}", ""])
    tokens = [r.get("tokens") for r in read_jsonl(run_dir / "responses.jsonl") if r.get("tokens")]
    if tokens:
        out.extend([f"Generation tokens reported by Codex (input + output): {sum(tokens):,}", ""])

    (run_dir / "report.md").write_text("\n".join(out))
    print("\n".join(out))

    # Every sample-0 pair, so quoted examples are not cherry-picked.
    by_key = {(r["id"], r["condition"], r["sample"]): r for r in rubric}
    ex = [f"# All sample-0 replies: {run_dir.name}", "",
          "Every case and condition, first sample. Quote from here by a stated rule.", ""]
    for case in load_cases(config.get("cases_file")):
        rows = [(c, by_key.get((case["id"], c, 0))) for c in conds]
        rows = [(c, r) for c, r in rows if r]
        if not rows:
            continue
        ex.extend([f"## `{case['id']}` ({case['maxim']}, {case['type']})", "",
                   f"**User:** {case['prompt']}", "", f"**Case check:** {case['check']}", ""]
                  + ([f"**Source:** {case['source']}", ""] if case.get("source") else []))
        for cond, r in rows:
            sc = r["scores"]
            meta = (f"Quantity {sc['quantity']} · Quality {sc['quality']} · Relation {sc['relation']} · "
                    f"Manner {sc['manner']} · check {'pass' if sc['case_check'] else 'fail'} · "
                    f"{len(r['reply'].split())} words")
            if cond in ("plugin", "pointer"):
                meta += f" · skill {'loaded' if r.get('skill_invoked') else 'not loaded'}"
            ex.extend([f"**{cond}** ({meta})", "", "````markdown", r["reply"].strip(), "````", ""])
            if r.get("fixture"):
                ex.extend(["<details><summary>Tool calls and check output</summary>", "", "```",
                           *(r.get("trace") or ["(no tool calls)"]), "", r.get("verify") or "", "```",
                           "", "</details>", ""])
    (run_dir / "examples.md").write_text("\n".join(ex))
    log(f"\nreport: wrote {run_dir / 'report.md'} and {run_dir / 'examples.md'}")


# ------------------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["generate", "judge", "report", "all"])
    p.add_argument("--run", help="run directory; pass an existing one to resume")
    p.add_argument("--backend", choices=["api", "claude-code", "codex"], default="api")
    p.add_argument("--model", default=None,
                   help="model under test (default: claude-opus-5-5; gpt-6-luna for codex)")
    p.add_argument("--judge-model", default=None,
                   help="judge model (default: same as --model); prefer a different model to limit self-preference")
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--samples", type=int, default=None,
                   help="replies per case and condition (default 3); when resuming, a higher value adds samples")
    p.add_argument("--conditions", default=None,
                   help="comma-separated: baseline,concise,skill,plugin,pointer "
                        "(default: baseline,concise,skill; plugin and pointer need claude-code or codex)")
    p.add_argument("--cases-file", default=None, help="JSONL test cases (default: evals/cases.jsonl)")
    p.add_argument("--cases", help="comma-separated case ids or maxims to run (default: all)")
    p.add_argument("--workers", type=int, default=None,
                   help="parallel calls (default: 4 for api, 2 for claude-code and codex)")
    p.add_argument("--usage-gate", type=float, default=0.20,
                   help="claude-code: stop starting new calls when the usage window reaches this fraction")
    p.add_argument("--timeout", type=int, default=300, help="claude-code and codex: seconds per call")
    p.add_argument("--usage-window", choices=["five_hour", "seven_day"], default="five_hour")
    args = p.parse_args()

    run_dir = Path(args.run) if args.run else RESULTS_DIR / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "config.json"
    if config_path.exists():  # resuming: keep the run's original settings
        saved = json.loads(config_path.read_text())
        extra_samples = args.samples if args.samples and args.samples > saved["samples"] else None
        for k in ("backend", "model", "judge_model", "effort", "samples", "conditions", "cases", "cases_file"):
            setattr(args, k, saved.get(k))
        if extra_samples:  # existing samples are kept; only the new ones are generated and judged
            args.samples = saved["samples"] = extra_samples
            config_path.write_text(json.dumps(saved, indent=2))
            log(f"resume: raised samples to {extra_samples}")
    else:
        args.samples = args.samples or 3
        args.model = args.model or ("gpt-6-luna" if args.backend == "codex" else "claude-opus-5-5")
        args.judge_model = args.judge_model or args.model
        args.conditions = (args.conditions or "baseline,concise,skill").split(",")
        config_path.write_text(json.dumps(
            {k: getattr(args, k) for k in ("backend", "model", "judge_model", "effort", "samples", "conditions", "cases", "cases_file")},
            indent=2))
    args.workers = args.workers or (4 if args.backend == "api" else 2)
    log(f"run: {run_dir} · backend {args.backend} · conditions {','.join(args.conditions)}")

    gate = UsageGate(args.usage_gate, args.usage_window)
    if args.stage != "report":
        backend = (ApiBackend(args.effort) if args.backend == "api" else
                   CodexBackend(args.effort, args.timeout) if args.backend == "codex" else
                   ClaudeCodeBackend(args.effort, gate, args.timeout))
    if args.stage in ("generate", "all"):
        generate(args, backend, gate, run_dir)
    if args.stage in ("judge", "all"):
        judge(args, backend, gate, run_dir)
    if args.stage in ("report", "all"):
        (run_dir / "progress.json").unlink(missing_ok=True)
        report(args, run_dir)


if __name__ == "__main__":
    main()
