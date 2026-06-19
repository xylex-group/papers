from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".latex-build",
    "node_modules",
    "target",
    "dist",
    "build",
}


def is_included(path: Path) -> bool:
    return not any(part in EXCLUDED_PARTS for part in path.parts)


def md_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def md_link(label: str, path: Path) -> str:
    href = quote(path.as_posix())
    return f"[{md_escape(label)}]({href})"


def clean_latex_text(value: str) -> str:
    value = re.sub(r"%.*", "", value)
    value = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_title(tex_path: Path) -> str:
    try:
        content = tex_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return tex_path.stem.replace("-", " ").replace("_", " ").title()

    match = re.search(r"\\title(?:\[[^\]]*\])?\{(.+?)\}", content, re.DOTALL)
    if not match:
        return tex_path.stem.replace("-", " ").replace("_", " ").title()

    title = clean_latex_text(match.group(1))
    return title or tex_path.stem.replace("-", " ").replace("_", " ").title()


def relative_files(pattern: str) -> list[Path]:
    files: list[Path] = []

    for path in ROOT.rglob(pattern):
        rel = path.relative_to(ROOT)
        if is_included(rel):
            files.append(rel)

    return sorted(files, key=lambda p: p.as_posix().lower())


def main() -> None:
    tex_files = relative_files("*.tex")
    pdf_files = relative_files("*.pdf")

    pdf_set = set(pdf_files)
    tex_pdf_outputs = {tex.with_suffix(".pdf") for tex in tex_files}
    standalone_pdfs = [pdf for pdf in pdf_files if pdf not in tex_pdf_outputs]

    lines: list[str] = []

    lines.append("# Papers")
    lines.append("")
    lines.append(
        "This README is generated automatically from the repository's LaTeX and PDF files."
    )
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    lines.append(f"- LaTeX sources: **{len(tex_files)}**")
    lines.append(f"- PDFs: **{len(pdf_files)}**")
    lines.append(
        f"- Last generated: **{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}**"
    )
    lines.append("")
    lines.append("## Index")
    lines.append("")
    lines.append("| Paper | Source | PDF | Status |")
    lines.append("|---|---:|---:|---|")

    for tex in tex_files:
        title = extract_title(ROOT / tex)
        expected_pdf = tex.with_suffix(".pdf")

        source = md_link(tex.name, tex)
        if expected_pdf in pdf_set:
            pdf = md_link(expected_pdf.name, expected_pdf)
            status = "Built"
        else:
            pdf = "Missing"
            status = "Source only"

        lines.append(
            f"| {md_escape(title)} | {source} | {pdf} | {status} |"
        )

    for pdf in standalone_pdfs:
        title = pdf.stem.replace("-", " ").replace("_", " ").title()
        lines.append(
            f"| {md_escape(title)} | — | {md_link(pdf.name, pdf)} | PDF only |"
        )

    lines.append("")
    lines.append("## Build")
    lines.append("")
    lines.append(
        "PDFs are compiled from `.tex` sources by GitHub Actions using `latexmk`."
    )
    lines.append(
        "The workflow then regenerates this README and commits the updated PDFs and manifest."
    )
    lines.append("")

    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
