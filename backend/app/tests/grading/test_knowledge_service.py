"""
Tests for knowledge service and RAG retrieval.

Integration tests (marked with 'integration') require OPENAI_API_KEY
and a running postgres instance. Unit tests run without either.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.grading.knowledge_service import (
    chunk_text,
    extract_text_from_pdf,
    _normalise,
)


class TestChunking:
    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("") == []

    def test_short_text_returns_single_chunk(self):
        text = " ".join(["word"] * 100)
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].startswith("word")

    def test_long_text_returns_multiple_chunks(self):
        text = " ".join([f"word{i}" for i in range(1200)])
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        assert len(chunks) > 2

    def test_chunks_overlap(self):
        words = [f"w{i}" for i in range(600)]
        text  = " ".join(words)
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        # First chunk ends with w399, second chunk starts around w320
        assert "w320" in chunks[1]

    def test_chunks_preserve_all_words(self):
        # Every word from the first chunk should appear in the output
        text = " ".join([f"word{i}" for i in range(800)])
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        # The last word should be in the final chunk
        assert "word799" in chunks[-1]

    def test_chunks_within_size_limit(self):
        text = " ".join([f"word{i}" for i in range(2000)])
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 400

    def test_very_short_chunks_discarded(self):
        # A paragraph of only 10 words — below MIN_CHUNK_LEN chars
        chunks = chunk_text("hi there ok")
        assert chunks == []


class TestNormalise:
    def test_collapses_multiple_spaces(self):
        assert _normalise("hello   world") == "hello world"

    def test_collapses_excessive_newlines(self):
        result = _normalise("para1\n\n\n\npara2")
        assert "\n\n\n" not in result
        assert "para1" in result
        assert "para2" in result


class TestPDFExtraction:
    def test_empty_bytes_raises(self):
        import io
        import pdfplumber
        # Create a minimal valid PDF that has no text
        # (We just test the exception path for unparseable input)
        with pytest.raises(Exception):
            extract_text_from_pdf(b"not a pdf")


class TestEmbedTexts:
    @pytest.mark.asyncio
    async def test_returns_correct_dimension(self):
        """Mock OpenAI to verify we handle the response structure correctly."""
        fake_embedding = [0.1] * 1536

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=fake_embedding)]

        with patch("app.services.grading.knowledge_service.AsyncOpenAI") as MockClient:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.grading.knowledge_service.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"
                from app.services.grading.knowledge_service import embed_texts
                result = await embed_texts(["test sentence"])

        assert len(result) == 1
        assert len(result[0]) == 1536

    @pytest.mark.asyncio
    async def test_no_api_key_raises(self):
        with patch("app.services.grading.knowledge_service.settings") as mock_settings:
            mock_settings.openai_api_key = None
            from app.services.grading.knowledge_service import embed_texts
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                await embed_texts(["test"])


class TestDocumentStorage:
    @pytest.mark.asyncio
    async def test_store_and_list(self, db):
        from app.services.grading.knowledge_service import store_chunks, list_documents
        fake_emb = [[0.1] * 1536, [0.2] * 1536]
        count = await store_chunks(
            db,
            source_title="Test Document",
            source_label="test_document",
            subject_tag="ENG",
            chunks=["Chunk one content here for testing purposes long enough to pass min length check.",
                    "Chunk two content here for testing purposes long enough to pass min length check."],
            embeddings=fake_emb,
            is_example=False,
        )
        assert count == 2

        docs = await list_documents(db)
        labels = [d["source_label"] for d in docs]
        assert "test_document" in labels

    @pytest.mark.asyncio
    async def test_delete_document(self, db):
        from app.services.grading.knowledge_service import store_chunks, delete_document, list_documents
        fake_emb = [[0.1] * 1536]
        await store_chunks(
            db,
            source_title="To Delete",
            source_label="to_delete",
            subject_tag="BIOL",
            chunks=["Some content long enough for the minimum character threshold here."],
            embeddings=fake_emb,
        )
        deleted = await delete_document(db, "to_delete")
        assert deleted == 1
        docs = await list_documents(db)
        assert "to_delete" not in [d["source_label"] for d in docs]
