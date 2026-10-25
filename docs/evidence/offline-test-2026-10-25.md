# Offline test (2026-10-25)

Same machine as ollama-baseline.md. Model gemma4:e2b, thinking off. Source: the console output of two runs of scripts\run_review.py.

## Run 1: airplane mode on, two browsers open
Total 104.1 s. Per finding: 26.4, 10.7, 11.2, 12.1, 11.9, 12.6, 10.2, 9.0 s. Free RAM not measured; connectivity not tested before the run.

## Run 2: offline
Before the run, `Test-Connection -ComputerName 1.1.1.1 -Count 1 -Quiet` returned False. Free RAM before the run: 2.1 GB. Total 63.5 s. Per finding: 6.8, 6.0, 8.3, 8.7, 8.9, 8.8, 8.5, 7.6 s. All 8 explanations came from the model.

## Notes
The first finding of run 2 took 6.8 s against 26.4 s in run 1, so the model was probably still loaded from run 1 (inference, not measured). The other findings were also faster; the cause was not diagnosed. Power mode and other open programs were not recorded.
