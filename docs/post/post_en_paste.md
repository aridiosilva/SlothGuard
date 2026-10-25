*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

**Be lazy when you read. Be careful when you approve.**

Access reviews are the chore everyone postpones. Someone hands you a long list of who can do what, and hidden in it is one question: which pairs of permissions should never belong to the same person? Security people call it segregation of duties (SoD). A user who can both create a vendor and release payments to that vendor is the textbook case.

SlothGuard does the dull part and keeps the human for the one decision that matters.

- **Rules detect.** Deterministic rules check 40 synthetic users against 9 SoD rules and find 8 conflicts (5 high, 2 medium, 1 low).
- **A local model explains.** Gemma 4 E2B, an open-weight model running on my own PC through Ollama, writes a short explanation for each finding. The code caps it at 4 sentences and falls back to a default text if the model fails.
- **A person approves.** To revoke a role, the app asks for approval on a phone through Auth0 (Universal Login, CIBA, Guardian). Approve, deny or ignore it: the three outcomes are in the video.

One rule holds the whole design together: **the model never decides findings or severity, and it never touches a permission.** It only explains. Everything is synthetic data, and a "revocation" changes a copy kept in memory.

![Sequence diagram of Phase 1: rules detect, Gemma explains](UPLOAD_slothguard_fig1_detect_explain.png)
*Figure 1. Phase 1 (detect and explain): the rules engine finds the conflicts and Gemma writes a short explanation for each one. If an answer is missing or breaks the 4-sentence limit, a fixed template is used and the reason is recorded.*

![Sequence diagram of Phase 2: human approval through Auth0](UPLOAD_slothguard_fig2_human_approval.png)
*Figure 2. Phase 2 (human approval): nothing is revoked unless the approver answers Approve on the phone. A denial, no answer in 120 s or a failure all mean nothing is revoked, and every step is logged.*

## Demo

Full demo, with English captions burned in (7 min 55 s): https://youtu.be/9JlqE3jBITk. The approval on the phone starts at [4:14](https://youtu.be/9JlqE3jBITk?t=254). The video is also embedded at the end of this post.

Phase 1 turned 40 synthetic users and 9 rules into 8 findings, each explained by Gemma. Rule, user and roles come from the data, severity comes from the rule, and the last column is how long the model took in the run of 23 Oct (97.1 s in total, `docs/evidence/review-run.md`):

| Rule | User | Conflicting roles | Severity (from the rule) | Explanation time |
|---|---|---|---|---|
| SOD-001 | U001 | Vendor_Master_Maintain + Payment_Release | High | 23.9 s * |
| SOD-002 | U002 | Purchase_Requester + Purchase_Approver | High | 10.6 s |
| SOD-003 | U003 | Journal_Entry_Create + Journal_Entry_Approve | High | 10.4 s |
| SOD-006 | U004 | User_Admin + Audit_Log_Admin | High | 11.5 s |
| SOD-004 | U010 | Payroll_Maintain + Payroll_Approve | High | 10.7 s |
| SOD-005 | U007 | Bank_Reconcile + Payment_Release | Medium | 9.8 s |
| SOD-007 | U008 | Dev_Commit + Prod_Deploy | Medium | 10.4 s |
| SOD-008 | U009 | Inventory_Adjust + Inventory_Count_Approve | Low | 9.9 s |

\* The first explanation includes loading the model.

![The findings page: severity comes from the rules, the explanation from the model](UPLOAD_slothguard_frame_03_phase2_findings.png)
*Figure 3. The findings page. Severity comes from the rules; the Explanation column comes from Gemma. Frame from the demo video.*

Here is the first finding in full. This is what Gemma wrote in the committed run of 23 Oct, in 4 sentences (`docs/evidence/report-sample.md`). The frame above comes from a later run, so its wording differs:

> Holding both the Vendor_Master_Maintain and Payment_Release roles creates a significant risk because a single user has the ability to create a vendor and then process payments for that vendor. This conflict violates the Separation of Duties (SOD-001) principle, allowing for potential fraud, such as creating fictitious vendors and issuing payments. To mitigate this, review the access controls to ensure that the authority to maintain vendor master data is strictly separated from the authority to release payments. Consider restricting the Payment_Release role to only payments against existing, approved vendors.

When a person proposes revoking a role, the request reaches the phone as a Guardian push. The page shows Waiting and refreshes by itself.

![The Guardian request on the phone](UPLOAD_slothguard_frame_05_phone_approve_request.png)
*Figure 4. The request on the phone: revoke `Vendor_Master_Maintain` from U001. "Negar" is Deny, "Permitir" is Allow. Tenant and e-mail are hidden.*

