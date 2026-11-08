# evals

Harness for the method in [../EVALUATION.md](../EVALUATION.md).

| File | Contents |
|------|----------|
| `cases.jsonl` | 26 test prompts: bait prompts per maxim and control prompts. Each has a `check`, one concrete pass/fail requirement. |
| `cases-personas.jsonl` | 25 prompts for students, researchers, developers and product managers, adapted from published examples. Each records its `source`. |
| `cases-agentic.jsonl` | 8 tasks the agent carries out in a small repo before it replies (claude-code and codex backends). Each names a `fixture` and lists the `facts` the judge needs. |
| `cases-agentic-hard.jsonl` | 6 harder agentic tasks: the problem is buried in long output, hidden by a re-run, in an untested caller, among minor review findings, in an unstated choice, or in data that needs cleaning. |
| `fixtures/<name>/` | `repo/`, copied into a fresh git repo for every call; optional `setup.sh`, run after the first commit (for example to create a branch); and `verify.sh`, a check the harness runs afterwards. The agent never sees `verify.sh`. |
| `run_eval.py` | Generates replies under `baseline`, `concise`, and `skill`, judges them blind, and writes the report. |
| `results/<run-id>/` | Output of a run: `responses.jsonl`, `rubric.jsonl`, `pairwise.jsonl`, `report.md`, `examples.md`, `config.json`, and `progress.json` if the usage gate stopped it. |

## Status of the case sets

| Case set | Claude Code (`claude-opus-5-5`) | Codex (`gpt-6-luna`) |
|---|---|---|
| `cases.jsonl` | Run 2026-11-04, 1 sample | Pending |
| `cases-personas.jsonl` | Run 2026-11-04, 1 sample; more samples pending | Pending |
| `cases-agentic.jsonl` | Run 2026-11-06, 2 samples | Pending |
| `cases-agentic-hard.jsonl` | Pending | Pending |

Run results are not committed yet.

## Run

There are three backends; [EVALUATION.md](../EVALUATION.md#running-it) compares them.

```bash
# 1. Claude API: needs an API key, billed per token
pip install -r evals/requirements.txt
export ANTHROPIC_API_KEY=...
python evals/run_eval.py all --samples 1                                # quick check
python evals/run_eval.py all --samples 3 --judge-model claude-sonnet-5-5  # full run
python evals/run_eval.py all --cases quality,control                    # a subset

# 2. Claude Code: your Claude login, no API key; stops at 20% of the 5-hour usage window
python evals/run_eval.py all --backend claude-code --samples 1 \
  --conditions baseline,concise,skill,plugin,pointer --usage-gate 0.20

# 3. Codex: your ChatGPT login, no API key; cheap model gpt-6-luna at medium effort by default
python evals/run_eval.py all --backend codex --samples 1 \
  --conditions baseline,concise,pointer

# Resume a stopped run (keeps its settings; raise the gate to approve more usage)
python evals/run_eval.py all --run evals/results/<run-id> --usage-gate 0.40

# Add samples to a finished run (existing samples are kept; only new ones run)
python evals/run_eval.py all --run evals/results/<run-id> --samples 3
```

Options: `--backend` (`api`, `claude-code` or `codex`), `--model` (model under test; default `claude-opus-5-5`, or `gpt-6-luna` for codex), `--judge-model` (default: same as `--model`), `--effort` (default `medium`), `--samples`, `--conditions`, `--cases-file`, `--cases`, `--workers`, `--usage-gate` and `--usage-window` (claude-code only), `--timeout`.

See [../EVALUATION.md](../EVALUATION.md) for what the conditions and the usage gate do.

## Adding cases

Add a line to `cases.jsonl`:

```json
{"id": "qlt-my-case", "maxim": "quality", "type": "bait", "prompt": "...", "check": "One concrete thing a good reply must do."}
```

`maxim` is one of `quantity`, `quality`, `relation`, `manner`, `control`. `type` is `bait` or `control`. Write the `check` so that a reader could decide pass or fail without judgement calls.

## Agentic cases

The persona cases hand the agent its results as text. The agentic cases make it do the work: run the tests, run the release script, read the incident notes. Then it reports, and the report is what gets judged.

Each fixture is set up so that something goes wrong in a way the agent can't fix: a test needs an unreachable service, a private SDK isn't installed, the infra repo isn't there, the publish step can't reach the registry. A cooperative report says so. An uncooperative one leaves it out, and the user concludes that everything worked (Grice 1975, p. 49: a quiet violation is "liable to mislead").

For each call the harness:

1. copies `fixtures/<name>/repo/` into a temporary git repo with one commit (plus the pointer `CLAUDE.md` in the `pointer` condition);
2. runs the agent there. Claude Code gets Bash, Read, Edit, Write, Glob and Grep, with permission checks off and package installs, network commands, `gh` and `git push` denied. Codex runs in its `workspace-write` sandbox, which has no network;
3. runs `verify.sh` in the repo and saves its output with the tool calls;
4. gives the judge the case's `facts` and the `verify.sh` output, so it can tell an accurate report from a confident wrong one.

```bash
python evals/run_eval.py all --backend claude-code --cases-file evals/cases-agentic.jsonl \
  --conditions baseline,concise,pointer --samples 2 --timeout 900 --usage-gate 0.80
```

The agent runs real shell commands on your machine, inside a temporary directory. The fixtures only use the Python standard library.

