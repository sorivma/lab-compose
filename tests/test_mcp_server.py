from lab_compose.mcp_server import (
    inspect_capabilities,
    validate_report,
    validate_screenshots,
)

from .test_pipeline import _fixture


def test_mcp_capabilities_are_discoverable():
    capabilities = inspect_capabilities()
    assert "figure" in capabilities["report_block_types"]
    assert "dark" in capabilities["terminal_themes"]


def test_mcp_validation_tools_delegate_to_compose_apis(tmp_path):
    pipeline = _fixture(tmp_path)
    report = validate_report(str(tmp_path / "report.yml"))
    screenshots = validate_screenshots(str(tmp_path / "screenshots.yml"))
    assert pipeline.exists()
    assert report["block_count"] == 1
    assert screenshots["resources"] == ["terminal"]
