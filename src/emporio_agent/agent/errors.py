"""Erros do agente mapeados no core (mensagens amigáveis para o cliente)."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from groq import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        InternalServerError,
        PermissionDeniedError,
        RateLimitError,
    )
except ImportError:  # pragma: no cover - groq sempre presente em runtime
    RateLimitError = AuthenticationError = APITimeoutError = APIConnectionError = ()  # type: ignore[misc, assignment]
    BadRequestError = InternalServerError = PermissionDeniedError = ()  # type: ignore[misc, assignment]


# kind → resposta personalizada (tom do assistente)
USER_MESSAGES: dict[str, str] = {
    "rate_limit": (
        "Estou com muita demanda agora 🎸 Aguarde alguns segundos e tente de novo. "
        "Se continuar, use /nova (ou “Nova conversa”) para limpar o histórico e reduzir o uso de tokens."
    ),
    "auth": (
        "Não consegui autenticar na API do modelo. "
        "Quem opera a demo precisa conferir a GROQ_API_KEY no arquivo .env."
    ),
    "timeout": (
        "A consulta ao modelo demorou demais e eu precisei interromper. "
        "Pode tentar de novo em instantes?"
    ),
    "connection": (
        "Tive um problema de conexão com o serviço do modelo. "
        "Verifique a rede e tente novamente em alguns segundos."
    ),
    "context": (
        "Nossa conversa ficou longa demais para o modelo. "
        "Inicie uma nova conversa (/nova) e reformule a pergunta de forma mais curta."
    ),
    "bad_request": (
        "A requisição ao modelo foi rejeitada. "
        "Tente reformular a mensagem; se persistir, confira o modelo configurado (GROQ_MODEL)."
    ),
    "server": (
        "O serviço do modelo está instável no momento. "
        "Aguarde um pouco e tente de novo; se for recorrente, troque temporariamente o GROQ_MODEL (ver README)."
    ),
    "recursion": (
        "Precisei de muitas etapas internas para responder e parei por segurança. "
        "Tente uma pergunta mais direta ou inicie uma nova conversa."
    ),
    "config": (
        "Falta configuração para eu funcionar (por exemplo GROQ_API_KEY). "
        "Use o .env.example como base — detalhes no README."
    ),
    "unknown": (
        "Não consegui responder agora. "
        "Tente de novo em instantes ou inicie uma nova conversa. "
        "Se persistir, confira os logs (LOG_LEVEL=DEBUG) e o README na seção de erros conhecidos."
    ),
}


@dataclass
class AgentError(Exception):
    """Erro conhecido do agente: `kind` técnico + `message` amigável ao usuário."""

    kind: str
    message: str

    def __str__(self) -> str:
        return self.message


# Compatibilidade com imports antigos
AgentAPIError = AgentError


def _iter_exception_chain(exc: BaseException):
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        yield cur
        seen.add(id(cur))
        cur = cur.__cause__ or cur.__context__


def _kind_from_type(exc: BaseException) -> str | None:
    if RateLimitError and isinstance(exc, RateLimitError):
        return "rate_limit"
    if AuthenticationError and isinstance(exc, AuthenticationError):
        return "auth"
    if PermissionDeniedError and isinstance(exc, PermissionDeniedError):
        return "auth"
    if APITimeoutError and isinstance(exc, APITimeoutError):
        return "timeout"
    if APIConnectionError and isinstance(exc, APIConnectionError):
        return "connection"
    if BadRequestError and isinstance(exc, BadRequestError):
        text = str(exc).lower()
        if any(x in text for x in ("context", "token", "maximum")):
            return "context"
        return "bad_request"
    if InternalServerError and isinstance(exc, InternalServerError):
        return "server"

    name = type(exc).__name__
    if name in {"GraphRecursionError", "RecursionError"}:
        return "recursion"
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return "auth"
    if name in {"RateLimitError"}:
        return "rate_limit"
    if name in {"APITimeoutError", "TimeoutError"}:
        return "timeout"
    if name in {"APIConnectionError"}:
        return "connection"
    if isinstance(exc, ValueError) and "GROQ_API_KEY" in str(exc):
        return "config"
    return None


def _kind_from_text(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(x in text for x in ("429", "rate limit", "rate_limit", "tpm", "too many requests")):
        return "rate_limit"
    if any(x in text for x in ("401", "403", "invalid api", "authentication", "unauthorized", "permission denied")):
        return "auth"
    if any(x in text for x in ("timeout", "timed out", "deadline")):
        return "timeout"
    if any(x in text for x in ("connection", "connecterror", "network")):
        return "connection"
    if any(x in text for x in ("context length", "maximum context", "token limit", "too many tokens")):
        return "context"
    if any(x in text for x in ("recursion", "recursion_limit")):
        return "recursion"
    if "groq_api_key" in text:
        return "config"
    if "500" in text or "internal server" in text:
        return "server"
    if any(x in text for x in ("400", "bad request", "invalid_request")):
        return "bad_request"
    return "unknown"


def classify_llm_error(exc: BaseException) -> str:
    """Classifica a exceção em um `kind` estável."""
    if isinstance(exc, AgentError):
        return exc.kind
    for link in _iter_exception_chain(exc):
        kind = _kind_from_type(link)
        if kind:
            return kind
    return _kind_from_text(exc)


def map_exception(exc: BaseException) -> AgentError:
    """Converte qualquer falha em `AgentError` com mensagem personalizada."""
    if isinstance(exc, AgentError):
        return exc
    kind = classify_llm_error(exc)
    message = USER_MESSAGES.get(kind, USER_MESSAGES["unknown"])
    return AgentError(kind=kind, message=message)
