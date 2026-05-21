# Project Pluto

Frontier benchmarks for terminal agents.

---

## What this is

You write tasks. A terminal agent tries to solve them. If the task is good — realistic, appropriately hard, and properly structured — it gets accepted and you get paid.

Right now: **$50 per accepted task**, plus bonus tiers if you hit volume before the deadline.

**Bonus tiers (ends Fri May 22 · 11:59am PT):**

| Tasks reaching Ready for Review | Bonus  |
| ------------------------------- | ------ |
| 5                               | $100   |
| 10                              | $300   |
| 25                              | $500   |
| 100                             | $1,000 |

There's also a **$50 referral fee** for anyone you bring in who gets accepted.

---

## How the submission loop works

Write the task locally, zip it up, upload it. The pipeline runs a stack of automated checks. Either everything passes and it moves to human review, or something fails and you get told exactly what to fix. Patch it, re-upload, repeat.

**Step by step:**

1. Author your task following the [Harbor framework docs](https://www.harborframework.com/docs/tasks).
2. Zip it up with the exact structure below.
3. Hit **Add submission** on the My Submissions tab and upload your `.zip`.
4. Enter the domain when prompted — a few plain words is fine.
5. The pipeline runs: CI, rubric, quality, GPTZero, oracle/NOP, difficulty probe, agent quality, similarity.
6. If everything passes, your task goes to **Ready for Review** for a human look.
7. If something fails, the failing check tells you what's wrong. Fix it, re-upload.

---

## ZIP structure

One zip, one task, this exact layout. Task names can only use letters, numbers, underscores, hyphens, or dots — no spaces, no special characters.

```
your-task-name/
  instruction.md         # The prompt the agent sees
  task.toml              # Metadata: domain, resources, etc.
  environment/
    Dockerfile           # Builds the task environment
  solution/
    solve.sh             # The oracle — the correct solution
  tests/
    test.sh              # Test runner
    test_*.py            # Pytest files (at least 6 test functions total)
```

---

## What the pipeline checks

### Content & quality

**Tests.** You need at least 6 `def test_*` functions across your test files. Tests must fail before `solve.sh` runs and pass after. If the environment already passes before anything runs, the task is broken — the whole point is that something needs fixing.

**Human-written instructions.** `instruction.md` goes through GPTZero. If it scores above 70% AI-detected, it's automatically rejected. Write it yourself. Write it like you're describing a problem to a coworker, not like you're filling out a form.

**No leakage.** The instruction can't hint at what the tests check, where the solution lives, or what the oracle does. `solve.sh` can't touch `tests/` or fake the reward file at `/logs/verifier/reward.txt`.

**Clean environments.** Pre-apply and post-apply runs need to be independent. Artifacts from the oracle run can't bleed into the NOP run.

**Difficulty band.** Two models run your task:

- Sonnet 4.6 runs it 5 times first. If it solves all 5, the task is rejected as too easy — Opus never even sees it.
- Opus 4.7 runs it 8 times. Between 1 and 6 passing runs puts you in the **GOOD** band. More than 6 is **TOO_EASY**. Fewer than 1 is **TOO_HARD**.

**Similarity check.** Near-duplicates are blocked. If your task is too close to something already in the pool, it won't make it through.

---

### File invariants

Run these locally before uploading. If they fail here, they'll fail in the pipeline.

```bash
bash -n solution/solve.sh
bash -n tests/test.sh
python -m py_compile tests/test_outputs.py
python -c "import tomllib; tomllib.load(open('task.toml','rb'))"
docker build environment/
```

A few things to get right:

- `tests/test.sh` writes `1` or `0` to `/logs/verifier/reward.txt`. Don't hardcode the reward.
- `task.toml` resource fields (timeout, CPU, memory, disk) should reflect what the task actually needs. No hardcoded tokens or API keys.
- The Dockerfile's build context is the `environment/` directory, not the task root. Write `COPY seed_data.py .` not `COPY environment/seed_data.py .`.
- Don't `COPY` anything from `tests/`, `solution/`, or verifier artifacts into the image. Use `.dockerignore` if you're using `COPY . .`.

---

## Domains

TB2.0 covered software engineering, sys-admin, security, and scientific computing. TB3.0 wants to go wider.

The target is any realistic, valuable computer task that runs in a terminal and can be verified programmatically. That's a bigger surface area than it sounds — working with Excel files using existing packages, querying databases, fixing pipelines, setting up services, parsing financial formats — all of it counts.

There are no domain quotas. Lean into what you actually know. Two strong, well-structured tasks from a niche domain is a real contribution. Don't spread yourself thin trying to cover everything.

---

## Keeping tasks diverse

The pool checks for embedding similarity and archetype saturation — too many tasks that look alike and they start getting blocked.

- Don't repeat the same tool + task type combination more than a few times.
- Mix up compilers, build systems, languages, and failure modes.
- Keep instructions realistic and loose. "The service isn't responding" is better than "the nginx config has a typo on line 14."
- The system will warn you if a pattern is getting oversaturated — pay attention to it.

---

## Validate locally before uploading

Run the NOP/oracle loop yourself first. If it passes here, you skip an unnecessary round-trip through the pipeline.

**Using Harbor:**

```bash
harbor run -p <task-dir> -a oracle    # Full verification after apply
harbor view jobs                       # Check logs, test output, and reward
```

**Using plain bash:**

```bash
cd <task-dir>

# NOP run — tests must FAIL here
rm -f /logs/verifier/reward.txt
bash tests/test.sh
cat /logs/verifier/reward.txt   # expect: 0

# Oracle run — tests must PASS here
rm -f /logs/verifier/reward.txt
bash solution/solve.sh
bash tests/test.sh
cat /logs/verifier/reward.txt   # expect: 1
```

Clear the reward file between runs. If you don't, the second run inherits state from the first and the results are meaningless.

---

## When something looks off

If the difficulty probe gives weird results, don't immediately assume the task is the wrong difficulty. Sample a few cases first.

- **Unexpected failures** — check for environment startup errors, missing dependencies, bad paths, or timeouts that are too tight. The agent should be making real attempts, not failing before it gets started.
- **Unexpected passes** — check for weak tests, hardcoded rewards, answer leakage in the instructions, or oracle artifacts that carried over.
- **High variance across runs** — if results are all over the place, something non-deterministic is in the environment. Fix the seed or explain why the variance is unavoidable.
- **Edge cases** (too easy, too hard, weirdly passing, weirdly failing) — make a call. Fix it, or cut it.
