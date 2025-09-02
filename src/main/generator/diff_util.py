# src/main/generator/diff_util.py
import subprocess
from typing import List, Tuple

def get_changed_line_spans(repo_root: str, file_path: str) -> List[Tuple[int, int]]:
    """
    Returns a list of (startLine, endLine) changed hunks for the given file versus HEAD.
    """
    rel = file_path if file_path.startswith(repo_root) else file_path
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_root, "diff", "--unified=0", "HEAD", "--", rel],
            stderr=subprocess.STDOUT
        ).decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError:
        return []

    spans = []
    # Parse @@ -a,b +c,d @@ headers: we care about the +c,d (new file)
    for line in out.splitlines():
        if line.startswith("@@"):
            # Example: @@ -25,0 +26,3 @@
            plus = line.split("+")[1].split("@@")[0].strip()
            if "," in plus:
                start, count = plus.split(",")
                start = int(start)
                count = int(count)
                spans.append((start, start + max(count, 1) - 1))
            else:
                # single line change
                start = int(plus)
                spans.append((start, start))
    return spans

def methods_touched(spans, methods):
    """
    Map changed line spans to method dicts (from parser).
    """
    touched = []
    for m in methods:
        mrange = (m["start_line"], m["end_line"])
        for (s, e) in spans:
            if not (e < mrange[0] or s > mrange[1]):  # overlap
                touched.append(m)
                break
    # unique by name + range
    uniq = []
    seen = set()
    for m in touched:
        key = (m["name"], m["start_line"], m["end_line"])
        if key not in seen:
            seen.add(key)
            uniq.append(m)
    return uniq
