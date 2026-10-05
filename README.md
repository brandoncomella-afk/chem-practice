# Chemistry — At-Home Practice

Self-checking practice problem sets for Mr. Comella's chemistry class,
linked from https://comellascience.com/classes/chemistry/

`index.html` is the landing page; `unit-01.html` … `unit-11.html` are the
per-unit practice sets. Every file is completely self-contained — all
questions, styling, and scripting live inside the single file, and nothing
is loaded from the internet. They work offline and can be opened directly
from disk.

Nothing is collected from students: no accounts, no tracking, no answers
sent anywhere. Everything happens in the browser.

## No-JavaScript question lists (`static/`)

`static/index.html` and `static/unit-01.html` … `static/unit-11.html` show every
question in a unit on one plain page, grouped by skill, with each answer and
explanation behind a "Show answer" fold. They contain no JavaScript at all, as a
fallback for networks that block the interactive pages. Rebuild them from the
unit banks with `python3 build_static.py` whenever a bank changes.
