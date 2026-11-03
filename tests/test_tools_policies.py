import pytest
from langchain_core.embeddings import FakeEmbeddings

from emporio_agent.data.ingest_policies import ingest_policies
from emporio_agent.tools import policies as policy_tools


@pytest.mark.unit
def test_search_policies_tool(tmp_path, policies_pdf):
    chroma = tmp_path / "chroma"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    policy_tools.set_chroma_dir(chroma)
    policy_tools.set_embeddings(emb)
    try:
        result = policy_tools.search_policies.invoke({"query": "endereço da loja"})
        assert "Maio" in result or "Campo Grande" in result or "contato" in result.lower()
    finally:
        policy_tools.set_chroma_dir(None)
        policy_tools.set_embeddings(None)
