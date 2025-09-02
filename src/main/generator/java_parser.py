# src/main/generator/java_parser.py
from tree_sitter_languages import get_parser

class JavaParser:
    """
    AST-based parser using tree-sitter.
    Extracts: package, class name, fields, and only non-private methods.
    """
    def __init__(self):
        self.parser = get_parser("java")

    def _bytes(self, s: str) -> bytes:
        return s.encode("utf-8")

    def parse_class_info(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            src = f.read()

        tree = self.parser.parse(self._bytes(src))
        root = tree.root_node

        package_name = self._extract_package(root, src)
        classes = self._extract_classes(root, src)

        if not classes:
            return {"package": package_name, "classes": []}

        main_class = next((c for c in classes if c.get("is_public")), classes[0])
        return {
            "package": package_name,
            "classes": classes,
            "primary_class": main_class
        }

    # ----- helpers -----

    def _text(self, src: str, node) -> str:
        return src[node.start_byte:node.end_byte]

    def _extract_package(self, root, src: str) -> str:
        for child in root.children:
            if child.type == "package_declaration":
                text = self._text(src, child)
                return (
                    text.strip()
                        .removeprefix("package")
                        .removesuffix(";")
                        .strip()
                )
        return ""

    def _extract_classes(self, root, src: str):
        result = []
        stack = [root]
        while stack:
            node = stack.pop()
            stack.extend(node.children or [])
            if node.type == "class_declaration":
                result.append(self._class_info(node, src))
        return result

    def _class_info(self, node, src: str) -> dict:
        name = ""
        is_public = False
        fields = []
        methods = []
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        for ch in node.children:
            if ch.type == "identifier":
                name = self._text(src, ch)
                break

        for ch in node.children:
            if ch.type == "modifiers":
                if "public" in self._text(src, ch).split():
                    is_public = True

        body = next((c for c in node.children if c.type == "class_body"), None)
        if body:
            for bd in body.children:
                if bd.type == "field_declaration":
                    fields.extend(self._field_decl(bd, src))
                elif bd.type == "method_declaration":
                    m = self._method_decl(bd, src)
                    if m["visibility"] != "private":   # 🚀 ignore private methods
                        methods.append(m)

        return {
            "name": name,
            "is_public": is_public,
            "fields": fields,
            "methods": methods,
            "start_line": start_line,
            "end_line": end_line
        }

    def _field_decl(self, node, src: str):
        tpe_node = next((c for c in node.children if c.type == "type"), None)
        tpe = self._text(src, tpe_node).strip() if tpe_node else ""
        out = []
        for ch in node.children:
            if ch.type == "variable_declarator":
                name_node = next((c for c in ch.children if c.type == "identifier"), None)
                if name_node:
                    out.append({"type": tpe, "name": self._text(src, name_node)})
        return out

    def _method_decl(self, node, src: str):
        name = ""
        visibility = "package"
        is_static = False
        ret_type = "void"
        throws = []
        params = []

        mods = next((c for c in node.children if c.type == "modifiers"), None)
        if mods:
            mtext = self._text(src, mods)
            if "public" in mtext.split(): visibility = "public"
            elif "protected" in mtext.split(): visibility = "protected"
            elif "private" in mtext.split(): visibility = "private"
            is_static = "static" in mtext.split()

        tpe = next((c for c in node.children if c.type == "type"), None)
        if tpe:
            ret_type = self._text(src, tpe).strip()

        ident = next((c for c in node.children if c.type == "identifier"), None)
        if ident: name = self._text(src, ident)

        param_list = next((c for c in node.children if c.type == "formal_parameters"), None)
        if param_list:
            for p in param_list.children:
                if p.type in ("formal_parameter", "receiver_parameter"):
                    ptype = next((c for c in p.children if c.type == "type"), None)
                    pname = next((c for c in p.children if c.type == "identifier"), None)
                    params.append({
                        "type": self._text(src, ptype).strip() if ptype else "",
                        "name": self._text(src, pname) if pname else ""
                    })

        throws_node = next((c for c in node.children if c.type == "throws"), None)
        if throws_node:
            for t in throws_node.children:
                if t.type in ("identifier", "scoped_type_identifier"):
                    throws.append(self._text(src, t))

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        return {
            "name": name,
            "visibility": visibility,
            "static": is_static,
            "return_type": ret_type,
            "params": params,
            "throws": throws,
            "start_line": start_line,
            "end_line": end_line
        }
