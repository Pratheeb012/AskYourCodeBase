import pytest
from unittest.mock import patch, MagicMock
from app.services.rag import generate_rag_response

@pytest.mark.asyncio
async def test_agent_rag_response():
    # Mock search_index to return some dummy chunks
    mock_chunks = [
        ({
            "file_path": "main.py",
            "start_line": 1,
            "end_line": 10,
            "content": "def main(): print('hello')",
            "language": "python"
        }, 0.9)
    ]
    
    with patch("app.services.rag.search_index", return_value=mock_chunks):
        # We need to mock the agents
        with patch("smolagents.ToolCallingAgent.run") as mock_run:
            # First call is researcher, second is manager
            mock_run.side_effect = ["Researcher findings...", "Final manager answer."]
            
            response = generate_rag_response(
                query="What does the main function do?",
                index_dir="dummy_dir",
                rewrite=False
            )
            
            assert "Final manager answer." in response["answer"]
            assert response["response_time_ms"] >= 0
            assert mock_run.call_count == 2
