# src/main/generator/llm_client.py
import subprocess
import time
import re
import yaml
import os

CODE_BLOCK_RE = re.compile(r"```(?:java|language|)[\r\n]+(.*?)[\r\n]+```", re.DOTALL)

def load_cfg():
    here = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(here, "config", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class LLMClient:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_cfg()
        self.provider = self.cfg["llm"]["provider"]
        self.model = self.cfg["llm"]["model"]
        self.junit = self.cfg["java"]["junit_version"]

    def _render_prompt(self, class_info: dict, method: dict) -> str:
        pkg = class_info.get("package", "")
        cls = class_info["primary_class"]["name"]
        junit = self.junit

        junit_imports = (
            "import org.junit.Test;\nimport static org.junit.Assert.*;\n"
            if junit == "4" else
            "import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n"
        )

        context_note = f"""
You are a senior Java engineer. Generate a COMPILE-READY JUnit test method (no explanations) for:

- Class: {cls}
- Package: {pkg}
- Target method: {method['name']}({", ".join([p['type'] + " " + p['name'] for p in method['params']])})
- Visibility: {method['visibility']}, Returns: {method['return_type']}
- Throws: {", ".join(method['throws']) if method['throws'] else "none"}
- Use Mockito to mock external dependencies (fields in the class).
- The project uses JUnit {junit}. Use the proper annotations and assertions for JUnit {junit}.
- If exceptions are expected, include an explicit test for them
  ({'@Test(expected=Exception.class)' if junit=='4' else 'assertThrows(...)'}).
- Include imports ONLY if you output a full class; if you output a single test method, do not include imports.

Return ONLY code. Prefer a single self-contained @Test method unless setup is necessary.
"""
        return context_note

    def _call_ollama(self, prompt: str) -> str:
        start = time.time()
        try:
            # Use non-JSON normal output (some models don’t support --format json)
            proc = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            took = time.time() - start
            print(f"⏱ LLM call with model={self.model} took {took:.2f} seconds")
            raw = proc.stdout.decode("utf-8", errors="ignore").strip()
            # Try to extract code fence
            m = CODE_BLOCK_RE.search(raw)
            return m.group(1).strip() if m else raw
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return ""

    def generate_test_method(self, class_info: dict, method: dict) -> str:
        if self.provider == "mock":
            # basic stub for offline dev
            name = method["name"]
            return f"    @Test\n    public void test_{name}() {{\n        // TODO auto-generated\n        assertTrue(true);\n    }}\n"
        prompt = self._render_prompt(class_info, method)
        code = self._call_ollama(prompt)
        # If a full class accidentally returned, try to keep only one @Test method
        if "@Test" in code and "class " in code and "{" in code and "}" in code:
            # crude slice: pick first @Test method block
            parts = re.split(r"(?=@Test\b)", code)
            if len(parts) > 1:
                # drop imports/class wrappers; keep the first @Test block
                code = parts[1]
                # ensure it ends with a closing brace
                if code.count("{") > code.count("}"):
                    code += "}\n"
                # indent method to 4 spaces
                code = "    " + code.replace("\n", "\n    ")
        # Ensure method has @Test annotation at least
        if "@Test" not in code:
            code = f"    @Test\n    public void test_{method['name']}() {{\n        // Fallback stub\n        assertTrue(true);\n    }}\n"
        return code
