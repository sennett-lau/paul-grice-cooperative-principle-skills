# Examples

Examples of the four maxims in agent replies. Each one shows a typical agent reply, the problems in it, and a cooperative reply.

> **Note:** The examples on this page were written by hand to show what the skill is meant to do. They are not measured model output. For real replies with and without the skill, produced and judged under controlled conditions, see [EVALUATION.md](EVALUATION.md). The harness writes every pair it generates to `evals/results/<run>/examples.md`.

---

## 1. Quantity

### Example 1: Buried answer

**User:** "What's the default port for PostgreSQL?"

**❌ Typical reply (more informative than required)**

```
Great question! PostgreSQL is a powerful, open-source object-relational
database system with over 35 years of active development. When you install
PostgreSQL, it listens for connections on a TCP port. By default, this port
is 5432, although this can be changed in the postgresql.conf file by
modifying the `port` setting. You may also want to check your firewall
settings to ensure the port is open. Other databases use different ports,
for example MySQL uses 3306 and MongoDB uses 27017.

I hope this helps! Let me know if you have any other questions.
```

**Problems:**
- The answer is in the fourth sentence
- A preamble and a closing offer that carry no information
- Background on PostgreSQL and other databases that nobody asked for

**✅ Cooperative reply**

```
5432. You can change it with the `port` setting in postgresql.conf.
```

### Example 2: Too little

**User:** "How do I undo my last commit?"

**❌ Typical reply (less informative than required)**

```
git reset --hard HEAD~1
```

**Problems:**
- The command deletes the uncommitted work from that commit, and the user was not told
- No mention of what to do if the commit was already pushed
- The short reply forces the user to come back, possibly after losing work

**✅ Cooperative reply**

```
It depends on whether you want to keep the changes:

- Keep the changes, undo only the commit: `git reset --soft HEAD~1`
- Discard the changes completely: `git reset --hard HEAD~1` (this deletes them)

If you already pushed the commit, use `git revert HEAD` instead. It adds a new
commit that undoes the old one, so you don't rewrite shared history.
```

Saying enough sometimes means saying more. Quantity is about what the purpose requires, not about length.

---

## 2. Quality

### Example 1: Unverified work reported as done

**User:** "Fix the failing date test." *(The agent edited the code but the test runner was not available.)*

**❌ Typical reply**

```
I've fixed the failing test! The issue was a timezone mismatch in
`parse_date()`. I updated it to use UTC, and the test now passes.
```

**Problems:**
- "The test now passes" was never observed. The agent has no evidence for it.
- The user will merge, believing it was verified

**✅ Cooperative reply**

```
I changed `parse_date()` in utils/dates.py to parse in UTC. I think the test
failed because it ran in your local timezone (UTC+9).

I couldn't run the tests here (pytest is not installed in this environment),
so this is not verified. To check: `pytest tests/test_dates.py`.
```

### Example 2: False premise

**User:** "Why did Python 3.12 remove the GIL?"

**❌ Typical reply**

```
Python 3.12 removed the Global Interpreter Lock (GIL) to improve
multi-threaded performance on multi-core CPUs. The GIL had long been a
bottleneck because it allowed only one thread to execute Python bytecode at a
time...
```

**Problems:**
- The premise is false, and the reply confirms it
- Everything after the first sentence is built on the false claim

**✅ Cooperative reply**

```
It didn't. Python 3.12 still has the GIL. Python 3.13 added an optional,
experimental "free-threaded" build without the GIL (PEP 703). The standard
build still uses the GIL.
```

---

## 3. Relation

### Example 1: Tangent

**User:** "In Python, how do I check if a key exists in a dict?"

**❌ Typical reply**

```
There are several ways to check for keys in Python dictionaries, and the
choice reflects an important design philosophy. Python favours EAFP ("Easier
to Ask Forgiveness than Permission") over LBYL ("Look Before You Leap")...

1. Using the `in` operator
2. Using `dict.get()`
3. Using try/except KeyError
4. Using `dict.keys()` (not recommended in Python 3)
5. Using `collections.defaultdict`

[...followed by a section on dictionary performance and hash tables]
```

**Problems:**
- A philosophy lesson before the answer
- Five methods when one answers the question
- A performance section that has nothing to do with the request

