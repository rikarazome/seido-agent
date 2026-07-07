"""Extract the <script> body from web/index.html for the node harnesses.

Writes page_script.js next to this file (gitignored -- regenerate before
each harness run):  python extract_js.py
"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

html = (Path(__file__).resolve().parents[2] / "web" / "index.html").read_text(encoding="utf-8")
m = re.search(r"<script>\n(.*)</script>", html, re.DOTALL)
if not m:
    print("NO SCRIPT FOUND"); sys.exit(1)
out = Path(__file__).resolve().parent / "page_script.js"
out.write_text(m.group(1), encoding="utf-8")
print(f"extracted {len(m.group(1))} chars -> {out.name}")
