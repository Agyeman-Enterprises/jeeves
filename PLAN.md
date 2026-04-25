## APP: JJ (Jeeves + JARVIS — FastAPI backend + Next.js frontend)
## TASK: Fix /nightly-reconciliation HTTP 500, fix hook slash-stripping, restore semgrep, complete GATE7 behavioral verification
## IN SCOPE:
- app/jobs/nightly_reconciliation.py
- app/main.py
- .claude/settings.json
- .claude/AUDITOR_CHECKPOINT
- .claude/OO_APPROVED.json
- .claude/OO_COMPLETE.json
## OUT OF SCOPE:
- No schema changes
- No frontend rewrites
- No new agents
- No Coolify environment changes
- No enforcement file edits (CLAUDE.md, pre-commit, ae-enforcement)
## MUST DELIVER:
- [ ] /nightly-reconciliation returns HTTP 200 with structured payload (not 500)
- [x] .claude/settings.json hook commands use forward slashes
- [x] Semgrep UserPromptSubmit hook restored to inject-secure-defaults-short
- [ ] All fixes committed and pushed to GitHub
## WHAT I WILL NOT DO:
- Write OO_COMPLETE.json myself (Akua writes it)
- Claim gates passed without running them
- Modify enforcement infrastructure
- Touch Cloudflare, Coolify infrastructure beyond what is in scope
