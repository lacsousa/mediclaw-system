import os
from typing import Iterator

from google import genai
from google.genai import types

from apps.common.exceptions import LLMProviderError

from .base import ChatMessage


class GeminiProvider:
    def __init__(self):
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.model_name = os.environ.get("CHAT_MODEL", "gemini-2.0-flash")

    def _build(self, messages: list[ChatMessage]) -> tuple[str, list[types.Content]]:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        contents: list[types.Content] = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            if contents and contents[-1].role == role:
                prev = contents[-1].parts[0].text if contents[-1].parts else ""
                contents[-1] = types.Content(
                    role=role,
                    parts=[types.Part(text=f"{prev}\n\n{m['content']}")],
                )
            else:
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=m["content"])])
                )
        return system, contents

    def _config(self, system: str, max_tokens: int) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system or None,
            max_output_tokens=max_tokens,
        )

    def stream(self, messages: list[ChatMessage], max_tokens: int) -> Iterator[str]:
        system, contents = self._build(messages)
        try:
            for chunk in self._client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=self._config(system, max_tokens),
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise LLMProviderError(str(e)) from e

    def complete(self, messages: list[ChatMessage], max_tokens: int) -> tuple[str, int]:
        system, contents = self._build(messages)
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self._config(system, max_tokens),
            )
            usage = response.usage_metadata
            tokens = (usage.total_token_count or 0) if usage else 0
            return response.text or "", tokens
        except Exception as e:
            raise LLMProviderError(str(e)) from e

    def complete_json(self, messages: list[ChatMessage], max_tokens: int) -> str:
        system, contents = self._build(messages)
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                ),
            )
            return response.text or "{}"
        except Exception as e:
            raise LLMProviderError(str(e)) from e
