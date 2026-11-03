import pytest

from emporio_agent.agent.graph import AgentAPIError, classify_llm_error


@pytest.mark.unit
def test_classify_rate_limit():
    assert classify_llm_error(RuntimeError("Error 429 rate_limit exceeded")) == "rate_limit"


@pytest.mark.unit
def test_classify_auth():
    assert classify_llm_error(RuntimeError("401 Unauthorized invalid api key")) == "auth"


@pytest.mark.unit
def test_agent_api_error_kind():
    err = AgentAPIError("boom", kind="timeout")
    assert err.kind == "timeout"
    assert "boom" in str(err)
