import pytest
from groq import AuthenticationError, RateLimitError

from emporio_agent.agent.errors import AgentError, USER_MESSAGES, classify_llm_error, map_exception
from emporio_agent.agent.graph import AgentAPIError


class _FakeRateLimit(RateLimitError):
    def __init__(self, message: str = "rate limited") -> None:
        Exception.__init__(self, message)


class _FakeAuth(AuthenticationError):
    def __init__(self, message: str = "unauthorized") -> None:
        Exception.__init__(self, message)


@pytest.mark.unit
def test_classify_rate_limit_by_text():
    assert classify_llm_error(RuntimeError("Error 429 rate_limit exceeded")) == "rate_limit"


@pytest.mark.unit
def test_classify_auth_by_text():
    assert classify_llm_error(RuntimeError("401 Unauthorized invalid api key")) == "auth"


@pytest.mark.unit
def test_classify_groq_rate_limit_type():
    assert classify_llm_error(_FakeRateLimit()) == "rate_limit"


@pytest.mark.unit
def test_classify_groq_auth_type():
    assert classify_llm_error(_FakeAuth()) == "auth"


@pytest.mark.unit
def test_classify_wrapped_cause():
    wrapped = RuntimeError("llm failed")
    wrapped.__cause__ = _FakeRateLimit()
    assert classify_llm_error(wrapped) == "rate_limit"


@pytest.mark.unit
def test_map_exception_personalized_message():
    err = map_exception(RuntimeError("429 too many requests / rate_limit"))
    assert isinstance(err, AgentError)
    assert err.kind == "rate_limit"
    assert err.message == USER_MESSAGES["rate_limit"]
    assert "aguarde" in err.message.lower()


@pytest.mark.unit
def test_map_exception_auth_message():
    err = map_exception(RuntimeError("401 authentication failed"))
    assert err.kind == "auth"
    assert err.message == USER_MESSAGES["auth"]


@pytest.mark.unit
def test_agent_error_alias():
    err = AgentAPIError(kind="timeout", message="demorou")
    assert err.kind == "timeout"
    assert str(err) == "demorou"


@pytest.mark.unit
def test_map_preserves_agent_error():
    original = AgentError(kind="context", message="custom")
    assert map_exception(original) is original
