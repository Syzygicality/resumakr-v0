import re
import typer
import subprocess
import httpx
import yaml

from pathlib import Path
from time import perf_counter

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


@app.command()
def schema():
    """Generate resume.schema.json from the Resume model."""
    import json
    from resumakr.schemas import Resume

    root = Path(ROOT_DIR)
    schema_path = root / "resumakr" / "resume.schema.json"
    schema_path.write_text(json.dumps(Resume.model_json_schema(), indent=2) + "\n")
    typer.echo(f"Written to {schema_path}")


@app.command()
def validate(
    resume: Path = typer.Argument(
        Path("resume.yaml"), help="Path to the YAML resume file."
    ),
):
    """Validate a YAML resume file against the Resume schema."""
    from resumakr.schemas import Resume

    if not resume.exists():
        typer.echo(f"Error: {resume} not found", err=True)
        raise typer.Exit(1)

    raw = yaml.safe_load(resume.read_text())
    try:
        Resume.model_validate(raw)
        typer.echo(f"{resume} is valid.")
    except Exception as exc:
        typer.echo(f"Validation error:\n{exc}", err=True)
        raise typer.Exit(1)


@app.command()
def template():
    """Render resume.tex from resume.yaml at the repo root."""
    import jinja2
    from resumakr.schemas import Resume

    root = Path(ROOT_DIR)
    resume_path = root / "resume.yaml"

    if not resume_path.exists():
        typer.echo(f"Error: {resume_path} not found", err=True)
        raise typer.Exit(1)

    raw = yaml.safe_load(resume_path.read_text())
    try:
        validated = Resume.model_validate(raw)
    except Exception as exc:
        typer.echo(f"Validation error:\n{exc}", err=True)
        raise typer.Exit(1)

    templates_dir = Path(__file__).parent / "templates"
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
    # Bold conversion is already done by BulletPointMixin at validation time;
    # this filter only needs to escape bare % signs for LaTeX.
    env.filters["tex_bold"] = lambda s: re.sub(r"(?<!\\)%", r"\\%", str(s))
    env.filters["display_url"] = lambda url: re.sub(
        r"^https?://(www\.)?", "", str(url)
    ).rstrip("/")

    rendered = env.get_template("resume.tex.j2").render(resume=validated.resume)

    out = root / "resume.tex"
    out.write_text(rendered)
    typer.echo(f"Written to {out}")


@app.command()
def build():
    """Template and compile resume.yaml → resume.tex → resume.pdf."""
    template()
    compile()


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


if __name__ == "__main__":
    app()
