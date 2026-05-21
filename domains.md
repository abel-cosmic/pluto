# Domain Guide — Terminal-Bench 3.0

This is a practical guide for picking a domain and building tasks that actually get accepted. Read it before you start writing — most rejections come from tasks that are either too obvious, too abstract, or don't reflect real work anyone does.

The short version: pick something you actually know, make it feel like a real job, and make sure the agent has to actually do something to pass.

---

## Software Engineering

This is the most saturated domain in the pool, so the bar is higher. Don't submit "fix the bug in this Python script" — that's been done. Go deeper.

**What works here:**
- Refactoring tasks with measurable outcomes (reduced cyclomatic complexity, passing a specific linter config, hitting a coverage threshold)
- Build system failures — broken CMake configs, missing linker flags, Makefile dependency loops
- Debugging across language boundaries (a Python script calling a C extension that segfaults)
- Getting a test suite from failing to green without touching the tests themselves
- Dependency resolution — conflicting package versions, pinned deps that break the build

**What doesn't:**
- "Write a function that does X" — too clean, too easy, no environment state
- Tasks where the agent just needs to google the right flag
- Anything that can be solved by running `--help`

**Tips:**
- Seed a broken repo state in the Dockerfile. The agent should inherit a mess, not a blank slate.
- Keep the instruction vague about the specific error. Say "the build is broken" not "there's a missing `-lm` flag on line 12 of the Makefile."
- Your tests should check the output artifact (binary runs, tests pass, lint score) — not how the agent got there.

---

## System Administration

Strong domain with a lot of room. Real sysadmin work is messy, underdocumented, and involves systems that are halfway broken before you even start.

**What works here:**
- Service configuration that's almost right — nginx rewrites that 404 on one route, cron jobs that don't fire, systemd units that fail silently
- Log parsing and alerting setup — get a monitoring condition working from raw logs
- Permission and ownership problems that cascade across a directory tree
- Networking — setting up routing rules, fixing iptables configs, getting two containers talking
- Certificate and TLS issues — expired certs, wrong SAN entries, chain problems

**What doesn't:**
- Tasks that boil down to "run this one command"
- Anything where the fix is just editing one line in a config file with no ambiguity

**Tips:**
- Broken services make the best seeds. Start with a systemd service that fails to start and give the agent the logs but not the reason.
- Real sysadmin problems have multiple things wrong. A service can be failing because of both a permission error and a misconfigured port — that's a better task than just one.
- Make sure your test checks the actual behavior (service responds on the right port, log output matches expected pattern) rather than just that a file exists.

---

## Security

High-value domain but easy to get wrong. The line between a security task and an exploitation tutorial is real — stay on the defensive and verification side.

**What works here:**
- Static analysis — find the vulnerability class in a codebase (SQL injection, unsafe deserialization, path traversal) and fix it
- Hardening tasks — take a running service and get it to pass a security benchmark (CIS, OWASP checklist)
- Secret scanning and remediation — credentials in code, leaked keys in git history
- Setting up authentication correctly — OAuth flows, JWT validation, session management
- CVE reproduction in a sandboxed environment, then patching it

**What doesn't:**
- Anything that teaches offensive techniques without a clear defensive framing
- Tasks that are just "run this scanner and read the output"
- Open-ended "find all vulnerabilities" prompts — too ambiguous to test deterministically

**Tips:**
- Scope the task tightly. "Fix the SQL injection vulnerability in the user login endpoint" is better than "make this app secure."
- Your tests should check that the fix actually works — send a payload and assert it fails safely, don't just check that a line of code changed.
- Be careful with instructions. Don't leak what the vulnerability is — describe the symptom, not the cause.

---

## Data Engineering & Scientific Computing

Underrepresented in TB2.0, good opportunity. These tasks tend to have clean verification because the output is a number, a file, or a query result.

**What works here:**
- ETL pipelines that are broken or incomplete — transform a dataset, handle malformed rows, get it into a target schema
- Query optimization — a slow SQL query that needs to run under a time threshold on a seeded database
- Numerical correctness — a simulation or computation that's producing wrong results due to a floating point or precision bug
- Data format conversion with constraints — convert formats while preserving specific fields, handle encoding issues
- Scientific workflows — a broken analysis pipeline (missing normalization step, wrong statistical test applied, off-by-one in a sliding window)

**What doesn't:**
- Tasks that are just "run this Jupyter notebook" with no broken state
- Pure data generation with no verification criteria

**Tips:**
- Seed a real dataset in the Dockerfile. Synthetic toy data makes tasks feel fake.
- Numerical tasks need tolerances in your tests — don't assert exact float equality.
- For pipeline tasks, break something in the middle of the pipeline, not at the start. Agents are good at "fix the error on line 1" — they're worse at finding where a silent data corruption crept in.

---

## Finance & Business Tooling

Wider than it sounds. A lot of economically valuable work happens in spreadsheets, accounting systems, and reporting tools — and most of it can be automated from the command line.

**What works here:**
- Excel/CSV manipulation with financial logic — amortization tables, reconciliation, pivot outputs that need to match a spec
- Generating reports from raw transaction data (categorization, aggregation, formatting to a standard)
- Working with financial data formats — OFX, QIF, XBRL — parsing and transforming them
- Building or fixing scripts that interact with financial APIs (rate limiting, pagination, data normalization)
- Accounting rule enforcement — flag transactions that violate constraints, rebalance ledger entries

**What doesn't:**
- Tasks that require live market data or external API calls without a mock
- Anything that depends on today's date in a way that breaks deterministic testing

**Tips:**
- Use `openpyxl`, `pandas`, or similar to work with Excel files from the command line — this is valid and underexplored.
- Seed realistic-looking fake financial data. Real transaction data is great for realism if it's anonymized.
- Your tests should check the output file's actual values, not just that it exists.

---

## DevOps & Infrastructure

Good domain. The tasks have natural broken states (pipelines that fail, containers that won't start, deploys that time out) and clear pass/fail verification.

**What works here:**
- Fixing a broken CI pipeline — a GitHub Actions or Dockerfile config that fails at a specific step
- Container orchestration — getting a multi-container setup to a working state (services can reach each other, health checks pass)
- Infrastructure as code — broken Terraform or Ansible configs that need to apply cleanly
- Observability setup — getting metrics, logs, or traces flowing to a target
- Deployment rollback scenarios — identify why a deploy failed and restore a working state

**What doesn't:**
- Tasks that require real cloud provider credentials
- "Set up monitoring" with no specific success criteria

**Tips:**
- Docker Compose works well for multi-service tasks — seed broken configs and let the agent fix them.
- Timeouts matter here. If a container takes 30 seconds to start, account for it in your `task.toml` resource fields.
- Make your test check the end state, not the process. The agent shouldn't get credit for restarting a service that's still broken.

---

## General Tips Across All Domains

**Broken state first.** The Dockerfile seeds the environment. Start with something that's already halfway wrong — the agent's job is to fix it, not build from scratch.

**Vague instructions, precise tests.** The instruction should describe the problem like a coworker would describe it to you. The tests should check exactly what matters.

**Avoid the obvious fix.** If the solution is the first thing that comes up on Stack Overflow, the task is probably too easy. Add a constraint, a wrinkle, or a second failure mode.

**Test the behavior, not the artifact.** Don't just check that a file exists or a process is running. Check that the service returns the right response, the output matches the expected schema, the test suite passes.

**Run the NOP/oracle loop before uploading.** If it doesn't pass locally, it won't pass in the pipeline. Save yourself the round-trip.