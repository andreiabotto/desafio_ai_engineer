"""Histórico simples de conversa por sessão."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


@dataclass
class ConversationMemory:
    session_id: str = "default"
    messages: list[BaseMessage] = field(default_factory=list)

    def add_user(self, text: str) -> None:
        self.messages.append(HumanMessage(content=text))

    def add_ai(self, text: str) -> None:
        self.messages.append(AIMessage(content=text))

    def clear(self) -> None:
        self.messages.clear()

    def as_list(self) -> list[BaseMessage]:
        return list(self.messages)