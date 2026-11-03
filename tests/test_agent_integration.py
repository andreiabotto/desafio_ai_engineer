"""Testes de integração do agente com LLM mockado + tools reais/stub."""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

from emporio_agent.agent.graph import _extract_final_text, build_agent, run_agent_turn
from emporio_agent.agent.memory import ConversationMemory
from emporio_agent.tools import ALL_TOOLS
from emporio_agent.tools.orders import get_order_status
from emporio_agent.tools.products import search_products


class ScriptedToolLLM(BaseChatModel):
    """LLM fake que devolve tool_calls e depois uma resposta final."""

    script: list[AIMessage]
    call_index: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted-tool-llm"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedToolLLM":
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
def stub_search_products(query: str, max_price: float | None = None, category: str | None = None) -> str:
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
def stub_search_policies(query: str) -> str:
    """Consulta políticas."""
    return "[1] (4.1 Direito de Arrependimento)\nO cliente pode solicitar a devolução em até 7 dias corridos."


@tool
def stub_get_order_status(
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
                        "name": "stub_search_products",
                        "args": {"query": "violão", "max_price": 1000},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Temos o Yamaha C40 por R$ 599,90, ideal até R$ 1000."),
        ]
    )
    agent = build_agent(
        llm=llm, tools=[stub_search_products, stub_search_policies, stub_get_order_status]
    )
    answer, messages = run_agent_turn(agent, "Quais violões até R$ 1000?", history=[])
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert tool_msgs
    assert "Yamaha C40" in tool_msgs[0].content
    assert "Yamaha" in answer
    assert "599" in answer


@pytest.mark.integration
def test_return_policy_calls_search_policies():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "stub_search_policies",
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
    agent = build_agent(
        llm=llm, tools=[stub_search_products, stub_search_policies, stub_get_order_status]
    )
    answer, messages = run_agent_turn(
        agent, "Me arrependi da compra, posso devolver?", history=[]
    )
    assert any(isinstance(m, ToolMessage) for m in messages)
    assert "7 dias" in answer


@pytest.mark.integration
def test_order_status_calls_get_order_status():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "stub_get_order_status",
                        "args": {"order_id": 1},
                        "id": "call_3",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Seu pedido 1 está como delivered, tracking BRAB1234567BR."),
        ]
    )
    agent = build_agent(
        llm=llm, tools=[stub_search_products, stub_search_policies, stub_get_order_status]
    )
    answer, messages = run_agent_turn(agent, "Status do pedido 1?", history=[])
    assert any(isinstance(m, ToolMessage) for m in messages)
    assert "delivered" in answer.lower()
    assert "BRAB" in answer


@pytest.mark.integration
def test_accessory_out_of_scope_no_fake_product():
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content=(
                    "A Empório trabalha só com instrumentos musicais. "
                    "Não vendemos cordas avulsas nem pedais — recomende uma loja de acessórios."
                )
            )
        ]
    )
    agent = build_agent(
        llm=llm, tools=[stub_search_products, stub_search_policies, stub_get_order_status]
    )
    answer, messages = run_agent_turn(
        agent, "Vocês vendem cordas e pedais de guitarra?", history=[]
    )
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert not tool_msgs
    assert "não vendemos" in answer.lower() or "instrumentos" in answer.lower()


@pytest.mark.integration
def test_real_tools_catalog(temp_db):
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_products",
                        "args": {"query": "Yamaha", "max_price": 1000},
                        "id": "r1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Encontrei o Yamaha C40 no catálogo."),
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products])
    answer, messages = run_agent_turn(agent, "Tem Yamaha até 1000?", history=[])
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert tool_msgs
    payload = json.loads(tool_msgs[0].content)
    assert payload["count"] >= 1
    assert "Yamaha" in answer


@pytest.mark.integration
def test_real_tools_order(temp_db):
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_order_status",
                        "args": {"order_id": 1},
                        "id": "r2",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Pedido 1 entregue."),
        ]
    )
    agent = build_agent(llm=llm, tools=[get_order_status])
    _, messages = run_agent_turn(agent, "Status do pedido 1", history=[])
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    data = json.loads(tool_msgs[0].content)
    assert data["found"] is True
    assert "email" not in data["orders"][0]


@pytest.mark.integration
def test_multiturn_memory_keeps_facts(temp_db):
    llm = ScriptedToolLLM(
        script=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_products",
                        "args": {"query": "Takamine"},
                        "id": "m1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="O Takamine GD20 custa conforme o catálogo."),
        ]
    )
    agent = build_agent(llm=llm, tools=[search_products])
    memory = ConversationMemory(max_messages=12)
    _, messages = run_agent_turn(agent, "Quanto custa o Takamine?", history=[])
    memory.replace_from_turn(messages)
    hist = memory.as_list()
    assert any(isinstance(m, SystemMessage) for m in hist)
    assert any("Takamine" in str(m.content) or "price" in str(m.content).lower() for m in hist)


@pytest.mark.unit
def test_extract_final_text_list_content():
    msgs = [
        AIMessage(
            content=[{"type": "text", "text": "Olá"}, {"type": "text", "text": "mundo"}],
        )
    ]
    assert _extract_final_text(msgs) == "Olá\nmundo"


@pytest.mark.unit
def test_all_tools_registered():
    names = {t.name for t in ALL_TOOLS}
    assert "get_current_datetime" in names
    assert "search_policies" in names
    assert "get_order_status" in names