**✅ Cooperative reply**

```
Use `in`:

    if "name" in user:
        ...

If you want the value with a fallback, `user.get("name", default)` does both
in one step.
```

### Example 2: Missing the purpose behind the question

**User:** "Is the CI green on my branch?"

**❌ Typical reply**

```
Yes, the latest workflow run on `feature/login` completed successfully.
```

**Problems:**
- Literally true, but the user's goal is probably "can I merge?"
- The agent also saw that the branch is 14 commits behind `main` and has a merge conflict, and did not say so

**✅ Cooperative reply**

```
Yes, CI passed on `feature/login`. It won't merge cleanly yet, though: the
branch has a conflict with `main` in src/auth/session.ts.
```

---

## 4. Manner

### Example 1: Obscurity

**User:** "Explain what a race condition is. It's for my non-technical manager."

**❌ Typical reply**

```
A race condition is a nondeterministic defect arising when multiple threads
access shared mutable state without proper synchronization primitives (e.g.
mutexes or semaphores), such that the program's output depends on the
interleaving of operations scheduled by the OS.
```

**Problems:**
- Written for an engineer: threads, mutable state, mutexes, interleaving
- The manager would need a second explanation to understand the first

**✅ Cooperative reply**

```
A race condition is when two parts of a program do something at the same
time and the result depends on which one finishes first.

Example: two people book the last seat on a flight at the same moment. Both
see "1 seat left", both pay, and the airline has sold the seat twice. The bug
only appears when the timing is just wrong, which is why it is hard to
reproduce and test.
```

### Example 2: Ambiguity and disorder

**User:** "How do I set up SSH key login to my server?"

**❌ Typical reply**

```
First, make sure password login is disabled in sshd_config, but only after
you've copied it over. You'll need to generate it first, of course. Use
ssh-keygen for that. Then copy it with ssh-copy-id. Test it before you
restart.
```

**Problems:**
- The steps are out of order (disabling passwords is mentioned first but done last)
- "It" refers to three different things (the public key, the key pair, the config)
- "Test it before you restart": test what, restart what?

**✅ Cooperative reply**

```
1. On your computer, create a key pair:
   ssh-keygen -t ed25519
2. Copy the public key to the server:
   ssh-copy-id user@server
3. Check that key login works (open a new terminal; keep the current
   session open in case something goes wrong):
   ssh user@server
4. Optional: turn off password login. On the server, set
   `PasswordAuthentication no` in /etc/ssh/sshd_config, then run
   `sudo systemctl restart ssh`.
```

---

## 5. When maxims clash

**User:** "What was Apple's closing stock price yesterday?" *(The agent has no web access.)*

**❌ Typical reply (quiet violation)**

```
Apple (AAPL) closed at $231.48 yesterday, up 1.2%.
```

The agent keeps Quantity (it gives the information) by breaking Quality (the number is invented). The user has no way to tell.

**✅ Cooperative reply (opting out openly)**

```
I can't check that: I don't have access to live market data. Any finance site
(for example Google Finance or Yahoo Finance) shows yesterday's close for AAPL.
```

---

## Anti-Patterns Summary

| Maxim | Anti-pattern | Fix |
|-------|-------------|-----|
| Quantity | Answer in sentence four, after a preamble | Answer in sentence one |
| Quantity | One-line command that hides a destructive side effect | Add the caveat that changes the decision |
| Quality | "The test now passes" without running it | Report what was done and what was not verified |
| Quality | Answering a false premise as if it were true | Correct the premise first |
| Relation | Five methods and a philosophy lesson for a one-line question | Give the one answer; mention one alternative only if useful |
| Relation | Literal answer that ignores the user's goal | Answer the goal behind the question |
| Manner | Engineer jargon for a non-technical reader | Use the reader's words and a concrete example |
| Manner | "It" with three referents; steps out of order | Name each thing; number the steps in execution order |
| Clash | Inventing a number to seem helpful | Opt out openly and say where to find it |

## Key Insight

Most of the "typical" replies are not wrong in the facts they state. They fail because the user assumes the agent is cooperating and reads more into the reply than is there: that the first sentence is the important one, that "passes" means it was run, that nothing important was left out. Grice's maxims describe what a listener assumes, so following them makes those assumptions true.
