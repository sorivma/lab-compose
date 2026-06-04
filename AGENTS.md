# Agent Guide

Use `lab-compose validate --json`, then `lab-compose apply --dry-run --json`,
then run the real pipeline with an explicit `--output-root` and `--force` only
when replacement is intended.

The screenshots stage always runs before the report stage.

Use `lab-compose-mcp` when an MCP client is available. MCP write tools require
an explicit output root and pipeline/screenshot tools default to dry-run.
