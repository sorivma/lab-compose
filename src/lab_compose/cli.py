"""Command-line interface for lab-compose."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .cli_output import error_payload, print_json, success_payload
from .pipeline import apply_pipeline, validate_pipeline
from .schemas import load_schema


class MachineArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "--json" in sys.argv[1:]:
            command = next((arg for arg in sys.argv[1:] if not arg.startswith("-")), "cli")
            print_json(error_payload(command, "invalid_arguments", message), error=True)
            self.exit(2)
        super().error(message)


def validate_command(args) -> int:
    result = validate_pipeline(args.file)
    data = {
        "pipeline": str(Path(args.file).resolve()),
        "screenshot_resources": [resource.name for resource in result["screenshot_resources"]],
        "report_output": result["report_config"]["document"]["output"],
    }
    _success("validate", args.json, data=data)
    return 0


def apply_command(args) -> int:
    result = apply_pipeline(
        args.file,
        dry_run=args.dry_run,
        force=args.force,
        output_root=args.output_root,
        manifest=args.manifest,
    )
    warnings = [{"code": "generation_warning", "message": message} for message in result["warnings"]]
    _success(
        "apply",
        args.json,
        outputs=result["outputs"],
        warnings=warnings,
        data={
            "pipeline": str(Path(args.file).resolve()),
            "dry_run": result["dry_run"],
            "screenshot_count": result["screenshot_count"],
            "manifest": str(result["manifest"]) if result["manifest"] else None,
        },
    )
    return 0


def inspect_command(args) -> int:
    data = {"pipeline_version": 1, "stages": ["screenshots", "report"], "schema_command": "lab-compose schema --json"}
    _success("inspect", args.json, data=data)
    return 0


def schema_command(args) -> int:
    schema = load_schema(args.version)
    if args.json:
        print_json(success_payload("schema", data={"version": args.version, "schema": schema}))
    else:
        print_json(schema)
    return 0


def _success(command: str, as_json: bool, *, outputs=None, data=None, warnings=None) -> None:
    if as_json:
        print_json(success_payload(command, outputs=outputs, data=data, warnings=warnings))
    else:
        print(f"{command} successful")


def build_parser() -> argparse.ArgumentParser:
    parser = MachineArgumentParser(prog="lab-compose", description="Run screenshot and report generation as one pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate the complete pipeline")
    validate.add_argument("-f", "--file", default="lab-compose.yml")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=validate_command)

    apply = subparsers.add_parser("apply", help="Run the complete pipeline")
    apply.add_argument("-f", "--file", default="lab-compose.yml")
    apply.add_argument("--dry-run", action="store_true")
    apply.add_argument("--force", action="store_true")
    apply.add_argument("--output-root")
    apply.add_argument("--manifest")
    apply.add_argument("--json", action="store_true")
    apply.set_defaults(func=apply_command)

    inspect = subparsers.add_parser("inspect", help="Describe pipeline capabilities")
    inspect.add_argument("--json", action="store_true")
    inspect.set_defaults(func=inspect_command)

    schema = subparsers.add_parser("schema", help="Print the pipeline JSON Schema")
    schema.add_argument("--version", type=int, default=1)
    schema.add_argument("--json", action="store_true")
    schema.set_defaults(func=schema_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        if getattr(args, "json", False):
            print_json(error_payload(args.command, "invalid_input", str(exc)), error=True)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if getattr(args, "json", False):
            print_json(error_payload(args.command, "internal_error", str(exc)), error=True)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
