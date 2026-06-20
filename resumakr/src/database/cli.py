import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

from resumakr.src.database.crud import (
    delete_resume,
    find_resumes_by_label,
    list_resumes,
    save_resume,
)

app = typer.Typer()
console = Console()

ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


@app.command()
def list():
    """List all saved resumes with their tags."""
    resumes = list_resumes()

    if not resumes:
        typer.echo("No resumes found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Label")
    table.add_column("Updated At")
    table.add_column("Created At")
    table.add_column("Tags")

    for r in resumes:
        table.add_row(
            str(r["id"]),
            r["label"],
            r["updated_at"],
            r["created_at"],
            r["tags"] or "-",
        )

    console.print(table)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def save(
    ctx: typer.Context,
    has_tags: Annotated[
        bool,
        typer.Option(
            "--tags", "-t", is_flag=True, help="Tag names follow: -t tag1 tag2 ..."
        ),
    ] = False,
):
    """Save resume.yaml into the database as a revertible snapshot."""
    tags = ctx.args if has_tags else []

    resume_path = Path(ROOT_DIR) / "resume.yaml"

    if not resume_path.exists():
        typer.echo(f"Error: {resume_path} not found", err=True)
        raise typer.Exit(1)

    content = resume_path.read_text()
    raw = YAML().load(content)
    label = raw.get("label")

    if not label:
        typer.echo("Error: resume.yaml has no 'label' field", err=True)
        raise typer.Exit(1)

    save_resume(label, content, tags)
    typer.echo(f"Saved '{label}'." + (f" Tags: {', '.join(tags)}" if tags else ""))


@app.command()
def load(
    label: Annotated[str, typer.Argument(help="Label of the saved resume to load.")],
):
    """Load a saved resume into resume.yaml and build the PDF."""
    matches = find_resumes_by_label(label)

    if not matches:
        typer.echo(f"Error: no resume found matching '{label}'", err=True)
        raise typer.Exit(1)

    if len(matches) > 1:
        exact = [m for m in matches if m["label"] == label]
        if exact:
            resume = exact[0]
        else:
            typer.echo(f"Error: '{label}' matches multiple resumes:", err=True)
            for m in matches:
                typer.echo(f"  {m['label']}", err=True)
            raise typer.Exit(1)
    else:
        resume = matches[0]
    resume_path = Path(ROOT_DIR) / "resume.yaml"
    resume_path.write_text(resume["content"])
    typer.echo(f"Loaded '{resume['label']}' into {resume_path}.")

    from resumakr.src.cli import build

    build()


@app.command()
def remove(
    label: Annotated[
        str, typer.Argument(help="Label (or substring) of the resume to remove.")
    ],
):
    """Remove a saved resume entry by label."""
    matches = find_resumes_by_label(label)

    if not matches:
        typer.echo(f"Error: no resume found matching '{label}'", err=True)
        raise typer.Exit(1)

    if len(matches) > 1:
        exact = [m for m in matches if m["label"] == label]
        if exact:
            resume = exact[0]
        else:
            typer.echo(f"Error: '{label}' matches multiple resumes:", err=True)
            for m in matches:
                typer.echo(f"  {m['label']}", err=True)
            raise typer.Exit(1)
    else:
        resume = matches[0]

    typer.confirm(f"Remove '{resume['label']}'?", abort=True)
    delete_resume(resume["label"])
    typer.echo(f"Removed '{resume['label']}'.")
