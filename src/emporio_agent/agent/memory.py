"""Histórico simples de conversa por sessão."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage


def _content_as_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(p for p in parts if p)
    return str(content) if content is not None else ""


def _summarize_tool_facts(messages: Sequence[BaseMessage], *, max_chars: int = 1200) -> str | None:
    """Extrai um resumo compacto dos ToolMessages do último turno para o próximo contexto."""
    facts: list[str] = []
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        name = getattr(msg, "name", None) or "tool"
        raw = _content_as_text(msg.content).strip()
        if not raw:
            continue
        snippet = raw
        try:
            parsed = json.loads(raw)
            snippet = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        except (json.JSONDecodeError, TypeError):
            snippet = raw.replace("\n", " ")
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        facts.append(f"- {name}: {snippet}")
    if not facts:
        return None
    body = "Fatos das tools (reconsultar se precisar de números exatos):\n" + "\n".join(facts)
    if len(body) > max_chars:
        body = body[: max_chars - 1] + "…"
    return body


def _align_window_start(kept: list[BaseMessage]) -> list[BaseMessage]:
    """Evita começar o histórico no meio de um turno (ex.: AI sem Human anterior)."""
    while kept and not isinstance(kept[0], HumanMessage):
        # SystemMessage de fatos no início é ok se seguido de diálogo
        if isinstance(kept[0], SystemMessage) and len(kept) > 1:
            break
        kept = kept[1:]
    return kept


def compact_messages_for_history(
    messages: Sequence[BaseMessage],
    *,
    max_messages: int = 12,
) -> list[BaseMessage]:
    """Remove traces brutos de tools, retém fatos resumidos e limita turnos (TPM Groq)."""
    tool_facts = _summarize_tool_facts(messages)
    kept: list[BaseMessage] = []
    if tool_facts:
        kept.append(SystemMessage(content=tool_facts))

    for msg in messages:
        if isinstance(msg, HumanMessage):
            kept.append(HumanMessage(content=_content_as_text(msg.content)))
            continue
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            text = _content_as_text(msg.content).strip()
            if text and not tool_calls:
                kept.append(AIMessage(content=text))

    if max_messages > 0 and len(kept) > max_messages:
        # Preserva o bloco de fatos (primeiro SystemMessage) quando existir
        if kept and isinstance(kept[0], SystemMessage):
            tail = kept[1:]
            budget = max(1, max_messages - 1)
            kept = [kept[0]] + tail[-budget:]
        else:
            kept = kept[-max_messages:]
        kept = _align_window_start(kept)
    return kept


@dataclass
class ConversationMemory:
    session_id: str = "default"
    messages: list[BaseMessage] = field(default_factory=list)
    max_messages: int = 12

    def add_user(self, text: str) -> None:
        self.messages.append(HumanMessage(content=text))

    def add_ai(self, text: str) -> None:
        self.messages.append(AIMessage(content=text))

    def replace_from_turn(self, messages: Sequence[BaseMessage]) -> None:
        self.messages = compact_messages_for_history(
            messages, max_messages=self.max_messages
        )

    def clear(self) -> None:
        self.messages.clear()

    def as_list(self) -> list[BaseMessage]:
        return list(self.messages)
