# Release checklist (Zenodo, arXiv, supervisor)

Do these in order. Items marked **Author** need your accounts or decisions.

1. **Author:** commit and push everything (`git add -A; git commit; git push`) and run `python -m pytest -q` once more (expect all tests to pass).
2. **Author:** send `paper/PAPER.md` (or the Word copy) and `paper/READING_NOTES.md` to your supervisor. Ask three things: is the framing right ("clean lead except FX, no consistent leakage signature, cannot prove absence"), which venue, and who the authors are.
3. **Author:** decide the licence holder in `LICENSE` and the author list in `CITATION.cff` (both currently list you alone).
4. **Author:** pin model revisions. On the laptop run `pip freeze > results/ENVIRONMENT.txt` and note the Hugging Face commit hash of each model (the model page shows it) in `REPRODUCE.md`.
5. **Author:** open each data licence link in `DATA_SOURCES.md` once; the Wikimedia terms are still marked "confirm".
6. **Author:** on GitHub, create a release (tag `v0.2.0`). Link the repository to Zenodo (zenodo.org, GitHub integration) before creating the release; Zenodo then issues a DOI.
7. Put the DOI in `CITATION.cff` and the paper's reproducibility section.
8. **Author:** arXiv needs an account and, for a first submission in a category, an endorsement; your supervisor can usually endorse. Category suggestion: stat.ML or cs.LG. Prepare the paper as LaTeX or PDF; ask the supervisor which template the target venue wants.
9. Before submitting, re-read Section 6 (limitations) and check that every number in the abstract matches a table (`python paper/make_tables.py`).
