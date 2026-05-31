import argparse
import json
import pathlib

import careshield.contracts.schemas as schemas
import careshield.pipeline.assistant as assistant_service


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    :return: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="careshield",
        description="Synthetic governed GenAI/RAG healthcare knowledge assistant demo.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser(name="ask", help="Ask a policy question")
    ask.add_argument("--role", choices=[role.value for role in schemas.Role], required=True)
    ask.add_argument("--question", required=True)
    ask.add_argument("--max-docs", type=int, default=3)

    analyze = subparsers.add_parser(
        name="analyze-doc",
        help="Parse, embed, retrieve, and analyze a local document",
    )
    analyze.add_argument("--file", required=True)
    analyze.add_argument(
        "--role",
        choices=[role.value for role in schemas.Role],
        default=schemas.Role.compliance_officer.value,
    )
    analyze.add_argument("--question", required=True)
    analyze.add_argument(
        "--sensitivity",
        choices=[item.value for item in schemas.Sensitivity],
        default=schemas.Sensitivity.clinical.value,
    )
    analyze.add_argument("--max-docs", type=int, default=3)

    subparsers.add_parser(name="roles", help="List available synthetic roles")
    return parser


def main() -> None:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "roles":
        print("\n".join(role.value for role in schemas.Role))
        return

    assistant = assistant_service.CareShieldAssistant()
    if args.command == "analyze-doc":
        path = pathlib.Path(args.file)
        response = assistant.analyze_document(
            content=path.read_bytes(),
            source_name=path.name,
            role=schemas.Role(args.role),
            question=args.question,
            sensitivity=schemas.Sensitivity(args.sensitivity),
            max_docs=args.max_docs,
        )
        print(json.dumps(obj=response.model_dump(mode="json"), indent=2))
        return

    request = schemas.AskRequest(
        role=schemas.Role(args.role),
        question=args.question,
        max_docs=args.max_docs,
    )
    response = assistant.ask(request=request)
    print(json.dumps(obj=response.model_dump(mode="json"), indent=2))
