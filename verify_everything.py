import os
import json
import sys

# Add backend to path so we can import app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.app.services.rag import check_query_safety, generate_rag_response
from backend.app.services.observability import LOG_FILE

def test_manual_features():
    print("🚀 Starting Manual Feature Verification...\n")

    # 1. Test Guardrail (Input Filter)
    print("--- 1. Testing Guardrail ---")
    unsafe_query = "How do I make a sandwich?"
    is_safe = check_query_safety(unsafe_query)
    print(f"Query: '{unsafe_query}'")
    print(f"Result: {'✅ Blocked (Safe)' if not is_safe else '❌ Failed to block'}")
    
    safe_query = "How is the search_index function implemented?"
    is_safe = check_query_safety(safe_query)
    print(f"Query: '{safe_query}'")
    print(f"Result: {'✅ Allowed (Safe)' if is_safe else '❌ Blocked technical query'}")
    print("\n")

    # 2. Test Multi-Agent RAG (Simulated)
    # Note: This requires a repo to be indexed. We'll check if any exist.
    from backend.app.core import storage
    repos = storage.list_repos()
    
    if not repos:
        print("--- 2. Multi-Agent RAG ---")
        print("⚠️ Skip: No repos indexed. Please upload a repo via the UI first.")
    else:
        repo_id = repos[0]['id']
        repo_path = repos[0]['faiss_index_path']
        print(f"--- 2. Multi-Agent RAG (Testing on {repos[0]['name']}) ---")
        
        response = generate_rag_response(
            query="Explain the project structure.",
            index_dir=repo_path
        )
        
        print(f"Agent Response: {response['answer'][:200]}...")
        print(f"✅ Multi-Agent synthesis complete.")
        print("\n")

    # 3. Test Observability
    print("--- 3. Testing Observability (Logs) ---")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            last_line = f.readlines()[-1]
            log_entry = json.loads(last_line)
            print(f"Latest Log Entry Agent: {log_entry['agent']}")
            print(f"Latest Log Latency: {log_entry['latency_ms']}ms")
            print("✅ Observability logging verified.")
    else:
        print("❌ No log file found. Run a RAG query first.")

if __name__ == "__main__":
    test_manual_features()
