import pytest
from unittest.mock import patch, MagicMock
from app.services.rag import generate_rag_response

@pytest.mark.asyncio
async def test_guardrail_blocks_unrelated_query():
    # Mock check_query_safety to return False (i.e., query is unsafe/unrelated)
    with patch("app.services.rag.check_query_safety", return_value=False):
        response = generate_rag_response(
            query="What is the weather in Tokyo?",
            index_dir="dummy_dir",
            rewrite=False
        )
        
        assert "I'm sorry, I can only answer technical questions" in response["answer"]
        assert len(response["references"]) == 0

@pytest.mark.asyncio
async def test_guardrail_allows_technical_query():
    # Mock check_query_safety to return True
    with patch("app.services.rag.check_query_safety", return_value=True):
        # Mock the agents as before to avoid real API calls
        with patch("smolagents.ToolCallingAgent.run", return_value="Technical answer"):
            response = generate_rag_response(
                query="How does the ingestion work?",
                index_dir="dummy_dir",
                rewrite=False
            )
            assert "Technical answer" in response["answer"]
