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

from .agent_tools import (
    get_example,
    get_schema,
    list_workspace_files,
    read_document,
    read_text_file,
    run_workspace_command,
    write_compose_config,
    write_text_file,
)
from .pipeline import apply_pipeline, validate_pipeline


mcp = FastMCP("lab-compose", json_response=True)


@mcp.tool()
def inspect_capabilities() -> dict:
    """Discover the complete laboratory workflow and available compose capabilities."""
    return {
        "report_block_types": sorted(REGISTRY),
        "report_templates": describe_templates(),
        "terminal_themes": list_terminal_theme_names(),
        "syntax_themes": list_syntax_theme_names(),
        "pipeline_stages": ["screenshots", "report"],
        "config_kinds": ["pipeline", "report", "screenshots"],
        "recommended_workflow": [
            "Inspect files with list_lab_files and read the assignment with read_lab_text or read_lab_document.",
            "Implement the laboratory solution with write_lab_text.",
            "Run and verify it with run_lab_command; save important output to a log_path.",
            "Author screenshots, report, and pipeline configs with write_lab_config.",
            "Validate the complete pipeline with validate_lab_pipeline.",
            "Call apply_lab_pipeline with dry_run=true and an explicit output_root.",
            "Call apply_lab_pipeline with dry_run=false only after successful validation and dry-run.",
        ],
        "safety": {
            "file_tools": "Paths are restricted to the explicit workspace_root.",
            "command_tool": "Commands run without shell parsing but inherit the MCP server process permissions.",
            "generation_tools": "Writes require output_root; pipeline and screenshot generation default to dry-run.",
        },
    }


@mcp.tool()
def get_agent_guide() -> dict:
    """Return instructions for autonomously completing a laboratory and producing its report."""
    return {
        "objective": "Complete the assignment, verify the implementation, preserve evidence, and generate the report.",
        "workflow": inspect_capabilities()["recommended_workflow"],
        "authoring": {
            "schemas": "Call get_compose_schema before authoring each config kind.",
            "examples": "Call get_compose_example for a minimal valid starting point.",
            "configs": "Use write_lab_config so structural errors are rejected before files are written.",
            "evidence": "Use run_lab_command(log_path=...) to preserve console output for screenshot-compose.",
        },
        "completion_criteria": [
            "The implemented solution satisfies the assignment.",
            "Relevant commands or tests exit successfully.",
            "The report references generated evidence.",
            "validate_lab_pipeline and a pipeline dry-run succeed.",
            "The final pipeline generation succeeds without unexpected warnings.",
        ],
    }


@mcp.tool()
def get_compose_schema(kind: str, version: int = 1) -> dict:
    """Return the full JSON Schema for pipeline, report, or screenshots config authoring."""
    return get_schema(kind, version)


@mcp.tool()
def get_compose_example(kind: str) -> dict:
    """Return a minimal pipeline, report, or screenshots configuration example."""
    return get_example(kind)


@mcp.tool()
def list_lab_files(workspace_root: str, pattern: str = "**/*", limit: int = 500) -> dict:
    """List files inside an explicit laboratory workspace."""
    return list_workspace_files(workspace_root, pattern, limit)


@mcp.tool()
def read_lab_text(workspace_root: str, path: str, max_bytes: int = 200_000) -> dict:
    """Read a UTF-8 assignment, source, config, or log file inside a laboratory workspace."""
    return read_text_file(workspace_root, path, max_bytes)


@mcp.tool()
def read_lab_document(workspace_root: str, path: str, max_chars: int = 200_000) -> dict:
    """Extract text from a UTF-8 text, DOCX, or PDF assignment inside a laboratory workspace."""
    return read_document(workspace_root, path, max_chars)


@mcp.tool()
def write_lab_text(workspace_root: str, path: str, content: str, overwrite: bool = False) -> dict:
    """Create a UTF-8 source, data, or documentation file inside a laboratory workspace."""
    return write_text_file(workspace_root, path, content, overwrite)


@mcp.tool()
def write_lab_config(
    workspace_root: str,
    path: str,
    kind: str,
    config: dict,
    overwrite: bool = False,
) -> dict:
    """Validate and write a pipeline, report, or screenshots YAML file inside a laboratory workspace."""
    return write_compose_config(workspace_root, path, kind, config, overwrite)


@mcp.tool()
def run_lab_command(
    workspace_root: str,
    command: list[str],
    cwd: str = ".",
    timeout_seconds: int = 120,
    log_path: str | None = None,
    overwrite_log: bool = False,
    max_output_chars: int = 100_000,
) -> dict:
    """Run an argv-style command for the laboratory and optionally save its output as evidence."""
    return run_workspace_command(
        workspace_root,
        command,
        cwd,
        timeout_seconds,
        log_path,
        overwrite_log,
        max_output_chars,
    )


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
