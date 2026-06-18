"""
Standalone RAG validation script.

Usage (from backend/):
    python -m scripts.test_retrieval --query "explain the causes of World War I" --subject HIST
    python -m scripts.test_retrieval --query "osmosis and diffusion" --subject BIOL --k 4
"""
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import AsyncSessionLocal
from app.services.grading import knowledge_service, rag_retriever


async def run(query: str, subject_tag: str, k: int) -> None:
    async with AsyncSessionLocal() as db:
        # Show what's in the knowledge base for this subject
        docs = await knowledge_service.list_documents(db)
        subject_docs = [d for d in docs if d["subject_tag"].upper() == subject_tag.upper()]
        print(f"\n{'='*60}")
        print(f"Knowledge base for {subject_tag.upper()}: {len(subject_docs)} document group(s)")
        for d in subject_docs:
            flag = "[EXAMPLE]" if d["is_example"] else "[REF]    "
            print(f"  {flag}  {d['source_title']}  ({d['chunk_count']} chunks)")

        print(f"\nQuery: {query!r}")
        print(f"{'='*60}")

        # Reference chunks
        refs = await rag_retriever.retrieve_chunks(db, query, subject_tag.upper(), k=k)
        print(f"\nTop {k} reference chunks:")
        for i, c in enumerate(refs, 1):
            print(f"\n  [{i}] similarity={c.similarity:.4f}  {c.source_title}  chunk#{c.chunk_index}")
            print(f"      {c.content[:250]}{'…' if len(c.content) > 250 else ''}")

        # Example chunks
        examples = await rag_retriever.retrieve_examples(db, query, subject_tag.upper(), k=1)
        if examples:
            print(f"\nTop example answer chunk:")
            e = examples[0]
            print(f"  similarity={e.similarity:.4f}  {e.source_title}  chunk#{e.chunk_index}")
            print(f"  {e.content[:250]}{'…' if len(e.content) > 250 else ''}")
        else:
            print("\nNo example answer chunks found for this subject.")

        print(f"\n{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG retrieval for EssAssess")
    parser.add_argument("--query",   required=True,          help="Query / essay question")
    parser.add_argument("--subject", required=True,          help="Subject code (e.g. BIOL, ENG)")
    parser.add_argument("--k",       type=int, default=6,    help="Number of reference chunks to retrieve")
    args = parser.parse_args()
    asyncio.run(run(args.query, args.subject, args.k))


if __name__ == "__main__":
    main()
