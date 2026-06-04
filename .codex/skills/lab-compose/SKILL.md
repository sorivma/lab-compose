---
name: lab-compose
description: Run screenshot-compose and otchet-compose as one validated, agent-friendly artifact pipeline.
---

# Lab Compose

1. Discover capabilities with `lab-compose inspect --json`.
2. Validate the full pipeline with `lab-compose validate -f <pipeline> --json`.
3. Preview all writes with `lab-compose apply -f <pipeline> --dry-run --output-root <root> --json`.
4. Run with an explicit output root. Add `--force` only for intentional replacement.
5. Use `lab-compose-mcp` when the client supports MCP.
