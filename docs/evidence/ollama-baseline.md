
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
