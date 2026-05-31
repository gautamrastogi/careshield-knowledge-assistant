from __future__ import annotations

import argparse
import json
from pathlib import Path

from careshield.app import CareShieldAssistant
from careshield.schemas import AskRequest, Role, Sensitivity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="careshield",
        description="Synthetic governed GenAI/RAG healthcare knowledge assistant demo.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Ask a policy question")
    ask.add_argument("--role", choices=[role.value for role in Role], required=True)
    ask.add_argument("--question", required=True)
    ask.add_argument("--max-docs", type=int, default=3)

    analyze = subparsers.add_parser("analyze-doc", help="Parse, embed, retrieve, and analyze a local document")
    analyze.add_argument("--file", required=True)
    analyze.add_argument("--role", choices=[role.value for role in Role], default=Role.compliance_officer.value)
    analyze.add_argument("--question", required=True)
    analyze.add_argument("--sensitivity", choices=[item.value for item in Sensitivity], default=Sensitivity.clinical.value)
    analyze.add_argument("--max-docs", type=int, default=3)

    subparsers.add_parser("roles", help="List available synthetic roles")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "roles":
        print("\n".join(role.value for role in Role))
        return

    assistant = CareShieldAssistant()
    if args.command == "analyze-doc":
        path = Path(args.file)
        response = assistant.analyze_document(
            content=path.read_bytes(),
            source_name=path.name,
            role=Role(args.role),
            question=args.question,
            sensitivity=Sensitivity(args.sensitivity),
            max_docs=args.max_docs,
        )
        print(json.dumps(response.model_dump(mode="json"), indent=2))
        return

    request = AskRequest(role=args.role, question=args.question, max_docs=args.max_docs)
    response = assistant.ask(request)
    print(json.dumps(response.model_dump(mode="json"), indent=2))
