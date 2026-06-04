# Agent Guide

Prefer `lab-compose-mcp` when an MCP client is available. Start by calling
`get_agent_guide` and `inspect_capabilities`.

For an autonomous laboratory workflow:

1. Read the assignment and inspect the workspace with `list_lab_files`,
   `read_lab_text`, and `read_lab_document` for DOCX/PDF assignments.
2. Implement the solution with `write_lab_text`.
3. Run and verify commands with `run_lab_command`. Save important output with
   `log_path` so it can be rendered as evidence.
4. Call `get_compose_schema` and `get_compose_example`, then create validated
   configs with `write_lab_config`.
5. Call `validate_lab_pipeline`, then `apply_lab_pipeline` with `dry_run=true`.
6. Run the real pipeline with an explicit `output_root`; set `force=true` only
   when replacement is intended.

File authoring tools restrict paths to the explicit `workspace_root`. Generation
tools require an explicit output root. The command tool runs without shell
parsing, but child processes inherit the MCP server process permissions.

The screenshots stage always runs before the report stage.
