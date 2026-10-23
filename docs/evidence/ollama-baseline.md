# Ollama baseline (T05)

Date: 2026-10-23 (runs between 00:03 and 00:12 local time)
Machine: Dell 24 All-in-One EC24250, Intel i5-1334U, 16 GB RAM (single channel), Windows 11
Ollama version: 0.40.8
Model: gemma4:e2b (4.6 GB on disk)
Conditions: free RAM before the first run: 4.2 GB (measured twice); not measured before the other runs or during any run; power mode and open programs: not recorded.

## Thinking enabled (default)

| Run | Load | Prompt eval (tok/s) | Prompt tokens (cached) | Eval count | Eval rate (tok/s) | Total |
|---|---|---|---|---|---|---|
| 1 (cold) | 15.46 s | 78.23 | 109 (0) | 508 | 16.94 | 46.89 s |
| 2 | 18.79 ms | 38.86 | 109 (104) | 521 | 19.42 | 26.98 s |
| 3 | 31.36 ms | 40.34 | 109 (104) | 489 | 18.10 | 27.18 s |

Notes:
- Warm eval rate (runs 2-3): mean 18.76 tok/s.
- In runs 2-3 the prompt eval rate appears to cover only the uncached tokens, so it is not comparable with run 1.
- The model wrote "critical" in runs 1 and 2 although the rule severity was "high".
## Thinking disabled (--think=false), 2026-10-23 ~00:10-00:12

| Run | Load | Prompt eval (tok/s) | Prompt tokens (cached) | Eval count | Eval rate (tok/s) | Total |
|---|---|---|---|---|---|---|
| 1 | 13.98 s | 85.93 | 102 (0) | 84 | 20.02 | 19.39 s |
| 2 | 11.26 ms | 38.99 | 102 (97) | 102 | 21.56 | 4.88 s |
| 3 | 8.23 ms | 38.33 | 102 (97) | 97 | 13.00 | 7.60 s |

Notes:
- Mean generated tokens: 506 with thinking on vs 94 with thinking off (about 81% fewer). Mean eval rate is the same (18.15 vs 18.19 tok/s), so the gain comes from fewer tokens.
- Warm total time (runs 2-3): 27.08 s with thinking vs 6.24 s without (about 4.3x faster).
- Eval rate varied from 13.00 to 21.56 tok/s; cause not measured.
- Estimate (not measured end to end): 8 findings take about 54-73 s with thinking off (19.39 s for the first, which includes the model load, plus 7 warm runs of 4.88-7.60 s).
- Quality: the word "critical" appeared in 4 of 6 answers although the rule severity was "high"; one answer had 5 sentences despite the 4-sentence limit.
- RAM free and power mode were not recorded for these runs.

