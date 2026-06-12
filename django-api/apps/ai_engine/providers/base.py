from typing import Iterator, Protocol, TypedDict, Literal


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(Protocol):
    def stream(self, messages: list[ChatMessage], max_tokens: int) -> Iterator[str]: ...

    def complete(
        self, messages: list[ChatMessage], max_tokens: int
    ) -> tuple[str, int]: ...
