import pytest
from langchain_core.embeddings import FakeEmbeddings

from emporio_agent.data.ingest_policies import (
    extract_pdf_text,
    ingest_policies,
    search_policy_chunks,
)


@pytest.mark.unit
def test_extract_pdf_contains_key_facts(policies_pdf):
    text = extract_pdf_text(policies_pdf)
    assert "14 de Maio" in text or "14 de maio" in text.lower()
    assert "Horário" in text or "horário" in text.lower()
    assert "arrependimento" in text.lower() or "Arrependimento" in text


@pytest.mark.unit
def test_ingest_and_retrieve_with_fake_embeddings(tmp_path, policies_pdf):
    chroma = tmp_path / "chroma"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    assert (chroma / ".ingested").exists()
    marker = (chroma / ".ingested").read_text(encoding="utf-8").strip()
    assert marker != ""
    assert marker != "ok"  # fingerprint real

    result = search_policy_chunks(
        "horário de funcionamento",
        chroma_dir=chroma,
        embeddings=emb,
        k=30,
    )
    lowered = result.lower()
    assert "09:00" in result or "funcionamento" in lowered or "segunda" in lowered
    assert "[" in result


@pytest.mark.unit
def test_retrieve_arrependimento(tmp_path, policies_pdf):
    chroma = tmp_path / "chroma2"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    result = search_policy_chunks(
        "posso devolver por arrependimento",
        chroma_dir=chroma,
        embeddings=emb,
        k=30,
    )
    lowered = result.lower()
    assert "7" in result or "arrependimento" in lowered or "devolução" in lowered


@pytest.mark.unit
def test_force_reingest_wipes(tmp_path, policies_pdf):
    chroma = tmp_path / "chroma3"
    emb = FakeEmbeddings(size=32)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    ingest_policies(pdf_path=policies_pdf, chroma_dir=chroma, force=True, embeddings=emb)
    result = search_policy_chunks("PIX", chroma_dir=chroma, embeddings=emb, k=20)
    assert "[" in result
