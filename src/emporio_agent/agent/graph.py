"""Grafo LangGraph ReAct do agente."""

from __future__ import annotations

import time
from typing import Any, Sequence

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from emporio_agent.agent.errors import AgentError, classify_llm_error, map_exception
from emporio_agent.agent.prompts import SYSTEM_PROMPT
from emporio_agent.config import Settings, get_settings
from emporio_agent.logging_setup import get_logger
from emporio_agent.tools import ALL_TOOLS
from emporio_agent.tools.datetime_tool import format_store_clock_context

# Re-export para imports legados (`from emporio_agent.agent.graph import AgentAPIError`)
AgentAPIError = AgentError

logger = get_logger(__name__)


def build_llm(settings: Settings | None = None, llm: BaseChatModel | None = None) -> BaseChatModel:
    if llm is not None:
        return llm
    cfg = settings or get_settings()
    if not cfg.groq_api_key:
        raise AgentError(
            kind="config",
            message=(
                "Falta configuração para eu funcionar (GROQ_API_KEY). "
                "Crie um arquivo .env a partir de .env.example com a chave de "
                "https://console.groq.com — detalhes no README."
            ),
        )
    return ChatGroq(
        model=cfg.groq_model,
        temperature=cfg.llm_temperature,
        api_key=cfg.groq_api_key,
        max_retries=cfg.llm_max_retries,
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
                text = "\n".join(p for p in parts if p).strip()
                if text:
                    return text
                continue
            text = str(content).strip()
            if text:
                return text
    return "Desculpe, não consegui gerar uma resposta agora. Pode tentar de novo?"


def run_agent_turn(
    agent: Any,
    user_message: str,
    history: list[BaseMessage] | None = None,
    verbose: bool = False,
    settings: Settings | None = None,
) -> tuple[str, list[BaseMessage]]:
    """Executa um turno e devolve (resposta_texto, mensagens_atualizadas).

    Falhas conhecidas da API/modelo são mapeadas no core para `AgentError`
    com mensagem personalizada — interfaces só exibem `error.message`.
    """
    cfg = settings or get_settings()
    text = (user_message or "").strip()
    if len(text) > cfg.max_user_input_chars:
        text = text[: cfg.max_user_input_chars]

    prior = list(history or [])
    clock_ctx = SystemMessage(content=format_store_clock_context())
    inputs = {"messages": prior + [clock_ctx, HumanMessage(content=text)]}
    # recursion_limit ≈ 2 * tool rounds + margem (modelo ↔ tools)
    recursion_limit = max(8, cfg.max_tool_rounds * 2 + 4)
    invoke_config = {"recursion_limit": recursion_limit}

    last_exc: BaseException | None = None
    result = None
    attempts = max(1, cfg.llm_max_retries)
    for attempt in range(attempts):
        try:
            result = agent.invoke(inputs, config=invoke_config)
            break
        except AgentError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            kind = classify_llm_error(exc)
            logger.warning(
                "Falha no turno do agente (attempt=%s/%s kind=%s): %s",
                attempt + 1,
                attempts,
                kind,
                exc,
            )
            # Retry só para rate limit / timeout / instabilidade transitória
            if kind in {"rate_limit", "timeout", "server", "connection"} and attempt < attempts - 1:
                time.sleep(1.5 * (2**attempt))
                continue
            raise map_exception(exc) from exc

    if result is None:
        assert last_exc is not None
        raise map_exception(last_exc) from last_exc

    messages: list[BaseMessage] = result["messages"]

    if verbose:
        for msg in messages[len(prior) :]:
            role = msg.__class__.__name__
            preview = str(getattr(msg, "content", ""))[:240]
            tool_calls = getattr(msg, "tool_calls", None)
            logger.info("[%s] %s", role, preview)
            if tool_calls:
                logger.info("  tool_calls=%s", tool_calls)

    answer = _extract_final_text(messages)
    return answer, messages
