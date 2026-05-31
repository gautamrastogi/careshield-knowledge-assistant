from __future__ import annotations

import argparse
import json

from careshield.app import CareShieldAssistant
from careshield.schemas import AskRequest, Role


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

    subparsers.add_parser("roles", help="List available synthetic roles")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "roles":
        print("\n".join(role.value for role in Role))
        return

    request = AskRequest(
        role=args.role,
        question=args.question,
        max_docs=args.max_docs,
    )
    response = CareShieldAssistant().ask(request)
    print(json.dumps(response.model_dump(mode="json"), indent=2))
