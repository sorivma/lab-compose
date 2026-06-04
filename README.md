# lab-compose

`lab-compose` runs `screenshot-compose` and `otchet-compose` as one validated,
agent-friendly pipeline.

Install editable checkouts of `otchet-compose` and `screenshot-compose` first,
then install this project:

```powershell
python -m pip install -e ..\otchet-compose -e ..\screenshot-compose
python -m pip install -e ".[dev,mcp]"
```

```yaml
version: 1

screenshots:
  project: ./screenshots/screenshot-compose.yml
  names: [tests, app-code]

report:
  config: ./report/otchet-compose.yml

manifest: ./build/lab-compose.manifest.json
```

```powershell
lab-compose validate -f lab-compose.yml --json
lab-compose apply -f lab-compose.yml --dry-run --output-root build --json
lab-compose apply -f lab-compose.yml --force --output-root build --json
lab-compose inspect --json
lab-compose schema --json
```

## MCP Server

Install the optional official MCP Python SDK integration:

```powershell
python -m pip install -e ".[mcp]"
lab-compose-mcp
```

The stdio server exposes discovery, validation, dry-run, and generation tools
for the combined pipeline and both underlying compose formats. Write tools
require an explicit output root and default to dry-run where applicable.

## Working Example

```powershell
lab-compose validate -f examples/lab-compose.yml --json
lab-compose apply -f examples/lab-compose.yml --dry-run --output-root examples/build --json
lab-compose apply -f examples/lab-compose.yml --output-root examples/build --json
```
