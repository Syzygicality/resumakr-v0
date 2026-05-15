import typer
import subprocess

from pathlib import Path

app = typer.Typer(help="Resumakr CLI")

ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


@app.command()
def clean():
    """Automatically remove metadata directories. (.ruff_cache, __pycache__)"""
    root = Path(ROOT_DIR)
    for folder in [".ruff_cache"]:
        target: Path = root / folder
        if target.exists():
            subprocess.run(["rm", "-r", str(target)], check=True)
    for pycache in root.rglob("__pycache__"):
        if pycache.exists():
            subprocess.run(["rm", "-r", str(pycache)], check=True)


@app.command()
def precommit():
    """Install and run pre-commit hooks on all files."""
    subprocess.run(["pre-commit", "install"], check=True)
    result = subprocess.run(["pre-commit", "run", "--all-files"])
    if result.returncode != 0:
        subprocess.run(["pre-commit", "run", "--all-files"])


if __name__ == "__main__":
    app()