The request can end three ways, and each one ends differently:

![Three outcomes: Approved, Denied and Expired](UPLOAD_slothguard_outcomes_composite.png)
*Figure 5. The three outcomes. Approved: the role was revoked from U001 in the program's memory only. Denied: the request for U003 was denied on the phone. Expired: nobody answered the request for U002, so nothing was revoked. Frames from the demo video.*

![Audit trail](UPLOAD_slothguard_frame_09_audit_trail.png)
*Figure 6. The audit trail after the runs: U001 proposed, approved, executed; U002 proposed and expired (two attempts); U003 proposed and denied.*

## Code

Repository: https://github.com/aridiosilva/SlothGuard

{% github aridiosilva/SlothGuard %}

To run it (PowerShell, from the project folder):

```powershell
ollama pull gemma4:e2b
.\.venv\Scripts\python scripts\run_review.py   # Phase 1: needs Ollama running
.\.venv\Scripts\python scripts\run_app.py      # Phase 2: open http://localhost:8000
```

Use `localhost`, not `127.0.0.1`: it is the address registered in Auth0. The Auth0 settings go in a local `.env` file, which git ignores; the README section "Auth0 setup" lists exactly what to configure.

Tests: 177 passed and 1 skipped, as the README reports (the skipped one needs a running Ollama: set `RUN_OLLAMA_TESTS=1`). The git history shows the `test:` commits before the matching `feat:` ones.

The central idea, the cap and the fallback around the model, from `src/slothguard/llm/__init__.py`:

```python
def explain_finding(
    finding: Finding,
    rule: SoDRule,
    client: LLMClient,
    cache: Optional[ExplanationCache] = None,
    max_sentences: int = MAX_SENTENCES,
) -> Explanation:
    if cache is not None:
        hit = cache.get(finding)
        if hit:
            return Explanation(text=hit, source="cache")

    try:
        answer = client.generate(build_prompt(finding, rule, max_sentences))
    except Exception:
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="model_error")

    text = clean_model_text(answer) if isinstance(answer, str) else ""
    if not text:
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="empty_answer")

    if count_sentences(text) > max_sentences:
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="too_many_sentences")

    if cache is not None:
        cache.put(finding, text)
    return Explanation(text=text, source="model")
```

The prompt asks the model to keep to 4 sentences and not to change the severity. The code does not rely on the model listening: severity comes from the rule, and the cap is checked afterwards.

## How I Built It

**First, can this PC run it?** Before building the explanation step (22 and 23 Oct), I checked whether this machine could carry a model at all. On paper it looked tight: 15.7 GB of usable RAM in a single channel, and a back-of-the-envelope speed ceiling of about 14 tokens per second from memory bandwidth. Then I measured six requests with Gemma 4 E2B: 13.0 to 21.6 tokens per second, with only 4.2 GB of RAM free before the first one. My ceiling was wrong, so I trusted the measurement over the estimate.

**Phase 1: rules first, model second.** The rules run before the model and decide everything that matters: which user, which rule, which severity. Only then does Gemma 4 E2B (the `gemma4:e2b` tag in Ollama, a 4.6 GB download) get the finding and write a short explanation, with thinking turned off. The limit is enforced by the code, not only requested in the prompt: in my first measurements one answer out of six broke it. If one answer fails, comes back empty or goes over the limit, a fixed template is used for that finding and the reason is recorded, so a bad answer never blocks the report. The fallback is not hypothetical: in my first real run of the review script (23 Oct), Ollama was not running, all 8 findings came out as the fixed template in 32.9 s, and the report was still written. Today, if Ollama cannot be reached at all, `run_review.py` stops at once instead of writing a report made only of templates.

**Phase 2: the human step.** The web app lets a reviewer log in through Auth0 Universal Login and propose a revocation from the findings page. The app starts a CIBA request, and Auth0 sends a push to the Guardian app on the phone, carrying a short message such as `SoD#SOD-001:revoke-Vendor_Master_Maintain-from-U001`. The page polls `GET /proposals/<id>` about every 3 seconds until the answer arrives. Approved, denied or expired, each outcome goes to the audit trail. The gateway fails closed: an error, an unknown answer or a timeout (120 s) all mean "do not revoke". The text on the phone is the text shown on the page, so the approver sees what they are approving. I checked all three outcomes in the real interface.

![Web server log and Auth0 log](UPLOAD_slothguard_evidence_composite.png)
*Figure 7. Evidence. Top: the web server log, one POST per proposal and then a GET about every 3 seconds (login callback values hidden). Bottom: the Auth0 log, from CIBA start to token exchange. Tenant name and address are hidden.*

