# English version of the graduation thesis

Parallel English files live under `DATN/en/`. Content matches the Vietnamese thesis; only the language changes.

## Completed (this batch)

| File | Content |
|------|---------|
| `Cover.tex`, `Cover2.tex` | Title page |
| `Chapter/0_2_Acknowledgment.tex` | Acknowledgment |
| `Chapter/0_3_Abstract.tex` | Abstract (translated from Vietnamese) |
| `Chapter/1_Introduction.tex` | Chapter 1 — Introduction |
| `Chapter/2_Literature_review.tex` | Chapter 2 — Literature Review |
| `Chapter/4_Theoretical_Analysis.tex` | Chapter 4 — rule design (expanded analysis) |
| `Chapter/5_Numerical_results.tex` | Chapter 5 — evaluation results |
| `Chapter/6_Conclusions.tex` | Chapter 6 — conclusions |
| `Chapter/Appendix_C_Stuxnet.tex` | Appendix — Stuxnet MITM details |
| `main.tex` | Full English build (Ch.1–6 + Appendix C) |

## Compile

From `DATN/en/`:

```bash
pdflatex main.tex
pdflatex main.tex
```

Or use your LaTeX editor with root file `DATN/en/main.tex`.

## Next steps

Translate and add, in order:

- (Optional) Appendix A/B if needed for English version

After each chapter is added, uncomment the matching `\chapter{...}` block in `main.tex`.

## Style note

English uses plain academic wording (simple sentences, no heavy jargon). Technical terms (S7comm, Suricata, IDS, OT, PLC, etc.) are kept as in the original.
