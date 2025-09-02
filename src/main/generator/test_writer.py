# src/main/generator/test_writer.py
import os
import re
import yaml
from .file_util import ensure_dir, read_text, write_text, class_name_from_path, find_package_decl

def load_cfg():
    here = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(here, "config", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

HEADER_JUNIT4 = """\
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

"""

HEADER_JUNIT5 = """\
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

"""

class TestWriter:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_cfg()
        self.junit = self.cfg["java"]["junit_version"]
        self.default_out = self.cfg["test"]["default_path"]
        self.test_pkg_suffix = self.cfg["java"].get("test_package_suffix", "")

    def _header(self) -> str:
        return HEADER_JUNIT4 if self.junit == "4" else HEADER_JUNIT5

    def _setup_block(self) -> str:
        return (
            "    @Before\n    public void setup() { MockitoAnnotations.openMocks(this); }\n\n"
            if self.junit == "4" else
            "    @BeforeEach\n    void setup() { MockitoAnnotations.openMocks(this); }\n\n"
        )

    def _compute_out_path(self, test_root: str, package: str, test_class: str) -> str:
        # mirror package dirs under root
        pkg_dir = package.replace(".", "/") if package else ""
        out_dir = os.path.join(test_root, pkg_dir)
        ensure_dir(out_dir)
        return os.path.join(out_dir, f"{test_class}.java")

    def _derive_test_package(self, orig_package: str) -> str:
        return (orig_package + self.test_pkg_suffix).strip(".")

    def write_or_update(self, src_path: str, class_info: dict, method_name: str, test_method_code: str, test_root: str = None):
        package = class_info.get("package", find_package_decl(src_path) or "")
        primary = class_info["primary_class"]["name"]
        test_class = f"{primary}Test"

        test_root = test_root or self.default_out
        ensure_dir(test_root)
        test_package = self._derive_test_package(package)
        test_file = self._compute_out_path(test_root, test_package, test_class)

        if not os.path.exists(test_file):
            # Create brand new class file
            parts = []
            if test_package:
                parts.append(f"package {test_package};\n\n")
            parts.append(self._header())
            parts.append(f"public class {test_class} {{\n")
            parts.append(self._setup_block())
            parts.append(test_method_code if test_method_code.endswith("\n") else test_method_code + "\n")
            parts.append("}\n")
            write_text(test_file, "".join(parts))
            print(f"✅ Created test class: {test_file}")
            return

        # Append method if not present
        content = read_text(test_file)
        # Avoid duplicates: look for method signature marker
        if re.search(rf"\btest_{re.escape(method_name)}\b", content):
            print(f"ℹ️  Test method for '{method_name}' already exists in {test_file}, skipping.")
            return

        new_content = re.sub(r"\}\s*$", "", content, count=1).rstrip() + "\n" + \
                      (test_method_code if test_method_code.endswith("\n") else test_method_code + "\n") + \
                      "}\n"
        write_text(test_file, new_content)
        print(f"✚ Appended test for method '{method_name}' → {test_file}")
