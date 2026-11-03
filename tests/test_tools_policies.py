import pytest
from langchain_core.embeddings import FakeEmbeddings

from emporio_agent.data.ingest_policies import ingest_policies, search_policy_chunks
from emporio_agent.tools import policies as policy_tools


@pytest.mark.unit
def test_search_policies_tool(tmp_path, policies_pdf, monkeypatch):
    chroma = tmp_path / "chroma"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    policy_tools.set_chroma_dir(chroma)
    policy_tools.set_embeddings(emb)
    monkeypatch.setattr(
        "emporio_agent.tools.policies.get_settings",
        lambda: type("S", (), {"rag_top_k": 30})(),
    )
    try:
        result = policy_tools.search_policies.invoke({"query": "endereço da loja"})
        lowered = result.lower()
        assert "maio" in lowered or "campo grande" in lowered or "contato" in lowered
    finally:
        policy_tools.set_chroma_dir(None)
        policy_tools.set_embeddings(None)


@pytest.mark.unit
def test_search_policy_chunks_empty_query_still_returns(tmp_path, policies_pdf):
    chroma = tmp_path / "chroma"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    result = search_policy_chunks("xyzzy_no_match_token", chroma_dir=chroma, embeddings=emb, k=3)
    # FakeEmbeddings sempre retorna k docs; garante formato
    assert "[" in result
