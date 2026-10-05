"""Build the no-JavaScript question lists in static/ from the unit-XX.html banks.

Run from the repo root:  python3 build_static.py
Re-run it whenever a unit's question bank changes.
"""
import glob
import html
import json
import os
import re

OUT = "static"
LEVELS = ["Beginner", "Intermediate", "Advanced"]
LETTERS = "ABCD"

CSS = """
*{box-sizing:border-box}
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2024;--muted:#5f6670;--line:#e3e6ea;
 --accent:#1f3864;--accent2:#2e5496;--ok:#0f7b3d;--okbg:#e8f6ed;--chip:#eef1f5}
@media (prefers-color-scheme:dark){
 :root{--bg:#12151a;--card:#1a1e25;--ink:#e8eaed;--muted:#9aa3ad;--line:#2c323b;
 --accent:#8ab4f8;--accent2:#a8c7fa;--ok:#5cd18a;--okbg:#12331f;--chip:#242a33}
}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);
 font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:0 0 60px}
.wrap{max-width:860px;margin:0 auto;padding:0 16px}
header{background:var(--card);border-bottom:1px solid var(--line);padding:22px 0 18px;margin-bottom:20px}
h1{margin:0 0 4px;font-size:23px;color:var(--accent)}
.sub{margin:0;color:var(--muted);font-size:14.5px}
.crumb{font-size:14px;margin:0 0 8px}
a{color:var(--accent2)}
.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin-bottom:18px}
.box p{margin:.35rem 0;font-size:15px}
.toc{columns:2;column-gap:24px;margin:0;padding-left:20px;font-size:15px}
@media(max-width:600px){.toc{columns:1}}
.toc li{margin:2px 0;break-inside:avoid}
.toc .c{color:var(--muted);font-size:13px}
h2{font-size:19px;color:var(--accent);margin:32px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--line)}
.q{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:0 0 12px}
.qh{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.lv{display:inline-block;padding:1px 8px;border-radius:999px;background:var(--chip);margin-left:6px}
.stem{margin:0 0 8px;font-weight:500}
ol.opts{list-style:none;margin:0 0 6px;padding:0}
ol.opts li{padding:3px 0 3px 30px;position:relative}
ol.opts li b{position:absolute;left:0;color:var(--muted)}
details{margin-top:6px;border-top:1px dashed var(--line);padding-top:6px}
summary{cursor:pointer;color:var(--accent2);font-weight:600;font-size:14.5px}
.ans{background:var(--okbg);border-radius:8px;padding:10px 12px;margin-top:8px;font-size:15px}
.ans b{color:var(--ok)}
.top{font-size:13px}
.grid{display:grid;gap:10px}
@media(min-width:620px){.grid{grid-template-columns:1fr 1fr}}
a.unit{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--line);
 border-left:4px solid var(--accent2);border-radius:8px;padding:12px 14px}
a.unit .n{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
a.unit .t{display:block;font-weight:600;color:var(--accent)}
a.unit .s{display:block;font-size:14px;color:var(--muted)}
footer{margin-top:30px;color:var(--muted);font-size:13px;text-align:center}
@media print{
 body{background:#fff;color:#000}
 header,.box,.q{border-color:#bbb}
 .q{break-inside:avoid}
 details{display:none}
}
"""

PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style></head><body>
{body}
</body></html>
"""

e = html.escape


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_units():
    units = []
    for f in sorted(glob.glob("unit-*.html")):
        src = open(f, encoding="utf-8").read()
        bank = json.loads(re.search(r"const BANK = (\[.*?\]);\n", src, re.S).group(1))
        title = html.unescape(re.search(r"<h1>(.*?)</h1>", src).group(1))
        num = re.match(r"Unit (\d+)", title).group(1)
        rest = title.split("—", 1)[1].strip()
        story, topic = [x.strip() for x in rest.split(":", 1)]
        units.append(dict(file=f, num=int(num), title=title, story=story, topic=topic, bank=bank))
    return units


def question_html(q, n):
    opts = "".join(f"<li><b>{L}.</b> {e(o)}</li>" for L, o in zip(LETTERS, q["options"]))
    return (
        f'<div class="q" id="q{q["id"]}">'
        f'<div class="qh">Question {n}<span class="lv">{e(q["level"])}</span></div>'
        f'<p class="stem">{e(q["stem"])}</p>'
        f'<ol class="opts">{opts}</ol>'
        f"<details><summary>Show answer</summary>"
        f'<div class="ans"><b>Answer: {e(q["answer"])}. {e(q["answer_text"])}</b><br>{e(q["exp"])}</div>'
        f"</details></div>"
    )


def unit_page(u):
    bank = u["bank"]
    # Skills in the order they first appear in the bank (the teacher's order).
    tags = list(dict.fromkeys(q["tag"] for q in bank))
    toc = "".join(
        f'<li><a href="#{slug(t)}">{e(t)}</a> <span class="c">({sum(q["tag"] == t for q in bank)})</span></li>'
        for t in tags
    )
    sections, n = [], 0
    for t in tags:
        qs = sorted((q for q in bank if q["tag"] == t), key=lambda q: (LEVELS.index(q["level"]), q["id"]))
        items = []
        for q in qs:
            n += 1
            items.append(question_html(q, n))
        sections.append(
            f'<h2 id="{slug(t)}">{e(t)}</h2>' + "".join(items) + '<p class="top"><a href="#top">Back to skill list</a></p>'
        )
    body = f"""<header id="top"><div class="wrap">
<p class="crumb"><a href="index.html">&larr; All units</a></p>
<h1>{e(u["title"])}</h1>
<p class="sub">{len(bank)} practice questions with answers and explanations</p>
</div></header>
<div class="wrap">
<div class="box">
<p><strong>How to use this page.</strong> Work each question on paper first, then tap <em>Show answer</em> to check yourself. Every answer has an explanation, including why the tempting wrong answer is wrong.</p>
<p>Questions are grouped by skill and go from Beginner to Advanced within each skill. Jump to a skill:</p>
<ol class="toc">{toc}</ol>
</div>
{"".join(sections)}
<footer>Mr. Comella &middot; Chemistry &middot; Nothing on this page is graded or sent anywhere.</footer>
</div>"""
    return PAGE.format(title=e(f"Unit {u['num']} Question List — {u['topic']}"), css=CSS, body=body)


def index_page(units):
    cards = "".join(
        f'<a class="unit" href="unit-{u["num"]:02d}.html"><span class="n">Unit {u["num"]} &middot; {len(u["bank"])} questions</span>'
        f'<span class="t">{e(u["topic"])}</span><span class="s">{e(u["story"])}</span></a>'
        for u in units
    )
    total = sum(len(u["bank"]) for u in units)
    body = f"""<header><div class="wrap">
<h1>Chemistry &mdash; Practice Question Lists</h1>
<p class="sub">All {total} practice questions, every unit, answers included</p>
</div></header>
<div class="wrap">
<div class="box">
<p>These are the same questions as the interactive practice, laid out as one simple page per unit. Work a question, then tap <em>Show answer</em> to check it.</p>
</div>
<div class="grid">{cards}</div>
<footer>Mr. Comella &middot; Chemistry</footer>
</div>"""
    return PAGE.format(title="Chemistry Practice Question Lists", css=CSS, body=body)


def main():
    units = load_units()
    os.makedirs(OUT, exist_ok=True)
    for u in units:
        with open(os.path.join(OUT, f"unit-{u['num']:02d}.html"), "w", encoding="utf-8") as f:
            f.write(unit_page(u))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page(units))
    print(f"{len(units)} units, {sum(len(u['bank']) for u in units)} questions -> {OUT}/")


if __name__ == "__main__":
    main()
