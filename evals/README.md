# evals

Harness for the method in [../EVALUATION.md](../EVALUATION.md).

| File | Contents |
|------|----------|
| `cases.jsonl` | 26 test prompts: bait prompts per maxim and control prompts. Each has a `check`, one concrete pass/fail requirement. |
| `run_eval.py` | Generates replies under `baseline`, `concise`, and `skill`, judges them blind, and writes the report. |
| `results/<run-id>/` | Output of a run: `responses.jsonl`, `rubric.jsonl`, `pairwise.jsonl`, `report.md`, `examples.md`, `config.json`, and `progress.json` if the usage gate stopped it. |

## Run

```bash
pip install -r evals/requirements.txt
export ANTHROPIC_API_KEY=...

python evals/run_eval.py all --samples 1                                # quick check
python evals/run_eval.py all --samples 3 --judge-model claude-sonnet-5-5  # full run
python evals/run_eval.py all --cases quality,control                    # a subset

# Through headless Claude Code with your Claude login, stopping at 20% of the 5-hour usage window
python evals/run_eval.py all --backend claude-code --samples 1 \
  --conditions baseline,concise,skill,plugin,pointer --usage-gate 0.20

# Resume a stopped run (keeps its settings; raise the gate to approve more usage)
python evals/run_eval.py all --run evals/results/<run-id> --usage-gate 0.40
```

Options: `--backend` (`api` or `claude-code`), `--model` (model under test, default `claude-opus-5-5`), `--judge-model`, `--effort` (default `medium`), `--samples`, `--conditions`, `--cases`, `--workers`, `--usage-gate`, `--usage-window`, `--timeout`.

See [../EVALUATION.md](../EVALUATION.md) for what the conditions and the usage gate do.

## Adding cases

Add a line to `cases.jsonl`:

```json
{"id": "qlt-my-case", "maxim": "quality", "type": "bait", "prompt": "...", "check": "One concrete thing a good reply must do."}
```

`maxim` is one of `quantity`, `quality`, `relation`, `manner`, `control`. `type` is `bait` or `control`. Write the `check` so that a reader could decide pass or fail without judgement calls.
