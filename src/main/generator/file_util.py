# src/main/generator/file_util.py
import os
import io
import re

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def read_text(path: str) -> str:
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, data: str):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(data)

def class_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

def find_package_decl(java_path: str) -> str:
    try:
        txt = read_text(java_path)
        m = re.search(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", txt, re.MULTILINE)
        return m.group(1) if m else ""
    except Exception:
        return ""
