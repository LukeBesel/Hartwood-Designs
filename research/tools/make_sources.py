"""Rebuild research/sources.md from research/raw/search_log.md (run from repo root)."""
import re
raw = open('research/raw/search_log.md').read().split('\n')
out = ["# Sources", "",
       "Every number labeled **Verified** in this project traces to a page listed here.", "",
       "**How these were checked (read this):** the build machine's network policy blocked direct page loads "
       "(robotime.com, amazon.com, walmart.com, wikipedia.org and others returned 403). All facts were taken from a web "
       "search tool that returns each page's title, URL and a short summary of that page. A fact is **Verified** when it "
       "appeared in the summary for the URL listed, on the date shown. I did not open the pages myself, so Lucas should "
       "spot-check key prices (see `TODO_LUCAS.md`).", "",
       "Full notes with the exact facts per source: [`raw/search_log.md`](raw/search_log.md).", ""]
seen = set(); n = 0
for line in raw:
    if line.startswith('## '):
        out += ["", f"## {line[3:].strip()}", ""]
        continue
    for u in re.findall(r'https?://[^\s;)]+', line):
        u = u.rstrip('.,')
        if u in seen:
            continue
        seen.add(u); n += 1
        fact = re.sub(r'https?://\S+', '', line).strip(' -;:').strip()[:160]
        out.append(f"- [{u}]({u}) - checked 2026-10-11 - {fact}")
out += ["", f"Total distinct source URLs: {n}", ""]
open('research/sources.md', 'w').write('\n'.join(out))
print(n, 'sources')
