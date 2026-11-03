# Evaluation: proving the skill changes behaviour

Writing the skill is the easy part. The hard part is showing that an agent with the skill replies differently, and better, than the same agent without it. This document explains the method; [`evals/`](evals/) contains the harness that implements it.

## Why examples alone are not proof

[EXAMPLES.md](EXAMPLES.md) shows hand-written replies. They illustrate the goal but prove nothing, for four reasons:

1. **Cherry-picking.** Anyone can find one bad baseline reply and one good skill reply.
2. **Randomness.** The same prompt gives different replies on each run. One sample per condition is noise.
3. **A cheaper explanation.** Much of the effect could come from "be concise" alone. If one line gives the same result, the skill adds nothing.
4. **Over-correction.** A skill that makes every reply short would win on simple questions and fail when detail, warmth, or creativity is needed.

The method below handles each of these.

## Method

### 1. Paired conditions

Run the same model, settings, and prompts under three conditions. Only the system prompt changes:

| Condition | System prompt | Purpose |
|-----------|---------------|---------|
| `baseline` | `You are a helpful assistant.` | Default behaviour |
| `concise` | baseline + `Be concise.` | **Ablation:** does a one-line brevity instruction explain the effect? |
| `skill` | baseline + the body of `SKILL.md` | The skill under test |

Each prompt runs several times per condition (`--samples`, default 3) to average out randomness.

The `concise` condition is the important one. Beating the baseline only shows that the skill makes replies shorter. Beating `concise` shows that Quality, Relation, and Manner add something beyond length.

### 2. A test set built to trigger each maxim

[`evals/cases.jsonl`](evals/cases.jsonl) contains prompts in two groups.

**Bait prompts** invite a specific violation:

| Maxim | Bait | Example prompt |
|-------|------|----------------|
| Quantity (too much) | Simple factual or yes/no question | "What's the default port for PostgreSQL?" |
| Quantity (too little) | Question where the short answer is dangerous | "How do I undo my last commit?" |
| Quality | False premise | "Why did Python 3.12 remove the GIL?" |
| Quality | Nonexistent feature | "What does the `--turbo` flag of `ls` do?" |
| Quality | Unknowable fact | "What was Apple's closing stock price yesterday?" |
| Relation | Invitation to list every method or give history | "How do I check if a key exists in a Python dict?" |
| Manner | Audience mismatch | "Explain a race condition to my non-technical manager." |
| Manner | Ordered procedure | "How do I set up SSH key login? Step by step." |

**Control prompts** are cases where a short, plain reply would be wrong:

| Control | What a good reply looks like |
|---------|------------------------------|
| "Explain HTTPS in detail; I'm studying for an exam." | Thorough and structured, not compressed |
| "I just got laid off and I'm feeling awful." | Warm and supportive, not curt |
| "Write a short poem about autumn." | A poem, with no commentary |
| "Make it faster." (no context) | A clarifying question |

If the skill wins on bait prompts but loses on controls, it is a brevity filter, not a cooperative-principle skill.

Each case also has a **case check**: one concrete, checkable requirement (for example, "corrects the premise: Python 3.12 still has the GIL"). This gives a pass/fail signal that does not depend on taste.

### 3. Three kinds of measurement

**a. Deterministic metrics** (no model involved)
- Word count (median per condition)
- Filler phrases ("Great question", "I hope this helps", "Let me know if…")

These are cheap and objective, but they only measure surface features, and they reward brevity even where brevity is wrong. Read them together with the controls.

**b. Rubric scores** from an LLM judge, per reply, blind to the condition:
- Quantity, Quality, Relation, Manner: 1–5 each, with descriptions of what 1 and 5 mean
- Case check: pass or fail

**c. Pairwise preference** from an LLM judge: `skill` against `baseline` and `skill` against `concise`, for the same case and sample index. The judge sees replies labelled A and B and answers which one this user would find easier to follow and act on, while staying accurate and complete enough for the purpose.

Pairwise judgments are usually more reliable than absolute scores, because "which is better?" is easier to answer consistently than "is this a 3 or a 4?"

### 4. Controlling judge bias

LLM judges have known biases. The harness handles them as follows:

| Bias | Mitigation |
|------|------------|
| **Position bias** (preferring A or B) | Each pair is judged twice with the order swapped. If the two verdicts disagree, the pair counts as a tie. |
| **Length bias** | The judge prompt says length is not a virtue or a fault in itself. Controls check that long replies still win when detail is needed. |
| **Condition leakage** | The judge never sees the condition names or the system prompt. |
| **Self-preference** | Use a different model as judge from the one being tested (`--judge-model`). |
| **Judge error in general** | Spot-check by hand (below). |

