"""Ingestão do PDF de políticas para ChromaDB com embeddings locais."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from emporio_agent.config import CHROMA_DIR, POLICIES_PDF, Settings, ensure_runtime_dirs, get_settings
from emporio_agent.logging_setup import get_logger, setup_logging

COLLECTION_NAME = "store_policies"
logger = get_logger(__name__)
_embeddings_singleton: HuggingFaceEmbeddings | None = None
_SUBCHUNK_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)


def _normalize_pdf_text(raw: str) -> str:
    """Normaliza PDFs do Google Docs (muitas vezes 1 palavra por linha)."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r" *\n *", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
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


def _pdf_fingerprint(pdf_path: Path) -> str:
    h = hashlib.sha256()
    h.update(str(pdf_path.stat().st_mtime_ns).encode())
    h.update(str(pdf_path.stat().st_size).encode())
    return h.hexdigest()[:16]


def _split_by_sections(text: str) -> list[Document]:
    """Fatia por 'N. Título'; sub-chunka seções longas."""
    pattern = re.compile(r"(?=^\d+\.\s+[A-ZÀ-Ü].+$)", re.MULTILINE)
    parts = [p.strip() for p in pattern.split(text) if p.strip()]

    docs: list[Document] = []
    if len(parts) >= 3:
        chunk_id = 0
        for part in parts:
            first_line = part.splitlines()[0][:120]
            if len(part) <= 1200:
                chunk_id += 1
                docs.append(
                    Document(
                        page_content=part,
                        metadata={
                            "section": first_line,
                            "source": "políticas_da_loja.pdf",
                            "chunk": chunk_id,
                        },
                    )
                )
            else:
                subdocs = _SUBCHUNK_SPLITTER.create_documents(
                    [part],
                    metadatas=[
                        {
                            "section": first_line,
                            "source": "políticas_da_loja.pdf",
                        }
                    ],
                )
                for sub in subdocs:
                    chunk_id += 1
                    sub.metadata["chunk"] = chunk_id
                    docs.append(sub)
        return docs

    return _SUBCHUNK_SPLITTER.create_documents(
        [text],
        metadatas=[{"source": "políticas_da_loja.pdf", "section": "manual"}],
    )


def get_embeddings(
    settings: Settings | None = None,
    *,
    force_reload: bool = False,
) -> HuggingFaceEmbeddings:
    """Carrega embeddings uma vez; prioriza cache local para evitar Hub/SSL no chat."""
    global _embeddings_singleton
    if _embeddings_singleton is not None and not force_reload:
        return _embeddings_singleton

    cfg = settings or get_settings()
    if cfg.hf_token:
        os.environ.setdefault("HF_TOKEN", cfg.hf_token)
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", cfg.hf_token)

    try:
        emb = HuggingFaceEmbeddings(
            model_name=cfg.embedding_model,
            model_kwargs={"local_files_only": True},
        )
    except (OSError, ValueError):
        emb = HuggingFaceEmbeddings(model_name=cfg.embedding_model)

    emb.embed_query("warmup")
    _embeddings_singleton = emb
    return emb


def _wipe_chroma(persist_dir: Path) -> None:
    if persist_dir.exists():
        shutil.rmtree(persist_dir, ignore_errors=True)
    persist_dir.mkdir(parents=True, exist_ok=True)


def ingest_policies(
    pdf_path: Path | None = None,
    chroma_dir: Path | None = None,
    settings: Settings | None = None,
    force: bool = False,
    embeddings=None,
) -> Path:
    cfg = settings or get_settings()
    persist_dir = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    pdf = Path(pdf_path) if pdf_path else POLICIES_PDF
    ensure_runtime_dirs()
    persist_dir.mkdir(parents=True, exist_ok=True)

    marker = persist_dir / ".ingested"
    fingerprint = _pdf_fingerprint(pdf)
    if marker.exists() and not force and any(persist_dir.iterdir()):
        try:
            stored = marker.read_text(encoding="utf-8").strip()
            if stored == fingerprint or stored == "ok":
                # "ok" legado: força reindex se o modelo/estrutura mudou e fingerprint novo
                if stored == fingerprint:
                    return persist_dir
        except OSError:
            pass

    text = extract_pdf_text(pdf)
    docs = _split_by_sections(text)
    if not docs:
        raise RuntimeError("Nenhum texto extraído do PDF de políticas.")

    emb = embeddings if embeddings is not None else get_embeddings(cfg)
    _wipe_chroma(persist_dir)
    Chroma.from_documents(
        documents=docs,
        embedding=emb,
        persist_directory=str(persist_dir),
        collection_name=COLLECTION_NAME,
    )
    marker.write_text(fingerprint, encoding="utf-8")
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
    top_k = k if k is not None else cfg.rag_top_k
    # MMR diversifica chunks; similarity é fallback (ex.: FakeEmbeddings em testes)
    try:
        return store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": top_k, "fetch_k": max(top_k * 3, 8)},
        )
    except Exception:  # noqa: BLE001
        return store.as_retriever(search_kwargs={"k": top_k})


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
    marker = persist_dir / ".ingested"
    if not marker.exists():
        return False
    # Coleção precisa ter algum artefato além do marker
    return any(p.name != ".ingested" for p in persist_dir.iterdir())


if __name__ == "__main__":
    setup_logging()
    out = ingest_policies(force=True)
    logger.info("Chroma pronto em %s", out)
