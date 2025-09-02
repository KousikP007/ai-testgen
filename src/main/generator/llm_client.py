# src/main/generator/llm_client.py
import subprocess, time, re, yaml, os

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

    def _render_prompt(self, class_info: dict, methods: list) -> str:
        pkg = class_info.get("package", "")
        cls = class_info["primary_class"]["name"]

        methods_text = "\n".join([
            f"- {m['name']}({', '.join([p['type'] for p in m['params']])}) returns {m['return_type']} [{m['visibility']}]"
            for m in methods
        ])

        return f"""
You are a senior Java engineer. Generate COMPILE-READY JUnit {self.junit} test methods (NO explanations) for:

Class: {cls}
Package: {pkg}

Target methods:
{methods_text}

Constraints:
- Use Mockito to mock dependencies.
- If exceptions are expected, add explicit tests.
- Return ONLY code with @Test methods (no class/headers).
"""

    def _call_ollama(self, prompt: str) -> str:
        start = time.time()
        try:
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
            m = CODE_BLOCK_RE.search(raw)
            return m.group(1).strip() if m else raw
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return ""

    def generate_test_methods(self, class_info: dict, methods: list) -> dict:
        if self.provider == "mock":
            return {
                m["name"]: f"    @Test\n    public void test_{m['name']}() {{\n        assertTrue(true);\n    }}\n"
                for m in methods
            }

        prompt = self._render_prompt(class_info, methods)
        code = self._call_ollama(prompt)

        # crude split: slice into individual @Test blocks
        tests = {}
        for block in re.split(r"(?=@Test\b)", code):
            if not block.strip(): continue
            header_line = block.split("\n")[0]
            name_match = re.search(r"test_(\w+)", block)
            method_name = name_match.group(1) if name_match else f"gen_{len(tests)}"
            tests[method_name] = "    " + block.strip().replace("\n", "\n    ") + "\n"

        return tests