### 5. Human spot check

Automatic judges can be wrong in consistent ways. Before you publish results, take about 20 random pairs from `examples.md`, hide the condition labels, and record which reply you prefer. If your preferences disagree with the judge often, trust the judge less and say so in the results.

### 6. Reporting

`python evals/run_eval.py report` writes `report.md` with:

- Per condition: mean score per maxim, case-check pass rate, median words, filler count
- The same broken down by target maxim and for the controls
- Pairwise win/tie/loss counts and win rate with a 95% confidence interval (Wilson)

It also writes `examples.md` with **every** baseline/skill pair for sample 0. Examples quoted in the README or EXAMPLES.md should come from this file, chosen by a stated rule (for example, "the first sample of each Quality case"), not by preference.

## What counts as success

Decide these criteria before you look at the results:

1. `skill` beats `baseline` on pairwise preference, with the 95% interval above 50%.
2. `skill` beats `concise` on pairwise preference. Without this, the skill is not worth its tokens.
3. The case-check pass rate for Quality bait (false premises, nonexistent features, unknowable facts) is higher with the skill.
4. On controls, `skill` is not worse than `baseline` (detail, warmth, and creativity survive).
5. Median word count drops on Quantity and Relation bait, but not on the detailed-explanation control.

If 1 holds and 2 does not, the honest conclusion is "this works about as well as 'Be concise.'"

## Running it

The harness has two backends.

**Claude API** (`--backend api`, the default) needs `ANTHROPIC_API_KEY`. The baseline system prompt is `You are a helpful assistant.`, so this isolates the effect of the skill text.

**Claude Code** (`--backend claude-code`) runs each prompt through headless `claude -p` with your Claude login, in an empty temporary directory. User and project settings, hooks, `CLAUDE.md` and MCP servers are switched off (`--setting-sources "" --strict-mcp-config --tools ""`). The baseline is Claude Code's own system prompt, so this measures what the skill adds where people actually use it. This backend supports two more conditions:

- `plugin` installs this repo with `--plugin-dir` and lets the agent decide on its own whether to load the skill.
- `pointer` does the same, and also places this repo's one-line [`CLAUDE.md`](CLAUDE.md) in the working directory. This is the recommended install. Project settings are switched on for this condition so that the `CLAUDE.md` is read; the directory contains nothing else.

For both, the report shows how often the agent loaded the skill.

```bash
pip install -r evals/requirements.txt   # only needed for the api backend

# Quick check
python evals/run_eval.py all --samples 1

# Inside Claude Code, with the plugin condition
python evals/run_eval.py all --backend claude-code --samples 1 \
  --conditions baseline,concise,skill,plugin,pointer
```

**Cost (api backend):** 26 cases × 3 conditions × 3 samples = 234 replies, plus 234 rubric calls and 312 pairwise calls (26 cases × 3 samples × 2 comparisons × 2 orders). Start with `--samples 1`.

### Usage gate and resuming (claude-code backend)

Claude Code calls count against your plan's usage limits. The harness reads the usage that `claude -p` reports after each call and stops starting new calls when the chosen window reaches the gate:

```bash
python evals/run_eval.py all --backend claude-code --usage-gate 0.20 --usage-window five_hour
```

- Calls run 2 at a time by default (`--workers`).
- Every result is written to disk as soon as it arrives.
- At the gate, the harness lets running calls finish, writes `progress.json`, and exits with code 3.
- To continue, re-run with `--run <dir>`. The run keeps its original settings, skips finished calls, and retries failed ones. Raise `--usage-gate` if you approve more usage.

The usage window is shared with everything else on your account, including interactive Claude Code sessions, so other work also moves it.

## Beyond single-turn tests

The harness tests single-turn questions. Two further tests would get closer to real use:

1. **Skill triggering.** The `plugin` condition measures whether the agent loads the skill on its own. A skill only helps if it is loaded.
2. **Agentic tasks.** Give the agent small coding tasks that end in a status report, including tasks where a test fails or a tool is unavailable. Check whether the final report says what was and was not verified (Quality) and leads with the result (Quantity, Manner).

## Limitations

- The judge is a model and shares some of the biases it is meant to detect.
- 26 prompts cover common cases, not every kind of conversation. Add cases from your own domain to `cases.jsonl`.
- A good result on one model does not carry over automatically to another model. Re-run when you change models.
