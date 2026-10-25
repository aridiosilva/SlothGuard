# SlothGuard

[Leia em português](README_PT.md)

A lazy access reviewer. Plain rules find segregation-of-duties (SoD) conflicts, a small open-weight model running on your own computer explains each one, and nothing is revoked unless a human approves it on their phone through Auth0.

**Rules detect, the model explains, a human approves.** The model never decides what is a finding or how severe it is, and it never touches a permission.

Built for the DEV Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady. Project started on 2026-10-22 (challenge window: 2026-10-19 to 2026-10-25).

All data is synthetic. A "revocation" only changes an in-memory copy of that data.

## What it does

- Loads users and roles (`data/synthetic/users.json`) and SoD rules (`data/synthetic/sod_rules.json`).
- Finds every user who holds both roles of a rule (deterministic code, severity comes from the rule).
- Asks a local model (Gemma 4 E2B through Ollama) for a short explanation of each finding. The answer is limited to four sentences by the code; if the model fails, answers nothing or breaks the limit, a fixed template is used and the reason is recorded.
- Builds a Markdown report.
- In a small web interface (sign-in with Auth0), a person can propose revoking one role. Auth0 sends a push to the approver's phone (Auth0 Guardian, CIBA). The role is revoked only after "approve". Denied, unanswered (120 s) or failed means nothing is revoked, and every step is written to an audit trail.

### Sequence of operation

**Phase 1: detect and explain** (terminal run of `run_review.py`).

![Phase 1: rules detect findings and a local model explains them](docs/images/slothguard_fig1_detect_explain.png)

**Phase 2: human approval** (web interface on `localhost:8000`).

![Phase 2: nothing is revoked without human approval on the phone through Auth0](docs/images/slothguard_fig2_human_approval.png)

*Rules detect, the model explains, a human approves.*

## Run it (Windows PowerShell)

Requirements: Python 3.10 or newer, Ollama with the model pulled (`ollama pull gemma4:e2b`), and an Auth0 tenant (see below).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt -r requirements.txt
Copy-Item .env.example .env        # then fill in the Auth0 values; never commit .env
.\.venv\Scripts\python -m pytest -q
```

At the time of writing the suite gives 177 passed, 1 skipped (the skipped test needs a running Ollama: set `RUN_OLLAMA_TESTS=1` to run it).

```powershell
.\.venv\Scripts\python scripts\run_review.py     # explain every finding with the local model, save the report and a run log
.\.venv\Scripts\python scripts\run_app.py        # web interface on http://localhost:8000
```

Open exactly `http://localhost:8000` (not `127.0.0.1`): that is the address registered in Auth0. `run_review.py` stops at once if Ollama cannot be reached. The web page reads the explanations saved by `run_review.py` (`data/output/explanations.json`, not committed).

## Auth0 setup (what this project used)

- A Regular Web Application with the callback URL `http://localhost:8000/callback` and the logout URL `http://localhost:8000/`.
- The Client Initiated Backchannel Authentication (CIBA) grant type enabled in the application's advanced settings, with the Guardian Push notification channel.
- The Push Notification (Auth0 Guardian) factor enabled under Security > Multi-factor Auth.
- A test user enrolled in Guardian (the approver). Its Auth0 user id goes in `AUTH0_TEST_USER_ID`.
- `.env` holds `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET` and `AUTH0_TEST_USER_ID` (plus `OLLAMA_HOST` and `OLLAMA_MODEL`). `.env.example` lists the names without values.

Honest note: I checked all of this on an Auth0 tenant during its free trial period. I have not verified whether asynchronous approval is available after the trial.

## How it is built

```
src/slothguard/
  models.py         immutable users, rules and findings
  rules/            the deterministic SoD engine and the JSON loaders
  llm/              explanations (cache, fallback, sentence limit) and the Ollama client
  report.py + review.py   report builder and the full review flow
  auth/             the human-approval gate (approvals.py) and the Auth0 CIBA gateway (ciba.py)
  web/              Flask app, templates and the Auth0 login (Authlib)
  revoker.py        the in-memory "revocation"
tests/              177+ tests, written before the code they cover
scripts/            run_review.py, run_app.py, review_quality.py and two manual Auth0 checks
docs/               constitution, spec, tasks, and docs/evidence with real measurements
```

Tests came first for each piece: the history shows `test:` commits before the matching `feat:` ones. The spec and rules of the project are in `docs/constitution.md` and `docs/spec.md`.

## Measurements (real runs, with their conditions)

See `docs/evidence/`. On a Dell all-in-one with an Intel Core i5-1334U, 16 GB of RAM in a single memory channel and no dedicated GPU, Gemma 4 E2B through Ollama generated 13 to 22 tokens per second. Turning the model's thinking trace off cut the generated tokens by about 81%. Explaining the 8 findings took between 63.5 and 157.4 seconds across the runs recorded in `docs/evidence/` (table below). The spread was not diagnosed, and free memory alone does not explain it: the fastest run had only 2.1 GB free, although the model was probably still loaded from the previous run. The Ollama version was 0.40.8 for the terminal measurements and 0.40.10 later.

