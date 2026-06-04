"""Thin MCP wrapper around the stable compose Python APIs."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from console_gen.project import render_project, validate_project
from console_gen.themes import list_syntax_theme_names, list_terminal_theme_names
from otchet_compose.config import load_config as load_report_config
from otchet_compose.generator import generate_document
from otchet_compose.generator.blocks import REGISTRY
from otchet_compose.generator.title_page import describe_templates

from .pipeline import apply_pipeline, validate_pipeline


mcp = FastMCP("lab-compose", json_response=True)


@mcp.tool()
def inspect_capabilities() -> dict:
    """Discover available report blocks, templates, and screenshot themes."""
    return {
        "report_block_types": sorted(REGISTRY),
        "report_templates": describe_templates(),
        "terminal_themes": list_terminal_theme_names(),
        "syntax_themes": list_syntax_theme_names(),
        "pipeline_stages": ["screenshots", "report"],
    }


@mcp.tool()
def validate_lab_pipeline(pipeline_path: str) -> dict:
    """Validate an entire lab-compose pipeline without writing files."""
    result = validate_pipeline(pipeline_path)
    return {
        "pipeline": str(Path(pipeline_path).resolve()),
        "screenshot_resources": [resource.name for resource in result["screenshot_resources"]],
        "report_output": result["report_config"]["document"]["output"],
    }


@mcp.tool()
def apply_lab_pipeline(
    pipeline_path: str,
    output_root: str,
    dry_run: bool = True,
    force: bool = False,
    manifest_path: str | None = None,
) -> dict:
    """Run a pipeline; defaults to dry-run and requires an explicit output root."""
    result = apply_pipeline(
        pipeline_path,
        dry_run=dry_run,
        force=force,
        output_root=output_root,
        manifest=manifest_path,
    )
    return {
        "outputs": [str(path) for path in result["outputs"]],
        "warnings": result["warnings"],
        "dry_run": result["dry_run"],
        "manifest": str(result["manifest"]) if result["manifest"] else None,
    }


@mcp.tool()
def validate_report(config_path: str) -> dict:
    """Validate an otchet-compose report config without generating a DOCX."""
    config = load_report_config(Path(config_path))
    return {
        "config": str(Path(config_path).resolve()),
        "output": config["document"]["output"],
        "block_count": len(config["content"]),
    }


@mcp.tool()
def generate_report(config_path: str, output_root: str, force: bool = False) -> dict:
    """Generate a report within an explicit output root."""
    config = load_report_config(Path(config_path))
    output = Path(config["document"]["output"]).resolve()
    _check_output(output, output_root, force)
    warnings: list[str] = []
    output = generate_document(config, quiet=True, warnings=warnings)
    return {"output": str(output), "warnings": warnings}


@mcp.tool()
def validate_screenshots(project_path: str, names: list[str] | None = None) -> dict:
    """Validate selected screenshot resources without rendering PNG files."""
    resources = validate_project(project_path, names)
    return {
        "project": str(Path(project_path).resolve()),
        "resources": [resource.name for resource in resources],
    }


@mcp.tool()
def render_screenshots(
    project_path: str,
    output_root: str,
    names: list[str] | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> dict:
    """Render selected screenshots; defaults to dry-run and requires an explicit output root."""
    outputs = render_project(project_path, names, dry_run=dry_run, force=force, output_root=output_root)
    return {"outputs": [str(path) for path in outputs], "dry_run": dry_run}


def _check_output(output: Path, output_root: str, force: bool) -> None:
    root = Path(output_root).resolve()
    if not output.is_relative_to(root):
        raise ValueError(f"Output path is outside output_root: {output}")
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists; set force=true to overwrite: {output}")


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
