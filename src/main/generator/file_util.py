# src/main/generator/file_util.py
import os
import io
import re

def ensure_dir(path: str):
    """
    Ensure that the directory for the given path exists.
    If 'path' is a file path, create its parent directory.
    If 'path' is already a directory, ensure it exists.
    """
    directory = path if os.path.isdir(path) else os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def read_text(path: str) -> str:
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, data: str):
    ensure_dir(path)
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
