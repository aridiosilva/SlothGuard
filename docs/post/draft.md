---
title: "SlothGuard: a lazy access reviewer that asks your phone before it revokes anything"
published: false
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

<!-- TODO list before publishing (search this file for "TODO"):
1. Demo video link and screenshots.
2. Repository link (make the repo public first).
3. The Lazy Payoff: the manual baseline time (docs/evidence/lazy-payoff.md).
4. Re-read every number against docs/evidence and fix anything that changed.
5. Set published: true only when everything above is done. -->

## What I Built

Every access review has the same dull core: find the people who hold two roles that should never be combined (the person who can create a vendor *and* release payments), then write down why it matters. It is exactly the kind of work people postpone.

**SlothGuard** does that part for you. Plain code finds the conflicts ("segregation of duties" rules). A small open-weight model running on my own computer writes a short explanation for each finding. And nothing is ever revoked unless a human says yes on their phone.

The principle I held to the whole way: **rules detect, the model explains, a human approves.** The model never decides what is a finding or how severe it is, and it never touches a permission.

On my synthetic data (40 users, 9 rules) it finds 8 conflicts (5 high, 2 medium, 1 low), explains all 8 in about two minutes while I do something else, and then waits. If I propose revoking a role, my phone gets a push with the exact action. Approve and the role is revoked (in this demo, in the program's memory). Deny, or say nothing for two minutes, and nothing happens.

## Demo

TODO: video link (about 3 minutes: findings, a proposal approved on the phone, a denial, the audit trail).

TODO: 2 or 3 screenshots (findings page, the "Waiting" page next to the phone, the audit trail).

## Code

TODO: embed the repository. The history is meant to be read: for each feature, the tests were committed before the code.

All data is synthetic. A revocation only changes the program's in-memory copy.

## How I Built It

**Detection (no AI).** A small rules engine compares each user's roles with each rule, ignoring case and spaces, and sorts the findings by severity. Because it is deterministic, it is easy to test, and the severity shown on screen always comes from the rule.

**Explanations (open-weight model, local).** [Gemma 4 E2B](https://ai.google.dev/gemma) runs through Ollama on my machine: a Dell all-in-one with an Intel Core i5-1334U, 16 GB of RAM in a single memory channel, and no dedicated GPU. For each finding the model gets the rule, the user id and the two roles, and must answer in at most four sentences. The four-sentence limit is enforced by the code, not just requested in the prompt: in my first measurements one answer out of six broke it. If the model fails, answers nothing or breaks the limit, the report falls back to a fixed template and says why. A broken model never blocks the report.

**The thinking switch.** Gemma writes a long "thinking" trace before every answer. On my laptop that trace was about 81% of the tokens it generated. Turning it off (`think: false`) took a warm explanation from about 27 seconds to about 6, with the same speed per token (13 to 22 tokens per second in my runs). I measured this, I did not assume it.

**Approval (Auth0).**
- Sign-in uses Auth0 Universal Login (authorization code flow).
- The risky action, revoking a role, is gated by Auth0's asynchronous authorization (CIBA) with a Guardian push to the approver's phone. The text on the phone, for example `SoD#SOD-001:revoke-Vendor_Master_Maintain-from-U001`, is the same text shown on the page, so the approver sees what they are approving.
- The gateway fails closed: an error, an unknown answer or a timeout means "do not revoke". Denied and expired are separate outcomes, and every step lands in an audit trail.
- I checked all three outcomes in the real interface: approved (the finding left the table), denied (it stayed), and no answer for 120 seconds (it stayed, "Expired").

**Tests first.** I wrote the spec and the tests before the code for each piece and committed them separately, so the history shows red before green. At the end there are 177 passing tests; the Auth0 and Ollama calls are covered with fakes, and I checked the real services by hand.

## Why Does Open Innovation Matter?

- **The permission data stays on my machine.** The explanations are written locally, so a list of who holds which roles does not go to a model API. For an access review, that is the point.
- **I could measure and tune the model on my own hardware.** The 81% saving from switching the reasoning trace off came from looking at tokens and seconds on the machine that does the work.
- **It cost nothing to run.** The model is free to run, the Python libraries are open source, and I paid nothing for Auth0 (see the honest note below).
- **I can swap the model.** The client talks to a local server with one request, so trying another open-weight model is a change of the model name (a model without a thinking mode may need the thinking switch removed; I only tested Gemma 4 E2B).

Where it was *not* better: a small local model is slow (about two minutes for eight explanations here), sometimes uses words you would not choose, and needs checking. That is why it only explains.

## The Lazy Payoff

Unattended, SlothGuard explains the 8 findings in 97 to 157 seconds (three runs; free memory was 6.1, 4.3 and 1.1 GB, so the spread is not diagnosed).

TODO: manual baseline. Time how long the same review takes by hand (find the 8 conflicts in the two files and write a three or four sentence explanation for each) and write the number here. One person, one run: say so.

## Prize Categories

- **Best Use of Gemma:** Gemma 4 E2B runs locally through Ollama and writes every explanation.
- **Best Use of Auth0 for AI Agents:** Auth0 signs the user in, and a person must approve the risky action (revoking a role) on their phone before anything happens. Honest note: the asynchronous approval worked on my Auth0 tenant during its free trial period. I have not checked whether it is available after the trial.

## What it does not do

- It uses synthetic data only and does not connect to any real directory.
- "Revoke" changes an in-memory copy.
- In my demo, the person who proposes and the person who approves can be the same Auth0 user. A real deployment needs two different people.
- The approval message contains the user id and the role name, and that text goes to Auth0. With real data I would send opaque ids.
- The web server is Flask's development server, for local use.
- The demo tenant has Auth0's brute-force protection (blocking on, default threshold) and suspicious IP throttling enabled; I did not harden it further for this demo.

*Built with AI help (I paired with Claude on the spec, the tests and the code); the spec, the tests and the commit history are in the repository.*
