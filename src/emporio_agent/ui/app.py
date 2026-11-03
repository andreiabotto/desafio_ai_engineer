"""Chat web do Empório da Música (Streamlit)."""

from __future__ import annotations

import streamlit as st

from emporio_agent.agent.graph import AgentAPIError, run_agent_turn
from emporio_agent.agent.memory import ConversationMemory
from emporio_agent.bootstrap import bootstrap_agent
from emporio_agent.config import get_settings


def _friendly_error(exc: BaseException) -> str:
    kind = getattr(exc, "kind", "unknown") if isinstance(exc, AgentAPIError) else "unknown"
    if kind == "rate_limit":
        return (
            "Não consegui responder agora (rate limit do Groq). "
            "Aguarde alguns segundos ou inicie uma nova conversa."
        )
    if kind == "auth":
        return "Falha de autenticação na API. Verifique a GROQ_API_KEY no `.env`."
    if kind == "context":
        return "A conversa ficou longa demais para o modelo. Inicie uma nova conversa."
    return "Não consegui responder agora. Tente de novo em instantes ou inicie uma nova conversa."

SUGGESTIONS = [
    "Quais violões até R$ 1000?",
    "Qual o endereço da loja?",
    "Quanto custa o Takamine GD20?",
    "Como funciona o frete em Campo Grande?",
    "Quais promoções estão ativas?",
]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;600&display=swap');

        :root {
          --brand: #0f3d2e;
          --brand-soft: #1a5c45;
          --accent: #c4922a;
          --bg: #eef2f0;
          --panel: #ffffff;
          --ink: #1c2420;
          --muted: #4d5f56;
        }

        html, body, .stApp, [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(1200px 500px at 10% -10%, #d9ebe3 0%, transparent 55%),
            radial-gradient(900px 400px at 100% 0%, #f3e6c8 0%, transparent 50%),
            var(--bg) !important;
          color: var(--ink) !important;
          font-family: "Source Sans 3", "Segoe UI", sans-serif !important;
        }

        /* Área principal: texto escuro legível */
        section.main, section[data-testid="stMain"],
        section.main p, section.main li, section.main span,
        section.main label, section.main h1, section.main h2,
        section.main h3, section.main h4, section.main strong,
        section.main .stMarkdown, section.main .stMarkdown p,
        section.main [data-testid="stMarkdownContainer"],
        section.main [data-testid="stMarkdownContainer"] * {
          color: var(--ink) !important;
        }

        .emporio-hero {
          padding: 0.85rem 1rem 1.1rem 1rem;
          margin-bottom: 1rem;
          border-radius: 16px;
          background: linear-gradient(135deg, #0f3d2e 0%, #1a5c45 70%);
          border: 1px solid rgba(15, 61, 46, 0.2);
        }
        .emporio-brand {
          font-family: Fraunces, Georgia, serif;
          font-size: clamp(1.8rem, 3vw, 2.4rem);
          font-weight: 700;
          color: #f4faf7 !important;
          letter-spacing: -0.02em;
          margin: 0;
          line-height: 1.1;
        }
        .emporio-slogan {
          margin: 0.35rem 0 0 0;
          color: #d5e8df !important;
          font-size: 1.05rem;
        }
        .emporio-chip {
          display: inline-block;
          margin-top: 0.75rem;
          padding: 0.2rem 0.65rem;
          border-radius: 999px;
          background: rgba(196, 146, 42, 0.95);
          color: #1c2420 !important;
          font-size: 0.8rem;
          font-weight: 600;
        }

        [data-testid="stChatMessage"] {
          background: var(--panel) !important;
          border: 1px solid rgba(15, 61, 46, 0.12);
          border-radius: 14px;
          padding: 0.5rem 0.75rem;
          color: var(--ink) !important;
        }
        [data-testid="stChatMessage"] * {
          color: var(--ink) !important;
        }
        [data-testid="stChatMessage"] code,
        [data-testid="stChatMessage"] pre {
          color: var(--ink) !important;
          background: #eef2f0 !important;
        }
        [data-testid="stChatMessage"] table,
        [data-testid="stChatMessage"] th,
        [data-testid="stChatMessage"] td {
          color: var(--ink) !important;
          border-color: rgba(28, 36, 32, 0.18) !important;
        }

        /* Sugestões / botões da área principal */
        section.main .stButton > button {
          background: #ffffff !important;
          color: #0f3d2e !important;
          border: 1px solid rgba(15, 61, 46, 0.28) !important;
          font-weight: 600 !important;
        }
        section.main .stButton > button:hover {
          background: #e4f0ea !important;
          border-color: #0f3d2e !important;
          color: #0f3d2e !important;
        }
        section.main .stButton > button p,
        section.main .stButton > button span {
          color: #0f3d2e !important;
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {
          color: var(--ink) !important;
          caret-color: var(--ink) !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
          color: var(--muted) !important;
        }

        /* Sidebar: texto claro sobre verde escuro */
        div[data-testid="stSidebar"] {
          background: linear-gradient(180deg, #123d30 0%, #0c2a21 100%) !important;
        }
        div[data-testid="stSidebar"],
        div[data-testid="stSidebar"] p,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] li,
        div[data-testid="stSidebar"] .stMarkdown,
        div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
          color: #e8f2ed !important;
        }
        div[data-testid="stSidebar"] .stButton > button {
          background: rgba(255,255,255,0.12) !important;
          border: 1px solid rgba(255,255,255,0.28) !important;
          color: #ffffff !important;
        }
        div[data-testid="stSidebar"] .stButton > button p,
        div[data-testid="stSidebar"] .stButton > button span {
          color: #ffffff !important;
        }
        div[data-testid="stSidebar"] code {
          color: #f4faf7 !important;
          background: rgba(0,0,0,0.25) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def _load_runtime():
    settings = get_settings()
    logs: list[str] = []
    agent, cfg = bootstrap_agent(settings=settings, log=logs.append)
    return agent, cfg, logs


def _ensure_session(max_messages: int) -> None:
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory(max_messages=max_messages)
    if "ui_messages" not in st.session_state:
        st.session_state.ui_messages = []


def _reset_chat(max_messages: int) -> None:
    st.session_state.memory = ConversationMemory(max_messages=max_messages)
    st.session_state.ui_messages = []


def main() -> None:
    st.set_page_config(
        page_title="Empório da Música — Chat",
        page_icon="🎸",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_styles()

    settings = get_settings()
    if not settings.groq_api_key:
        st.error(
            "GROQ_API_KEY não configurada. Crie um `.env` a partir de `.env.example` "
            "com a chave de https://console.groq.com"
        )
        st.stop()

    with st.spinner("Preparando agente, dados e embeddings..."):
        try:
            agent, cfg, boot_logs = _load_runtime()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha ao iniciar o agente: {exc}")
            st.stop()

    _ensure_session(cfg.max_history_messages)

    with st.sidebar:
        st.markdown("### Atendimento")
        st.caption("Campo Grande/MS · instrumentos musicais")
        if st.button("Nova conversa", use_container_width=True):
            _reset_chat(cfg.max_history_messages)
            st.rerun()
        if st.button("Reiniciar agente", use_container_width=True):
            _load_runtime.clear()
            _reset_chat(cfg.max_history_messages)
            st.rerun()
        show_tools = st.toggle("Mostrar tools usadas", value=False)
        st.markdown("---")
        st.markdown("**Modelo**")
        st.code(cfg.groq_model, language=None)
        with st.expander("Inicialização"):
            for line in boot_logs or ["Pronto."]:
                st.write(f"• {line}")
        st.markdown("---")
        st.caption("Dica: limpe o histórico se bater rate limit do Groq free tier.")

    st.markdown(
        """
        <div class="emporio-hero">
          <p class="emporio-brand">Empório da Música</p>
          <p class="emporio-slogan">Sua música começa aqui — atendimento com catálogo, pedidos e políticas.</p>
          <span class="emporio-chip">assistente virtual</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.ui_messages:
        cols = st.columns(len(SUGGESTIONS))
        for col, suggestion in zip(cols, SUGGESTIONS):
            if col.button(suggestion, use_container_width=True):
                st.session_state.pending_prompt = suggestion
                st.rerun()

    for msg in st.session_state.ui_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.session_state.pop("pending_prompt", None) or st.chat_input(
        "Pergunte sobre produtos, pedidos, frete, trocas..."
    )

    if not prompt:
        return

    capped = prompt[: cfg.max_user_input_chars]
    with st.chat_message("user"):
        st.markdown(capped)

    with st.chat_message("assistant"):
        with st.spinner("Consultando catálogo e políticas..."):
            try:
                answer, messages = run_agent_turn(
                    agent,
                    capped,
                    history=st.session_state.memory.as_list(),
                    settings=cfg,
                )
                st.session_state.memory.replace_from_turn(messages)
                st.session_state.ui_messages.append({"role": "user", "content": capped})
                st.session_state.ui_messages.append({"role": "assistant", "content": answer})
                if show_tools:
                    from langchain_core.messages import ToolMessage

                    used = sorted(
                        {
                            getattr(m, "name", "tool")
                            for m in messages
                            if isinstance(m, ToolMessage)
                        }
                    )
                    if used:
                        st.caption("Tools: " + ", ".join(used))
            except Exception as exc:  # noqa: BLE001
                answer = _friendly_error(exc)
                # Não altera memory/ui_messages em falha — evita dessincronizar histórico
        st.markdown(answer)


if __name__ == "__main__":
    main()
