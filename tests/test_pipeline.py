import json
from pathlib import Path

import pytest

from lab_compose.pipeline import apply_pipeline, validate_pipeline


def _fixture(tmp_path: Path) -> Path:
    screenshots = tmp_path / "screenshots.yml"
    source = tmp_path / "source.log"
    source.write_text("$ echo hello\nhello\n", encoding="utf-8")
    screenshots.write_text(
        """
version: 1
renders:
  terminal:
    input: source.log
    output: build/terminal.png
""",
        encoding="utf-8",
    )
    report = tmp_path / "report.yml"
    report.write_text(
        """
version: 1
document:
  output: build/report.docx
  toc: false
content:
  - type: figure
    caption: Terminal
    path: build/terminal.png
""",
        encoding="utf-8",
    )
    pipeline = tmp_path / "lab-compose.yml"
    pipeline.write_text(
        """
version: 1
screenshots:
  project: screenshots.yml
report:
  config: report.yml
manifest: build/manifest.json
""",
        encoding="utf-8",
    )
    return pipeline


def test_validate_pipeline(tmp_path):
    result = validate_pipeline(_fixture(tmp_path))
    assert result["screenshot_resources"][0].name == "terminal"


def test_apply_pipeline_dry_run(tmp_path):
    pipeline = _fixture(tmp_path)
    result = apply_pipeline(pipeline, dry_run=True, output_root=tmp_path / "build")
    assert result["dry_run"] is True
    assert not (tmp_path / "build" / "terminal.png").exists()


def test_apply_pipeline_writes_all_outputs_and_manifest(tmp_path):
    pipeline = _fixture(tmp_path)
    result = apply_pipeline(pipeline, output_root=tmp_path / "build")
    assert (tmp_path / "build" / "terminal.png").exists()
    assert (tmp_path / "build" / "report.docx").exists()
    manifest = json.loads((tmp_path / "build" / "manifest.json").read_text(encoding="utf-8"))
    assert result["screenshot_count"] == 1
    assert len(manifest["outputs"]) == 2


def test_pipeline_manifest_must_stay_inside_output_root(tmp_path):
    pipeline = _fixture(tmp_path)
    outside = tmp_path / "outside.json"

    with pytest.raises(ValueError, match="outside --output-root"):
        apply_pipeline(pipeline, dry_run=True, output_root=tmp_path / "build", manifest=outside)


def test_repository_example_is_valid():
    result = validate_pipeline(Path("examples/lab-compose.yml"))
    assert [resource.name for resource in result["screenshot_resources"]] == ["terminal"]


def test_report_collision_is_rejected_before_screenshot_write(tmp_path):
    pipeline = _fixture(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "report.docx").write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="use --force"):
        apply_pipeline(pipeline, output_root=build)

    assert not (build / "terminal.png").exists()
