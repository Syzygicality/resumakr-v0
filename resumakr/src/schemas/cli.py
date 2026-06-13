import typer
from ruamel.yaml import YAML
import subprocess

from pathlib import Path

app = typer.Typer()

ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


@app.command()
def generate():
    """Generate resume.schema.json from the Resume model."""
    import json
    from resumakr.src.schemas.schemas import Resume

    root = Path(ROOT_DIR)
    schema_path = root / "resumakr" / "src" / "schemas" / "resume.schema.json"
    schema_path.write_text(json.dumps(Resume.model_json_schema(), indent=2) + "\n")
    typer.echo(f"Written to {schema_path}")


@app.command()
def validate():
    """Validate a YAML resume file against the Resume schema."""
    from resumakr.src.schemas.schemas import Resume

    resume = Path("resume.yaml")
    if not resume.exists():
        typer.echo(f"Error: {resume} not found", err=True)
        raise typer.Exit(1)

    raw = YAML().load(resume.read_text())
    try:
        Resume.model_validate(raw)
        typer.echo(f"{resume} is valid.")
    except Exception as exc:
        typer.echo(f"Validation error:\n{exc}", err=True)
        raise typer.Exit(1)
