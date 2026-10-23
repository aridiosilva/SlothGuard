# Review run

Date: 2026-10-23
Model: gemma4:e2b (thinking off)
Users: 40 | Rules: 9 | Findings: 8
Explanations by source: model=8, cache=0, fallback=0
Total time: 157.4 s
Conditions: free RAM 1.1 GB before the run (low); power mode not checked; Windows restarted, Ollama started by hand; other apps were still open (largest processes before the run: ServiceShell 1610 MB, ChatGPT 1041 MB, claude 557 MB, msedgewebview2 537 MB, explorer 419 MB). Not a clean-conditions run.

Per finding (the first one includes loading the model):
- SOD-001 | U001: model, 57.8 s
- SOD-002 | U002: model, 14.2 s
- SOD-003 | U003: model, 15.6 s
- SOD-006 | U004: model, 12.8 s
- SOD-004 | U010: model, 14.6 s
- SOD-005 | U007: model, 11.7 s
- SOD-007 | U008: model, 17.0 s
- SOD-008 | U009: model, 13.6 s
