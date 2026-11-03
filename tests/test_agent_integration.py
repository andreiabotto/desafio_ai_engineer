"""Testes de integração do agente com LLM mockado."""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

from emporio_agent.agent.graph import build_agent, run_agent_turn


class ScriptedToolLLM(BaseChatModel):
    """LLM fake que devolve tool_calls e depois uma resposta final."""

    script: list[AIMessage]
    call_index: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted-tool-llm"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedToolLLM":
        # create_react_agent exige bind_tools; o script já define as tool_calls.
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.call_index >= len(self.script):
            msg = AIMessage(content="Resposta final padrão.")
        else:
            msg = self.script[self.call_index]
            self.call_index += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


@tool
def search_products(query: str, max_price: float | None = None, category: str | None = None) -> str:
    """Busca produtos."""
    return json.dumps(
        {
            "count": 1,
            "results": [
                {
                    "name": "Yamaha C40 Nylon Natural",
                    "price_brl": 599.9,
                    "stock_quantity": 12,
                    "status": "active",
                }
            ],
        },
        ensure_ascii=False,
    )


@tool
def search_policies(query: str) -> str:
    """Consulta políticas."""
    return "[1] (4.1 Direito de Arrependimento)\nO cliente pode solicitar a devolução em até 7 dias corridos."


@tool
def get_order_status(
    order_id: int | None = None,
    tracking_code: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> str:
    """Status de pedido."""
    return json.dumps(
        {
            "found": True,
            "orders": [
                {
                    "order_id": 1,
                    "status": "delivered",
                    "tracking_code": "BRAB1234567BR",
                    "total_brl": 11499,
                }
            ],
        },
        ensure_ascii=False,
    )


@pytest.mark.integration
def test_catalog_query_calls_search_products():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_products",
                        "args": {"query": "violão", "max_price": 1000},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="Temos o Yamaha C40 por R$ 599,90, ideal até R$ 1000."
            ),
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products, search_policies, get_order_status])
    answer, messages = run_agent_turn(
        agent, "Quais violões até R$ 1000?", history=[]
    )
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert tool_msgs
    assert "Yamaha C40" in tool_msgs[0].content or "599" in tool_msgs[0].content
    assert "599" in answer or "Yamaha" in answer


@pytest.mark.integration
def test_return_policy_calls_search_policies():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_policies",
                        "args": {"query": "arrependimento devolução"},
                        "id": "call_2",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="Sim, você pode devolver em até 7 dias pelo direito de arrependimento."
            ),
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products, search_policies, get_order_status])
    answer, messages = run_agent_turn(
        agent, "Me arrependi da compra, posso devolver?", history=[]
    )
    assert any(isinstance(m, ToolMessage) for m in messages)
    assert "7" in answer


@pytest.mark.integration
def test_order_status_calls_get_order_status():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_order_status",
                        "args": {"order_id": 1},
                        "id": "call_3",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Seu pedido 1 está como delivered, tracking BRAB1234567BR."),
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products, search_policies, get_order_status])
    answer, messages = run_agent_turn(agent, "Status do pedido 1?", history=[])
    assert any(isinstance(m, ToolMessage) for m in messages)
    assert "delivered" in answer.lower() or "BRAB" in answer


@pytest.mark.integration
def test_accessory_out_of_scope_no_fake_product():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content=(
                    "A Empório trabalha só com instrumentos musicais. "
                    "Não vendemos cordas avulsas nem pedais — recomendo uma loja de acessórios."
                )
            )
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products, search_policies, get_order_status])
    answer, messages = run_agent_turn(
        agent, "Vocês vendem cordas e pedais de guitarra?", history=[]
    )
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert not tool_msgs
    assert "instrumento" in answer.lower() or "não vendemos" in answer.lower() or "acessório" in answer.lower()
