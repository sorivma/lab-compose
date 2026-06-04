import asyncio

from lab_compose.mcp_server import (
    get_agent_guide,
    get_compose_schema,
    inspect_capabilities,
    mcp,
    validate_report,
    validate_screenshots,
)

from .test_pipeline import _fixture


def test_mcp_capabilities_are_discoverable():
    capabilities = inspect_capabilities()
    assert "figure" in capabilities["report_block_types"]
    assert "dark" in capabilities["terminal_themes"]
    assert capabilities["config_kinds"] == ["pipeline", "report", "screenshots"]
    assert "run_lab_command" in capabilities["recommended_workflow"][2]


def test_mcp_agent_guide_and_schemas_are_discoverable():
    guide = get_agent_guide()
    assert "validate_lab_pipeline" in guide["completion_criteria"][3]
    assert get_compose_schema("pipeline")["properties"]["version"]["const"] == 1


def test_complete_agent_tool_contract_is_registered():
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    assert {
        "get_agent_guide",
        "get_compose_schema",
        "get_compose_example",
        "list_lab_files",
        "read_lab_text",
        "read_lab_document",
        "write_lab_text",
        "write_lab_config",
        "run_lab_command",
        "validate_lab_pipeline",
        "apply_lab_pipeline",
    } <= tools.keys()
    assert tools["apply_lab_pipeline"].inputSchema["required"] == ["pipeline_path", "output_root"]


def test_mcp_validation_tools_delegate_to_compose_apis(tmp_path):
    pipeline = _fixture(tmp_path)
    report = validate_report(str(tmp_path / "report.yml"))
    screenshots = validate_screenshots(str(tmp_path / "screenshots.yml"))
    assert pipeline.exists()
    assert report["block_count"] == 1
    assert screenshots["resources"] == ["terminal"]
