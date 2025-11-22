import enum
from dataclasses import dataclass
from typing import Protocol, TypedDict

import anthropic

from llm_ffi.config import LLMApiSettings


class MessageSource(enum.StrEnum):
    user = "user"
    assistant = "assistant"


class MessageDict(TypedDict):
    role: str
    content: str


@dataclass
class Message:
    role: MessageSource
    content: str

    def to_dict(self) -> MessageDict:
        return {"role": str(self.role), "content": self.content}


class LLMInterface(Protocol):
    def infer(
        self, system_prompt: str, history: list[Message], user_prompt: str
    ) -> str: ...

    def model_name(self) -> str: ...


@dataclass
class LLMExternalInference:
    _api_key: str
    model: str

    @classmethod
    def from_config(cls, model_name: str) -> LLMInterface:
        settings = LLMApiSettings()  # type: ignore
        # TODO: Handle config load failure here.
        if model_name.startswith("claude"):
            return AnthropicInference(settings, model_name)
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"LLMExternalInference(model={self.model})"


def format_messages(history: list[Message], user_prompt: str) -> list[MessageDict]:
    messages: list[MessageDict] = []
    for message in history:
        messages.append(message.to_dict())
    messages.append({"role": str(MessageSource.user), "content": user_prompt})
    return messages


class AnthropicInference(LLMInterface):
    def __init__(self, settings: LLMApiSettings, model_name: str) -> None:
        self.client = anthropic.Anthropic(api_key=settings.api_key)
        self.model = model_name
        self.max_tokens = settings.max_tokens

    def infer(
        self, system_prompt: str, history: list[Message], user_prompt: str
    ) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=format_messages(history, user_prompt),  # type: ignore
        )
        return response.content[0].text.strip()

    def model_name(self) -> str:
        return self.model
