#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


API_URL = "https://api.openai.com/v1/responses"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SYSTEM_PROMPT_FILE = SCRIPT_DIR / "prompts" / "system_prompt.txt"
DEFAULT_USER_PROMPT_FILE = SCRIPT_DIR / "prompts" / "user_prompt.txt"


def read_prompt_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_user_prompt(template: str, text: str) -> str:
    if "{text}" in template:
        return template.replace("{text}", text)
    return f"{template}\n\n{text}".strip()


def extract_text_from_response(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""


def parse_json_maybe_wrapped(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def call_openai(api_key: str, model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_input_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.file:
        return Path(args.file).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Judge monitored text with prompts from local .txt files.")
    parser.add_argument("--text", help="Text to analyze")
    parser.add_argument("--file", help="File path of text to analyze")
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="OpenAI model name, default from OPENAI_MODEL or gpt-4.1-mini",
    )
    parser.add_argument(
        "--system-prompt-file",
        default=str(DEFAULT_SYSTEM_PROMPT_FILE),
        help=f"System prompt txt file path (default: {DEFAULT_SYSTEM_PROMPT_FILE.name})",
    )
    parser.add_argument(
        "--user-prompt-file",
        default=str(DEFAULT_USER_PROMPT_FILE),
        help=f"User prompt txt file path (default: {DEFAULT_USER_PROMPT_FILE.name})",
    )
    args = parser.parse_args()

    input_text = get_input_text(args)
    if not input_text:
        print("Error: no input text. Use --text, --file, or pipe stdin.", file=sys.stderr)
        return 2

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Error: OPENAI_API_KEY is not set in .env.", file=sys.stderr)
        return 2

    try:
        system_prompt = read_prompt_file(Path(args.system_prompt_file))
        user_template = read_prompt_file(Path(args.user_prompt_file))
    except Exception as e:
        print(f"Error loading prompt files: {e}", file=sys.stderr)
        return 2

    user_prompt = build_user_prompt(user_template, input_text)

    try:
        response_payload = call_openai(api_key, args.model, system_prompt, user_prompt)
        model_text = extract_text_from_response(response_payload)
        result = parse_json_maybe_wrapped(model_text)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        print(f"HTTPError {e.code}: {detail}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
