from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI()


class LatexRequest(BaseModel):
    source: str


@app.post("/compile")
def compile_latex(req: LatexRequest) -> Response:
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "document.tex")
        pdf_path = os.path.join(tmpdir, "document.pdf")

        with open(tex_path, "w") as f:
            f.write(req.source)

        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                tmpdir,
                tex_path,
            ],
            capture_output=True,
            text=True,
        )

        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=422, detail=result.stdout)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

    return Response(content=pdf_bytes, media_type="application/pdf")
