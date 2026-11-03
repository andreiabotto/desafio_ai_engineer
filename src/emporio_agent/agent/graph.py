"""Grafo LangGraph ReAct do agente."""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from emporio_agent.agent.prompts import SYSTEM_PROMPT
from emporio_agent.config import Settings, get_settings
from emporio_agent.tools import ALL_TOOLS


def build_llm(settings: Settings | None = None, llm: BaseChatModel | None = None) -> BaseChatModel:
    if llm is not None:
        return llm
    cfg = settings or get_settings()
    if not cfg.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY não configurada. Crie um arquivo .env a partir de .env.example "
            "com sua chave gratuita de https://console.groq.com"
        )
    return ChatGroq(
        model=cfg.groq_model,
        temperature=cfg.llm_temperature,
        api_key=cfg.groq_api_key,
    )


def build_agent(
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
    tools: Sequence | None = None,
):
    model = build_llm(settings=settings, llm=llm)
    return create_agent(
        model,
        tools=list(tools) if tools is not None else ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def _extract_final_text(messages: Sequence[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            content = msg.content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        parts.append(block)
                return "\n".join(p for p in parts if p).strip()
            return str(content).strip()
    return "Desculpe, não consegui gerar uma resposta agora. Pode tentar de novo?"


def run_agent_turn(
    agent: Any,
    user_message: str,
    history: list[BaseMessage] | None = None,
    verbose: bool = False,
) -> tuple[str, list[BaseMessage]]:
    """Executa um turno e devolve (resposta_texto, mensagens_atualizadas)."""
    prior = list(history or [])
    inputs = {"messages": prior + [HumanMessage(content=user_message)]}
    result = agent.invoke(inputs)
    messages: list[BaseMessage] = result["messages"]

    if verbose:
        for msg in messages[len(prior) :]:
            role = msg.__class__.__name__
            preview = str(getattr(msg, "content", ""))[:240]
            tool_calls = getattr(msg, "tool_calls", None)
            print(f"[{role}] {preview}")
            if tool_calls:
                print(f"  tool_calls={tool_calls}")

    # Histórico persistido: human + última AI final (sem tool spam excessivo)
    # Mantemos o trace completo do grafo para continuidade correta do LangGraph.
    answer = _extract_final_text(messages)
    return answer, messages


def bootstrap_messages() -> list[BaseMessage]:
    return [SystemMessage(content=SYSTEM_PROMPT)]
