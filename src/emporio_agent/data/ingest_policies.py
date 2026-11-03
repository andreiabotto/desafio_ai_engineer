"""Ingestão do PDF de políticas para ChromaDB com embeddings locais."""

from __future__ import annotations

import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from emporio_agent.config import CHROMA_DIR, POLICIES_PDF, Settings, ensure_runtime_dirs, get_settings

COLLECTION_NAME = "store_policies"


def _normalize_pdf_text(raw: str) -> str:
    """Normaliza PDFs do Google Docs (muitas vezes 1 palavra por linha)."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r" *\n *", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    # Reinsere quebras antes de seções numeradas do manual
    text = re.sub(r" (?=(\d+)\.\s+[A-ZÀ-Ü])", "\n", text)
    return text


def extract_pdf_text(pdf_path: Path | None = None) -> str:
    path = Path(pdf_path) if pdf_path else POLICIES_PDF
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return _normalize_pdf_text("\n".join(pages))


def _split_by_sections(text: str) -> list[Document]:
    """Tenta fatiar pelo padrão 'N. Título' do manual; fallback por tamanho."""
    pattern = re.compile(r"(?=^\d+\.\s+[A-ZÀ-Ü].+$)", re.MULTILINE)
    parts = [p.strip() for p in pattern.split(text) if p.strip()]

    docs: list[Document] = []
    if len(parts) >= 3:
        for i, part in enumerate(parts, start=1):
            first_line = part.splitlines()[0][:120]
            docs.append(
                Document(
                    page_content=part,
                    metadata={"section": first_line, "source": "políticas_da_loja.pdf", "chunk": i},
                )
            )
        return docs

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    return splitter.create_documents(
        [text],
        metadatas=[{"source": "políticas_da_loja.pdf", "section": "manual"}],
    )


def get_embeddings(settings: Settings | None = None) -> HuggingFaceEmbeddings:
    cfg = settings or get_settings()
    return HuggingFaceEmbeddings(model_name=cfg.embedding_model)


def ingest_policies(
    pdf_path: Path | None = None,
    chroma_dir: Path | None = None,
    settings: Settings | None = None,
    force: bool = False,
    embeddings=None,
) -> Path:
    cfg = settings or get_settings()
    persist_dir = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    ensure_runtime_dirs()
    persist_dir.mkdir(parents=True, exist_ok=True)

    marker = persist_dir / ".ingested"
    if marker.exists() and not force and any(persist_dir.iterdir()):
        return persist_dir

    text = extract_pdf_text(pdf_path)
    docs = _split_by_sections(text)
    if not docs:
        raise RuntimeError("Nenhum texto extraído do PDF de políticas.")

    emb = embeddings if embeddings is not None else get_embeddings(cfg)
    Chroma.from_documents(
        documents=docs,
        embedding=emb,
        persist_directory=str(persist_dir),
        collection_name=COLLECTION_NAME,
    )
    marker.write_text("ok", encoding="utf-8")
    return persist_dir


def get_policy_retriever(
    chroma_dir: Path | None = None,
    settings: Settings | None = None,
    k: int | None = None,
    embeddings=None,
):
    cfg = settings or get_settings()
    persist_dir = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    emb = embeddings if embeddings is not None else get_embeddings(cfg)
    if not (persist_dir / ".ingested").exists():
        ingest_policies(chroma_dir=persist_dir, settings=cfg, embeddings=emb)

    store = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=emb,
        collection_name=COLLECTION_NAME,
    )
    return store.as_retriever(search_kwargs={"k": k or cfg.rag_top_k})


def search_policy_chunks(
    query: str,
    chroma_dir: Path | None = None,
    settings: Settings | None = None,
    k: int | None = None,
    embeddings=None,
) -> str:
    retriever = get_policy_retriever(
        chroma_dir=chroma_dir, settings=settings, k=k, embeddings=embeddings
    )
    docs = retriever.invoke(query)
    if not docs:
        return "Nenhum trecho de política encontrado para esta consulta."

    blocks = []
    for i, doc in enumerate(docs, start=1):
        section = doc.metadata.get("section", "política")
        blocks.append(f"[{i}] ({section})\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(blocks)


def policies_ready(chroma_dir: Path | None = None) -> bool:
    persist_dir = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    return (persist_dir / ".ingested").exists()


if __name__ == "__main__":
    out = ingest_policies(force=True)
    print(f"Chroma pronto em {out}")