from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from dotenv import load_dotenv


load_dotenv()


class LLMUnavailableError(RuntimeError):
    pass


def generate_text(
    prompt: str,
    system_prompt: str,
    max_output_tokens: int = 700,
    provider: Optional[str] = None,
) -> str:
    selected_provider = _normalize_provider(provider)
    if selected_provider == "groq":
        return _generate_text_with_groq(
            prompt=prompt,
            system_prompt=system_prompt,
            max_output_tokens=max_output_tokens,
        )

    return _generate_text_with_openai(
        prompt=prompt,
        system_prompt=system_prompt,
        max_output_tokens=max_output_tokens,
    )


def generate_json(
    prompt: str,
    system_prompt: str,
    max_output_tokens: int = 1200,
    provider: Optional[str] = None,
) -> dict[str, Any]:
    selected_provider = _normalize_provider(provider)
    if selected_provider == "groq":
        output_text = _generate_text_with_groq(
            prompt=f"{prompt}\n\nReturn valid JSON only. Do not include markdown fences.",
            system_prompt=system_prompt,
            max_output_tokens=max_output_tokens,
            response_format={"type": "json_object"},
        )
        return _parse_json_output(output_text)

    output_text = _generate_json_text_with_openai(
        prompt=prompt,
        system_prompt=system_prompt,
        max_output_tokens=max_output_tokens,
    )
    return _parse_json_output(output_text)


def _normalize_provider(provider: Optional[str]) -> str:
    return (provider or os.getenv("LLM_PROVIDER") or "openai").lower().strip()


def _generate_text_with_openai(
    prompt: str,
    system_prompt: str,
    max_output_tokens: int,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailableError("OPENAI_API_KEY is not configured.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("OpenAI SDK is not installed.") from exc

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:
        raise LLMUnavailableError(str(exc)) from exc

    output_text: Optional[str] = getattr(response, "output_text", None)
    if not output_text:
        raise LLMUnavailableError("LLM returned an empty response.")

    return output_text.strip()


def _generate_json_text_with_openai(
    prompt: str,
    system_prompt: str,
    max_output_tokens: int,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailableError("OPENAI_API_KEY is not configured.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("OpenAI SDK is not installed.") from exc

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=prompt,
            max_output_tokens=max_output_tokens,
            text={"format": {"type": "json_object"}},
        )
    except Exception as exc:
        raise LLMUnavailableError(str(exc)) from exc

    output_text: Optional[str] = getattr(response, "output_text", None)
    if not output_text:
        raise LLMUnavailableError("LLM returned an empty JSON response.")

    return output_text.strip()


def _generate_text_with_groq(
    prompt: str,
    system_prompt: str,
    max_output_tokens: int,
    response_format: Optional[dict[str, str]] = None,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMUnavailableError("GROQ_API_KEY is not configured.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("OpenAI SDK is not installed.") from exc

    model = "openai/gpt-oss-20b"
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.2,
    }
    if response_format:
        request_kwargs["response_format"] = response_format

    try:
        response = client.chat.completions.create(**request_kwargs)
    except Exception as exc:
        raise LLMUnavailableError(str(exc)) from exc

    output_text = response.choices[0].message.content if response.choices else None
    if not output_text:
        raise LLMUnavailableError("Groq returned an empty response.")

    return output_text.strip()


def _parse_json_output(output_text: str) -> dict[str, Any]:
    cleaned = output_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMUnavailableError("LLM returned invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise LLMUnavailableError("LLM JSON response must be an object.")

    return parsed
