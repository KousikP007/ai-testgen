# src/main/generator/test_writer.py
# ... keep imports/load_cfg same
import os

from src.main.generator.file_util import write_text, read_text, find_package_decl, ensure_dir


class TestWriter:
    # ... keep __init__, _header, _setup_block, _compute_out_path, _derive_test_package

    def write_or_update(self, src_path: str, class_info: dict, test_methods: dict, test_root: str = None):
        package = class_info.get("package", find_package_decl(src_path) or "")
        primary = class_info["primary_class"]["name"]
        test_class = f"{primary}Test"

        test_root = test_root or self.default_out
        ensure_dir(test_root)
        test_package = self._derive_test_package(package)
        test_file = self._compute_out_path(test_root, test_package, test_class)

        if not os.path.exists(test_file):
            parts = []
            if test_package:
                parts.append(f"package {test_package};\n\n")
            parts.append(self._header())
            parts.append(f"public class {test_class} {{\n")
            parts.append(self._setup_block())
            for code in test_methods.values():
                parts.append(code if code.endswith("\n") else code + "\n")
            parts.append("}\n")
            write_text(test_file, "".join(parts))
            print(f"✅ Created test class: {test_file}")
            return

        content = read_text(test_file)
        added = []
        for mname, code in test_methods.items():
            if re.search(rf"\btest_{re.escape(mname)}\b", content):
                print(f"ℹ️  Test method for '{mname}' already exists in {test_file}, skipping.")
                continue
            content = re.sub(r"\}\s*$", "", content, count=1).rstrip() + "\n" + code + "}\n"
            added.append(mname)

        if added:
            write_text(test_file, content)
            print(f"✚ Appended tests for methods: {', '.join(added)} → {test_file}")
