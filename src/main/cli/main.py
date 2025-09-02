# src/main/cli/main.py
import click
import os
import yaml

from src.main.generator.java_parser import JavaParser
from src.main.generator.diff_util import get_changed_line_spans, methods_touched
from src.main.generator.llm_client import LLMClient
from src.main.generator.test_writer import TestWriter

def load_cfg():
    here = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
    with open(here, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--input", "input_path", required=True, help="Path to source .java file")
@click.option("--test-path", default=None, help="Output root for tests (mirrors packages here)")
@click.option("--only-changed", is_flag=True, default=None, help="If set, generate only for changed methods (git)")
@click.option("--repo-root", default=".", help="Git repo root (for --only-changed)")
def generate(input_path, test_path, only_changed, repo_root):
    """Generate or update tests for a given Java class."""
    cfg = load_cfg()
    junit = cfg["java"]["junit_version"]
    if test_path is None:
        test_path = cfg["test"]["default_path"]
    if only_changed is None:
        only_changed = cfg["test"]["only_changed"]

    parser = JavaParser()
    class_info = parser.parse_class_info(input_path)
    if not class_info.get("primary_class"):
        click.echo("❌ No class found in file.")
        return

    methods = class_info["primary_class"]["methods"]
    if only_changed:
        spans = get_changed_line_spans(repo_root, input_path)
        if not spans:
            click.echo("ℹ️  No git changes detected; nothing to do.")
            return
        methods = methods_touched(spans, methods)
        if not methods:
            click.echo("ℹ️  No changed methods overlap detected; nothing to do.")
            return

    click.echo(f"🔎 Target class: {class_info['primary_class']['name']} (package: {class_info.get('package','')})")
    click.echo("🔧 Test style: JUnit " + junit)
    click.echo(f"🗂  Output root: {test_path}")
    click.echo("🧠 Methods to generate: " + ", ".join(m['name'] for m in methods))

    llm = LLMClient(cfg)
    writer = TestWriter(cfg)

    for m in methods:
        test_method = llm.generate_test_method(class_info, m)
        writer.write_or_update(input_path, class_info, m["name"], test_method, test_root=test_path)

    click.echo("✅ Done.")

if __name__ == "__main__":
    cli()