| Date | Total | Conditions | Evidence |
|---|---|---|---|
| 23 Oct | 97.1 s | Free RAM 6.1 GB; Ollama started by hand; ChatGPT closed | `review-run.md` |
| 23 Oct | 139.0 s | Free RAM 4.3 GB; Claude and a browser still open; model unloaded before the run | `review-run-4.3gb-2026-10-23.md` |
| 23 Oct | 157.4 s | Free RAM 1.1 GB; not a clean run | `review-run-low-ram.md` |
| 24 Oct | 98.9 s | Not recorded; the run shown in the demo video | (video) |
| 25 Oct | 104.1 s | Airplane mode, two browsers open; RAM and connectivity not measured | `review-run-airplane-two-browsers-2026-10-25.md` |
| 25 Oct | 63.5 s | Offline (connectivity check returned False); free RAM 2.1 GB | `review-run-offline-2026-10-25.md` |

Conditions of the two runs of 25 Oct: `docs/evidence/offline-test-2026-10-25.md`.

## Limits

- Synthetic data only; no real directory is connected.
- The proposer and the approver can be the same Auth0 user in the demo. A real deployment needs two people.
- The approval message contains the user id and the role name, and that text goes to Auth0.
- The web server is Flask's development server, meant for local use.

## Credits

Built with AI help (pair-programmed with Claude). Libraries: Flask, Authlib, Requests, pytest. Model: Gemma 4 E2B, run through Ollama. Identity and approval: Auth0 (Universal Login, CIBA, Guardian). The Auth0 and Ollama documentation were used for the request formats.

### Pair programming with AI: roles and responsibilities

I built SlothGuard as a human developer working in pair-programming with an AI coding assistant, Claude.

**Human developer.** I contributed the ideas, proposals, guidance and project decisions. I also defined the requirements and the architecture, carried out the review and verification of the code, raised change requests, and I am accountable for the final product. The developer owns the implementation and the final decisions.

**Direction.** The project was conceived, directed and carried through to completion by me. I set the goal, made the project decisions, steered each iteration, and tested and accepted the result. The AI assisted; it did not set the direction.

**AI coding assistant.** Claude assisted me during development through pair programming, code suggestions, debugging, testing and documentation. Its contribution was supportive: it provided suggestions and assistance, and it did not hold ownership of the result.

**My own contributions to the documentation.** The ideas of illustrating the system with real screenshots (the Auth0 Guardian push on the phone, the web page asking to approve or deny the revocation, the Auth0 tenant logs), of capturing the browser Network tab and the Flask server console, and of adding tables with measured processing data were mine. So were the requests to split the sequence diagram into one image per phase, to enlarge the text, to shorten the actor names to keep the width down, and to extend the human role in the pair-programming diagram with ideas, proposals, guidance, project decisions and change requests. The assistant produced the drafts and renderings; I reviewed each one and asked for changes.

**Manual work.** I carried out every manual step myself. I installed the Auth0 Guardian app on the phone and the Ollama app on my computer, and I did all the Auth0 account configuration on the web (the application, the callback and logout URLs, the CIBA and Guardian settings, and the enrolled test user). I also downloaded the generated files, copied the texts into the README files, ran the commands in PowerShell, and checked each result before moving on.

**The AI in the product is a different thing.** The AI coding assistant is not part of the submitted product. The open-source AI that runs inside the application is Gemma 4 E2B, an open-weight model that runs locally through Ollama and writes the short explanation of each finding. Detection and severity are plain code, and no permission is changed without a human approving it.

For verification, the tests were written before the code they cover, and the suite gives 177 passed and 1 skipped at the time of writing.

![Human-AI pair-programming context and the open-source AI runtime](docs/images/slothguard_pair_programming_context.png)

*Roles in the development process and the open-source AI runtime inside the product. Diagram redrawn and extended with Claude at the author's direction.*

© Aridio Silva @aridiosilva

## License

- Code: MIT License, see `LICENSE`.
- Documentation, figures, diagrams, videos and post text: CC BY 4.0, see `LICENSE-DOCS.txt`. (c) 2026 Aridio Silva @aridiosilva.
- The Gemma model is not part of this repository. It is distributed by Google, and its own license applies.

## Submission post

Post: `docs/post/` ([post_en.md](docs/post/post_en.md), [post_pt.md](docs/post/post_pt.md)). Demo video: https://youtu.be/9JlqE3jBITk

## Commits after the submission deadline

None so far.

## Primary sources

1. DEV Community. *Hacktoberfest Open-Source AI Challenge: Week 3* (2026): https://dev.to/challenges/hacktoberfest-week3-2026-10-19
2. Major League Hacking PBC Inc. *Official Challenges and Hackathon Rules* (updated February 25, 2026): https://dev.to/page/official-hackathon-rules
