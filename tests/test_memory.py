import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from emporio_agent.agent.memory import ConversationMemory, compact_messages_for_history


@pytest.mark.unit
def test_compact_keeps_tool_fact_summary():
    messages = [
        HumanMessage(content="preço do takamine"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_product_by_name",
                    "args": {"name": "Takamine"},
                    "id": "c1",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(content='{"price_brl": 2199}', tool_call_id="c1", name="get_product_by_name"),
        AIMessage(content="O Takamine custa R$ 2199."),
        HumanMessage(content="e o frete?"),
        AIMessage(content="Frete grátis acima de R$ 500."),
    ]
    compact = compact_messages_for_history(messages, max_messages=12)
    assert any(isinstance(m, SystemMessage) for m in compact)
    assert any(isinstance(m, HumanMessage) for m in compact)
    assert not any(isinstance(m, ToolMessage) for m in compact)
    facts = next(m for m in compact if isinstance(m, SystemMessage))
    assert "2199" in facts.content
    assert compact[-1].content.startswith("Frete")


@pytest.mark.unit
def test_compact_respects_max_messages():
    messages = []
    for i in range(10):
        messages.append(HumanMessage(content=f"u{i}"))
        messages.append(AIMessage(content=f"a{i}"))
    compact = compact_messages_for_history(messages, max_messages=4)
    assert len(compact) == 4
    assert compact[0].content == "u8"


@pytest.mark.unit
def test_memory_replace_from_turn():
    memory = ConversationMemory(max_messages=6)
    memory.replace_from_turn(
        [
            HumanMessage(content="oi"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_policies",
                        "args": {},
                        "id": "x",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(content="politica longa " * 50, tool_call_id="x", name="search_policies"),
            AIMessage(content="Horário 9 às 18."),
        ]
    )
    msgs = memory.as_list()
    assert any(isinstance(m, SystemMessage) for m in msgs)
    assert msgs[-1].content == "Horário 9 às 18."
    assert any(isinstance(m, HumanMessage) and m.content == "oi" for m in msgs)
