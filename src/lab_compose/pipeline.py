"""Validation and execution of combined artifact pipelines."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml

from console_gen.project import render_project, validate_project
from otchet_compose.config import load_config as load_report_config
from otchet_compose.generator import generate_document

from .schemas import validate_instance


def load_pipeline(path: str | Path) -> dict:
    pipeline_path = Path(path).resolve()
    with pipeline_path.open("r", encoding="utf-8-sig") as handle:
        raw = yaml.safe_load(handle) or {}
    validate_instance(raw, raw.get("version", 1))
    base = pipeline_path.parent
    screenshots = raw.get("screenshots")
    return {
        "path": pipeline_path,
        "screenshots": None
        if screenshots is None
        else {
            "project": _resolve(base, screenshots["project"]),
            "names": screenshots.get("names", []),
        },
        "report": {"config": _resolve(base, raw["report"]["config"])},
        "manifest": _resolve(base, raw["manifest"]) if raw.get("manifest") else None,
    }


def validate_pipeline(path: str | Path) -> dict:
    pipeline = load_pipeline(path)
    resources = []
    if pipeline["screenshots"]:
        resources = validate_project(pipeline["screenshots"]["project"], pipeline["screenshots"]["names"])
    report = load_report_config(pipeline["report"]["config"])
    return {
        "pipeline": pipeline,
        "screenshot_resources": resources,
        "report_config": report,
    }


def apply_pipeline(
    path: str | Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    output_root: str | Path | None = None,
    manifest: str | Path | None = None,
) -> dict:
    validated = validate_pipeline(path)
    pipeline = validated["pipeline"]
    manifest_path = Path(manifest).resolve() if manifest else pipeline["manifest"]
    if manifest_path:
        _check_output(manifest_path, output_root, force)
    report_output = Path(validated["report_config"]["document"]["output"]).resolve()
    _check_output(report_output, output_root, force)

    screenshot_outputs = []
    if pipeline["screenshots"]:
        screenshot_outputs = render_project(
            pipeline["screenshots"]["project"],
            pipeline["screenshots"]["names"],
            dry_run=dry_run,
            force=force,
            output_root=output_root,
        )

    warnings: list[str] = []
    if not dry_run:
        report_output = generate_document(validated["report_config"], quiet=True, warnings=warnings)

    outputs = [*screenshot_outputs, report_output]
    if manifest_path and not dry_run:
        inputs = [pipeline["path"], pipeline["report"]["config"]]
        inputs.extend(resource.input_path for resource in validated["screenshot_resources"])
        manifest_path = _write_manifest(manifest_path, inputs, outputs)
        outputs.append(manifest_path)

    return {
        "outputs": outputs,
        "warnings": warnings,
        "manifest": manifest_path if not dry_run else None,
        "dry_run": dry_run,
        "screenshot_count": len(screenshot_outputs),
    }


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _check_output(output: Path, output_root: str | Path | None, force: bool) -> None:
    if output_root and not output.is_relative_to(Path(output_root).resolve()):
        raise ValueError(f"Output path is outside --output-root: {output}")
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists; use --force to overwrite: {output}")


def _write_manifest(path: Path, inputs: list[Path], outputs: list[Path]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "command": "lab-compose apply",
        "inputs": [_record(item) for item in inputs],
        "outputs": [_record(item) for item in outputs],
    }
    handle = tempfile.NamedTemporaryFile(prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent, delete=False)
    handle.close()
    temp = Path(handle.name)
    try:
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path


def _record(path: Path) -> dict[str, object]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path.resolve()), "sha256": digest, "size": path.stat().st_size}
