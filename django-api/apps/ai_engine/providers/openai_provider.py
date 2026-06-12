import os
from typing import Iterator

from openai import OpenAI

from apps.common.exceptions import LLMProviderError

from .base import ChatMessage


class OpenAIProvider:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")

    def stream(self, messages: list[ChatMessage], max_tokens: int) -> Iterator[str]:
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as e:
            raise LLMProviderError(str(e))

    def complete(self, messages: list[ChatMessage], max_tokens: int) -> tuple[str, int]:
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content or "", r.usage.total_tokens or 0
        except Exception as e:
            raise LLMProviderError(str(e))

    def complete_json(self, messages: list[ChatMessage], max_tokens: int) -> str:
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return r.choices[0].message.content or "{}"
        except Exception as e:
            raise LLMProviderError(str(e))
