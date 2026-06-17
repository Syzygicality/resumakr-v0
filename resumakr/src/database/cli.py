import typer
from rich.console import Console
from rich.table import Table

from resumakr.src.database.crud import list_resumes

app = typer.Typer()
console = Console()


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
    table.add_column("Created At")
    table.add_column("Updated At")
    table.add_column("Tags")

    for r in resumes:
        table.add_row(
            str(r["id"]),
            r["label"],
            r["created_at"],
            r["updated_at"],
            r["tags"] or "-",
        )

    console.print(table)