**Tests first.** For each piece I wrote the tests before the code and committed them separately, so the history shows `test:` commits before the matching `feat:` ones. The Auth0 and Ollama calls are covered with fakes, and I checked the real services by hand.

**Pair-programming with an AI.** I built SlothGuard as the human developer, in pair-programming with an AI coding assistant, Claude (Anthropic). I set the goal, the requirements and the architecture, made the project decisions, reviewed and verified the code, and did every manual step myself: the Auth0 configuration, the Guardian and Ollama setup, and running the commands. Claude helped with code suggestions, debugging, tests and documentation drafts. It did not set the direction, and it is not part of the product: the AI inside the product is Gemma 4 E2B. Figure 8 shows the split; the full account is in the [README](https://github.com/aridiosilva/SlothGuard#credits).

![Pair-programming context](UPLOAD_slothguard_pair_programming_context.png)
*Figure 8. Diagram redrawn and extended with Claude at the author's direction.*

## Why Does Open Innovation Matter?

**The data stays on my machine.** The explanation comes from a model I run myself. The list of who holds which role never goes to a model provider. What leaves the machine is the login and one short approval message that Auth0 delivers to the phone. That is the whole trade, and it is visible on the phone screen in the video.

**Phase 1 works offline.** I ran it with the PC in airplane mode, after a connectivity check returned `False`: 8 of 8 explanations came from the local model, in 63.5 s. Only Phase 2 needs the internet, because Auth0 does.

**I can measure and tune it.** Because I run the model, I could look at tokens and seconds on the machine that does the work. Gemma writes a long thinking trace before each answer. Turning it off cut the generated tokens by about 81% (506 to 94 on average, three runs each) and took a warm explanation from about 27 s to about 6 s, at the same speed per token (13 to 22 tokens per second). I measured it, I did not assume it (`docs/evidence/ollama-baseline.md`).

**It is small enough for an ordinary PC.** Everything ran on a Dell 24 All-in-One (EC24250). The workbook `docs/recursos_hardware_e_limitacoes_v2.xlsx` in the repository has the full table of resources and limits (in Portuguese). In short:

| Item | Value |
|---|---|
| Machine | Dell 24 All-in-One EC24250, Windows 11 |
| CPU | Intel Core i5-1334U (13th gen), 10 cores (2 performance + 8 efficiency), 15 W base |
| RAM | 16 GB (15.7 GB usable), SODIMM at 5200 MT/s, single channel (1 of 2 slots used) |
| GPU | Intel UHD Graphics, 128 MB dedicated, borrows system RAM; I did not verify whether Ollama used it |
| Software | Ollama 0.40.8 (0.40.10 later), `gemma4:e2b` (4.6 GB on disk), Python 3.14.7 |

**I can swap the model.** The client sends one request to a local server, so trying another open-weight model is a change of the model name. I only tested Gemma 4 E2B, and a model without a thinking mode may need the thinking switch removed.

**Where open did not clearly win.** I did not compare against a closed model, so I make no claim that Gemma explains better or cheaper. A small local model is slow here (63.5 to 157.4 s for eight explanations, depending on the run) and sometimes picks words I would not: in my baseline it wrote "critical" in 4 of 6 answers for findings the rule rates "high". That is why it only explains. Auth0 is a hosted service and the approval step needs the internet. What the open model gives me is control over where the sensitive part runs, not a benchmark.

## The Lazy Payoff

Only numbers I measured. Phase 1, 40 users against 9 rules, 8 findings, all 8 explained by the model. The table lists the runs that have a file in the repository or in its history, plus the run shown in the video:

| Run | Total time | Conditions |
|---|---|---|
| 23 Oct, `review-run.md` | 97.1 s | Free RAM 6.1 GB; Ollama started by hand; ChatGPT closed. The first finding takes 23.9 s because it includes loading the model; the other seven take 9.8 to 11.5 s |
| 23 Oct, `review-run-4.3gb-2026-10-23.md` | 139.0 s | Free RAM 4.3 GB; power mode not checked; ChatGPT closed, but Claude and a browser still open; model unloaded before the run; Ollama started by hand. The first finding takes 52.8 s; the other seven take 10.5 to 13.9 s |
| 23 Oct, `review-run-low-ram.md` | 157.4 s | Free RAM 1.1 GB; Windows just restarted and other apps open, so not a clean run. The first finding takes 57.8 s |
| 24 Oct, the run shown in the video | 98.9 s | Conditions not recorded; this run is not committed |
| 25 Oct, `review-run-airplane-two-browsers-2026-10-25.md` | 104.1 s | Airplane mode on, two browsers open; free RAM not measured; connectivity not tested. The first finding takes 26.4 s |
| 25 Oct, `review-run-offline-2026-10-25.md` | 63.5 s | Offline (connectivity check returned `False`); free RAM 2.1 GB before the run. The first finding takes only 6.8 s, so the model was probably still loaded from the previous run (my inference); the other seven take 6.0 to 8.9 s |

In the three runs of 23 Oct, more free memory meant a faster run (97.1 s, 139.0 s, 157.4 s). The offline run of 25 Oct shows it is not the whole story: it was the fastest, with only 2.1 GB free, although the model was probably already loaded. So the reviewer's wait is a range, from 63.5 s to 157.4 s, and I have not diagnosed why. Before building the pipeline I had estimated 54 to 73 s for eight findings from a small benchmark (an estimate, not a measurement; same workbook). The offline run falls inside that range and the other recorded runs fall above it.

Quality check (`docs/evidence/review-quality.md`): 8 findings, 8 explained, all 8 within 4 sentences. One explanation (SOD-007, U008) used the word "critical" for a finding the rule rates medium.

I did not measure how much time this saves compared with reviewing by hand, and I do not claim a number.

## Limits

- **Synthetic data only.** 40 users and 9 rules. This is a prototype, not a product.
- **The revocation changes a copy in memory.** Nothing touches a real identity system, and the audit trail resets when the app restarts.
- **A small model drifts.** In the final run all 8 explanations stayed within 4 sentences, but one called a medium finding "critical"; in my baseline "critical" appeared in 4 of 6 answers for "high" findings, and one answer had 5 sentences. That is why severity comes from the rules and the code enforces the limit. My quality check counts sentences and severity words; it does not judge whether an explanation is correct.
- **Timing varies.** See the table above.
- **The timeout.** U002's request expired after 120 s with no answer; the audit trail shows two such attempts.
- **Rough edges in my own recording.** The first login attempt ended in a 400 error page, and the second one worked. The Auth0 log also warns that development keys are in use for the Google connection. The phone clips are from separate runs, recorded at 22:20, 22:29 and 22:33. The captions say so.
- **GPU use not verified.** The machine has only Intel UHD graphics, which borrow system RAM. I ran Ollama with its default settings and did not check whether the integrated GPU was used.
- **One person can play both roles.** In my demo the proposer and the approver can be the same Auth0 user. A real deployment needs two people.
- **The approval message leaves the machine.** It contains the user id and the role name, and that text goes to Auth0. With real data I would send opaque ids.
- **Auth0 free trial.** I checked the asynchronous approval on an Auth0 tenant during its free trial period. I have not verified whether it is available after the trial.
- **Development server.** The web server is Flask's development server, meant for local use.
- **No claim of novelty.** I did not search for prior work, so I do not call the project new in any way beyond "built this week".
- **Commits after the deadline.** None.

## Prize Categories

- **Best Use of Auth0 for AI Agents.** The challenge page lists "ask a person to approve a risky action before the agent takes it" as a use. SlothGuard's central step is that: a revocation is only proposed until a person answers through Auth0 CIBA and Guardian, with Universal Login for the sign-in. Honest note: the asynchronous approval worked on my Auth0 tenant during its free trial period, and I have not checked whether it is available after the trial.
- **Best Use of Gemma.** Gemma 4 E2B runs locally through Ollama and writes every explanation in the demo, with no cloud call for the model.

## Primary sources

- [Hacktoberfest Open-Source AI Challenge: Week 3](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)
- [General Contest Official Rules](https://dev.to/page/official-hackathon-rules)
- [Auth0 for AI Agents](https://auth0.com/ai/docs)
- [Gemma](https://ai.google.dev/gemma)

## Credits

Built by Aridio Silva, Independent Researcher ([@aridiosilva](https://dev.to/aridiosilva)), ORCID 0009-0008-2411-6995, with AI help (pair-programmed with Claude). Libraries: Flask, Authlib, Requests, pytest. Model: Gemma 4 E2B, run through Ollama. Identity and approval: Auth0 (Universal Login, CIBA, Guardian). The Auth0 and Ollama documentation were used for the request formats.

Images, video and metadata: © Aridio Silva @aridiosilva, 24 Oct 2026.

Licenses: the code is under the MIT License; the documentation, figures, video and text of this post are under CC BY 4.0 (`LICENSE` and `LICENSE-DOCS.txt` in the repository).

## Full demo video

{% embed https://youtu.be/9JlqE3jBITk %}
