<img src="assets/icon.svg" width="64" height="64" alt="">

# Paul Grice Cooperative Principle Skills

An agent skill that makes an agent talk the way Paul Grice described cooperative conversation: say what is needed, say only what is true, stay relevant, and be clear.

## Quick Install

Paste this into your coding agent (Claude Code, Codex, or another agent that supports Agent Skills):

```
Install the cooperative-principle skill from
https://github.com/sennett-lau/paul-grice-cooperative-principle-skills
1. Copy the folder skills/cooperative-principle/ from that repository into your personal skills folder
   (Claude Code: ~/.claude/skills/, Codex: ~/.agents/skills/).
2. In this project's agent instruction file (CLAUDE.md for Claude Code, AGENTS.md for Codex),
   append the contents of https://raw.githubusercontent.com/sennett-lau/paul-grice-cooperative-principle-skills/main/CLAUDE.md
   without changing anything else. Create the file if it does not exist.
3. Show me what you changed.
```

Step 2 adds one short instruction that tells the agent to load the skill. Without it, the agent decides on its own whether the skill is relevant, and it often decides not to (see [Install](#install)).

## The Problem

Agents often reply in ways that are hard to follow, even when the content is correct:

- **The answer is buried.** It comes after a preamble, a restated question, and three paragraphs of context. Or it is left out, so the user has to ask again.
- **Unchecked claims sound like facts.** "This fixes the bug" when nothing was run. Invented flags, APIs, and citations. False premises answered as if they were true.
- **The reply drifts.** Tangents, history lessons, and alternatives nobody asked for.
- **The reply is hard to parse.** Undefined jargon, "it" and "this" with no clear referent, steps out of order, bullet lists used as decoration.

## Where the principle comes from

The British philosopher **H. Paul Grice** (1913–1988) presented the Cooperative Principle in his **William James Lectures at Harvard University in 1967**. The second lecture was published as **"Logic and Conversation" in 1975** (Grice, 1975), and the lectures were later reprinted in his collection ***Studies in the Way of Words*** (Grice, 1989).

Grice's claim is that conversation works because participants assume each other to be cooperative. He stated the principle as follows:

> "Make your conversational contribution such as is required, at the stage at which it occurs, by the accepted purpose or direction of the talk exchange in which you are engaged." (Grice, 1975, p. 45; 1989, p. 26)

He then split it into four categories of maxims. In his words, "Echoing Kant, I call these categories Quantity, Quality, Relation, and Manner" (Grice, 1975, p. 45). The names come from the table of categories in Kant's *Critique of Pure Reason* (Quantity, Quality, Relation, Modality), with Manner in place of Modality.

Because listeners assume the speaker follows the maxims, they draw inferences from what the speaker says and does not say. Grice called these inferences **conversational implicatures**. This is why the maxims matter for an agent: if the agent leaves out a failed test, the user infers that every test passed.

## The Solution

Four maxims, written as agent instructions:

| Maxim | Grice's wording (1975, pp. 45–46) | Addresses |
|-------|-----------------------------------|-----------|
| **Quantity** | "Make your contribution as informative as is required … Do not make your contribution more informative than is required." | Buried answers, padding, missing essentials |
| **Quality** | "Try to make your contribution one that is true": "Do not say what you believe to be false. Do not say that for which you lack adequate evidence." | Overconfidence, unchecked claims, hallucinations, false premises |
| **Relation** | "Be relevant." | Tangents, scope drift, unrequested extras |
| **Manner** | "Be perspicuous": "Avoid obscurity of expression. Avoid ambiguity. Be brief (avoid unnecessary prolixity). Be orderly." | Jargon, vague referents, wordiness, disorder |

## The Four Maxims in Detail

### 1. Quantity: Say enough, then stop

**Be as informative as required. Do not be more informative than required.**

- **Answer first:** the answer, decision, or result goes in the first sentence
- **Match length to the question:** a yes/no question gets a yes or no plus the reason that matters
- **Include what the user needs to act:** the decisive caveat, the next step, the one command
- **Cut the rest:** restated questions, preambles, recaps, closing offers, unrequested alternatives
- **Don't under-inform:** a reply that forces a follow-up about something essential also fails

**The test:** Would the user need a follow-up for something essential? Could you delete a sentence without loss?

### 2. Quality: Say only what you believe and can back up

**Do not say what you believe to be false. Do not say that for which you lack adequate evidence.**

- Separate what you checked, what you inferred, and what you don't know
- Don't report unrun or unverified work as done
- Say "I don't know"; never invent APIs, flags, paths, citations, numbers, or quotes
- Correct false premises before answering
- Hedge only where real uncertainty exists, and say what it depends on

**The test:** For each claim, could you say where it came from?

### 3. Relation: Be relevant

**Every part of the reply serves the question asked and the goal behind it.**

- Answer the question that was asked, at the level it was asked
- Read the purpose behind the request ("Is the build passing?" means "Can I merge?")
- No tangents or displays of related knowledge
- Flag an important off-topic risk in one line, after the answer
- Follow the user when they change topic

**The test:** If the user asked "why are you telling me this?", could every paragraph answer?

### 4. Manner: Be clear

**Avoid obscurity. Avoid ambiguity. Be brief. Be orderly.**

- **Obscurity:** use the user's words; define terms they may not know
- **Ambiguity:** name the file, function, or value instead of "it" or "this"; give numbers
- **Brevity:** short words, short sentences, no padding
- **Order:** conclusion first; steps in the order they are done; lists only for list-shaped content

**The test:** Could the user follow it in one pass, without rereading?

### When the maxims can't all be kept

Grice lists ways a speaker can fail to fulfil a maxim: quietly violate it, openly opt out, face a clash, or flout it on purpose (1975, p. 49). The skill turns this into four rules: **never violate quietly** (it misleads), **opt out openly** ("I can't verify this"), **resolve clashes in favour of Quality**, and **read the user's implicatures** ("Can you check the tests?" means run them and report).

## Install

Installation has two parts: the skill itself, and one line in your instruction file that tells the agent to load it.

The full guidelines live only in the skill. Your `CLAUDE.md` or `AGENTS.md` gets just this:

```markdown
## Communication

At the start of each conversation, load the `cooperative-principle` skill (if it is not already loaded) and follow it in every reply to the user.
```

The line matters. An agent loads a skill when it judges the skill relevant to the task, and a question like "What's the default port for PostgreSQL?" doesn't look like a communication task. In our first trial, Claude Code with the skill installed but no pointer line loaded it in only 5 of 26 replies (see [EVALUATION.md](EVALUATION.md)).

### 1. Install the skill

**Claude Code: plugin (recommended)**

From within Claude Code, add the marketplace:
```
/plugin marketplace add sennett-lau/paul-grice-cooperative-principle-skills
```

Then install the plugin:
```
/plugin install paul-grice-cooperative-principle-skills@grice-skills
```

**Claude Code: copy the folder**

Copy [`skills/cooperative-principle/`](skills/cooperative-principle/) into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project).

**Codex**

Copy [`skills/cooperative-principle/`](skills/cooperative-principle/) into `~/.agents/skills/` (all repositories) or `.agents/skills/` (one repository).

**Other agents**

Any agent that supports the Agent Skills format can use [`skills/cooperative-principle/`](skills/cooperative-principle/). Put it wherever that agent looks for skills.

### 2. Add the pointer line

Claude Code (`CLAUDE.md`):
```bash
curl https://raw.githubusercontent.com/sennett-lau/paul-grice-cooperative-principle-skills/main/CLAUDE.md >> CLAUDE.md
```

Codex and other agents that read `AGENTS.md`:
```bash
curl https://raw.githubusercontent.com/sennett-lau/paul-grice-cooperative-principle-skills/main/CLAUDE.md >> AGENTS.md
```

For a personal setup across all projects, add the line to `~/.claude/CLAUDE.md` (Claude Code) or `~/.codex/AGENTS.md` (Codex) instead.

## Using with Cursor

This repository includes a Cursor project rule ([`.cursor/rules/cooperative-principle.mdc`](.cursor/rules/cooperative-principle.mdc)). See **[CURSOR.md](CURSOR.md)** for setup and for using the rule in other projects.

## Examples

**[EXAMPLES.md](EXAMPLES.md)** shows, for each maxim, a typical agent reply next to a cooperative one, with the problems in the first reply named.

## Proving It Works

Hand-picked examples show what the skill is meant to do. They do not prove that it changes anything. **[EVALUATION.md](EVALUATION.md)** describes how to measure the difference, and [`evals/`](evals/) contains a runnable harness:

- **Paired A/B runs:** the same model and prompts with no skill, with only "Be concise.", and with the skill (plus the skill loaded through the one-line pointer)
- **Bait prompts per maxim:** yes/no questions that invite padding, false premises, nonexistent flags, tangent traps, jargon traps
- **Control prompts:** cases where a long, warm, or creative reply is correct, to catch over-correction
- **Blind LLM judging:** per-maxim rubric scores and pairwise preference with order swapping
- **Deterministic metrics:** word count, filler phrases, case-specific pass checks

The harness runs the same cases three ways:

- **Claude API**: needs `ANTHROPIC_API_KEY`, billed per token.
- **Claude Code**: headless `claude -p` with your Claude login. No API key. This is how the runs so far were done.
- **Codex**: headless `codex exec` with your ChatGPT login. No API key. Uses the cheap `gpt-6-luna` model by default.

```bash
python evals/run_eval.py all --backend claude-code --samples 1 --conditions baseline,concise,pointer
python evals/run_eval.py all --backend codex --samples 1 --conditions baseline,concise,pointer
```

See [`evals/README.md`](evals/README.md) for the case sets, including agentic tasks in small fixture repos, and which ones have been run.

## How to Know It's Working

You should see:

- **The answer in the first sentence**, not after a preamble
- **Fewer "what do you mean?" follow-ups**
- **Claims marked as checked, inferred, or unknown**, with no invented details
- **False premises corrected** instead of answered
- **Shorter replies on simple questions, and replies that are still thorough when detail is asked for**

## Customization

The skill holds the general rules. Put project-specific rules in your own instruction file, next to the pointer line, for example:

```markdown
## Project-Specific Guidelines

- The users are non-technical support staff; define every technical term
- Status updates: one line for the result, then a bullet per failed check
```

## Tradeoff Note

The maxims are relative to "the accepted purpose or direction of the talk exchange". These guidelines bias toward **short, direct, checkable replies**. That is right for most technical questions, but not for every conversation. A tutorial, an emotional conversation, or creative writing has a different purpose, and the required amount of information changes with it. Grice also noted that other maxims exist, "aesthetic, social, or moral in character", such as "Be polite" (1975, p. 47). The skill does not ask the agent to be curt.

## References

Primary sources:

- Grice, H. P. (1975). Logic and conversation. In P. Cole & J. L. Morgan (Eds.), *Syntax and Semantics, Vol. 3: Speech Acts* (pp. 41–58). New York: Academic Press.
- Grice, H. P. (1989). *Studies in the Way of Words*. Cambridge, MA: Harvard University Press. ISBN 0-674-85270-2. ("Logic and Conversation" is reprinted on pp. 22–40.)
- Kant, I. (1781/1787). *Critique of Pure Reason*. (Source of the category names Quantity, Quality, Relation.)

Further reading:

- Grandy, R. E., & Warner, R. (2005; rev. 2017). Paul Grice. In *The Stanford Encyclopedia of Philosophy*. https://plato.stanford.edu/entries/grice/
- Davis, W. (2024). Implicature. In *The Stanford Encyclopedia of Philosophy*. https://plato.stanford.edu/entries/implicature/
- Leech, G. N. (1983). *Principles of Pragmatics*. London: Longman. (Adds politeness maxims.)
- Sperber, D., & Wilson, D. (1986/1995). *Relevance: Communication and Cognition*. Oxford: Blackwell. (Reworks the maxims around relevance alone.)

Page numbers for the 1975 chapter refer to the Cole & Morgan edition.

## License

[MIT](LICENSE)
