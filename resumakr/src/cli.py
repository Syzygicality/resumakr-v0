import re
import typer
import subprocess
import httpx
from ruamel.yaml import YAML

from pathlib import Path
from time import perf_counter

from resumakr.src.schemas.cli import app as schema_app
from resumakr.src.database.cli import app as database_app

app = typer.Typer(help="Resumakr CLI")
app.add_typer(database_app)
app.add_typer(schema_app, name="schema", help="Schema-related commands.")


ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


@app.command(hidden=True)
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


@app.command(hidden=True)
def precommit():
    """Install and run pre-commit hooks on all files."""
    subprocess.run(["pre-commit", "install"], check=True)
    result = subprocess.run(["pre-commit", "run", "--all-files"])
    if result.returncode != 0:
        subprocess.run(["pre-commit", "run", "--all-files"])


@app.command()
def template():
    """Render resume.tex from resume.yaml at the repo root."""
    import jinja2
    from resumakr.src.schemas.schemas import Resume

    start = perf_counter()
    root = Path(ROOT_DIR)
    resume_path = root / "resume.yaml"

    if not resume_path.exists():
        typer.echo(f"Error: {resume_path} not found", err=True)
        raise typer.Exit(1)

    raw = YAML().load(resume_path.read_text())
    try:
        validated = Resume.model_validate(raw)
    except Exception as exc:
        typer.echo(f"Validation error:\n{exc}", err=True)
        raise typer.Exit(1)

    templates_dir = Path(__file__).parent.parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        block_start_string="((%",
        block_end_string="%))",
        variable_start_string="((",
        variable_end_string="))",
        comment_start_string="((#",
        comment_end_string="#))",
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tex_bold"] = lambda s: re.sub(
        r"(?<!\\)%", r"\\%", str(s)
    )  # this filter only needs to escape bare % signs for LaTeX.
    env.filters["display_url"] = lambda url: re.sub(
        r"^https?://(www\.)?", "", str(url)
    ).rstrip("/")

    rendered = env.get_template("resume.tex.j2").render(resume=validated.resume)

    out = root / "resume.tex"
    out.write_text(rendered)
    end = perf_counter()
    typer.echo(f"Written to {out} in {(end - start) * 1000:.2f} ms.")


@app.command()
def compile():
    """Compile resume.tex via the local LaTeX API and write resume.pdf."""
    start = perf_counter()
    root = Path(ROOT_DIR)
    tex_path = root / "resume.tex"
    pdf_path = root / "resume.pdf"

    if not tex_path.exists():
        typer.echo(f"Error: {tex_path} not found", err=True)
        raise typer.Exit(1)

    source = tex_path.read_text()
    response = httpx.post("http://localhost:8000/compile", json={"source": source})

    if response.status_code != 200:
        typer.echo(
            f"Compile error:\n{response.json().get('detail', response.text)}", err=True
        )
        raise typer.Exit(1)

    pdf_path.write_bytes(response.content)
    end = perf_counter()
    typer.echo(f"Written to {pdf_path} in {(end - start) * 1000:.2f} ms.")


@app.command()
def build():
    """Template and compile resume.yaml → resume.tex → resume.pdf."""
    template()
    compile()


@app.command()
def autobuild():
    """Watch resume.yaml and rebuild on every change (250ms debounce)."""
    import asyncio
    from watchfiles import awatch

    root = Path(ROOT_DIR)
    resume_path = root / "resume.yaml"

    async def _run():
        typer.echo(f"Watching {resume_path} ... (Ctrl+C to stop)")
        async for _ in awatch(resume_path, debounce=250):
            try:
                build()
            except SystemExit:
                pass

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        typer.echo("Stopped.")


if __name__ == "__main__":
    app()
