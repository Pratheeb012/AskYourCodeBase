import time
from typing import List, Tuple, Dict, Any
from groq import Groq
from smolagents import Tool, ToolCallingAgent, LiteLLMModel
from app.core.config import settings
from app.services.embedding import search_index
from app.services.observability import log_llm_transaction

# Groq Client for utility tasks
client = Groq(api_key=settings.GROQ_API_KEY)

def safe_chat_completion(messages: list, max_tokens: int = 1024, temperature: float = 0.1, model: str = None):
    """
    Executes a chat completion with automatic failover if rate limited.
    """
    primary_model = model or settings.GROQ_MODEL
    fallback_model = settings.GROQ_FALLBACK_MODEL

    try:
        # Try Primary
        return client.chat.completions.create(
            model=primary_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:
        # If rate limited (429) or any error, try fallback
        if "429" in str(e) or "rate_limit" in str(e).lower():
            print(f"⚠️ Rate limit on {primary_model}. Falling back to {fallback_model}...")
            return client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        raise e

class SearchCodebaseTool(Tool):
    name = "search_codebase"
    description = "Searches the repository for relevant code snippets based on a semantic query."
    inputs = {
        "query": {
            "type": "string",
            "description": "The technical search query to find code. Should include function names, classes, or keywords.",
        }
    }
    output_type = "string"

    def __init__(self, index_dir: str, top_k: int = 8, **kwargs):
        super().__init__(**kwargs)
        self.index_dir = index_dir
        self.top_k = top_k
        self.retrieved_chunks = []

    def forward(self, query: str) -> str:
        """
        Executes the semantic search and formats results for the agent.
        
        Args:
            query: The search string to look for in the vector index.
            
        Returns:
            A formatted string containing code snippets and file paths.
        """
        # 1. Retrieve relevant chunks
        retrieved = search_index(self.index_dir, query, top_k=self.top_k)
        self.retrieved_chunks = retrieved # Store for reference extraction
        
        if not retrieved:
            return "No relevant code found for this query."

        # 2. Format context
        parts = []
        for i, (chunk, score) in enumerate(retrieved, 1):
            parts.append(
                f"--- Snippet {i} ---\n"
                f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})\n"
                f"Language: {chunk['language']}\n"
                f"```{chunk['language']}\n{chunk['content']}\n```"
            )
        return "\n\n".join(parts)

def check_query_safety(query: str) -> bool:
    """Guardrail: Verify if the query is technical and related to software/codebase."""
    prompt = f"""You are a security guard for a software repository AI. 
Analyze the user query below. Is it a technical question specifically about code, software architecture, programming, or the repository?
If it is about cooking, weather, general chat, or anything unrelated to software development, respond with NO.

Respond with ONLY 'YES' or 'NO'.

Query: {query}"""
    try:
        response = safe_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        )
        return "YES" in response.choices[0].message.content.upper()
    except Exception:
        return True # Default to allow if check fails

def generate_rag_response(
    query: str,
    index_dir: str,
    top_k: int = 8,
    rewrite: bool = True,
) -> dict:
    """
    Robust RAG pipeline using direct Groq calls.
    1. Rewrite query (optional)
    2. Search codebase
    3. Synthesize answer
    """
    start_time = time.time()

    # Guardrail: Input Safety/Relevance
    if not check_query_safety(query):
        return {
            "rewritten_query": query,
            "answer": "I'm sorry, I can only answer technical questions related to the codebase. Please ask about code structure, logic, or implementation.",
            "references": [],
            "tokens_used": 0,
            "response_time_ms": int((time.time() - start_time) * 1000),
        }

    # 1. Query Rewriting / Search Optimization
    search_query = query
    if rewrite:
        try:
            rewrite_prompt = f"Given the user query: '{query}', generate a single technical search query (keywords, function names, etc.) to find relevant code in a repository. Respond with ONLY the search query."
            res = safe_chat_completion(
                messages=[{"role": "user", "content": rewrite_prompt}],
                max_tokens=50,
                temperature=0,
            )
            search_query = res.choices[0].message.content.strip().strip('"')
        except Exception:
            search_query = query

    # 2. Retrieve relevant chunks
    retrieved = search_index(index_dir, search_query, top_k=top_k)
    
    # Filter out massive lock-files and duplicate snippets from the same file
    # to save tokens and prevent Rate Limits (429)
    filtered_retrieved = []
    seen_files = {}
    
    for chunk, score in retrieved:
        path = chunk['file_path'].lower()
        if any(ignore in path for ignore in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', '.pyc']):
            continue
        
        # Limit to max 2 snippets per file to ensure variety and token efficiency
        seen_files[path] = seen_files.get(path, 0) + 1
        if seen_files[path] <= 2:
            filtered_retrieved.append((chunk, score))
            
    # Keep only the top 5 most relevant snippets to stay safe with token limits
    filtered_retrieved = filtered_retrieved[:5]

    if not filtered_retrieved:
        return {
            "rewritten_query": search_query,
            "answer": "I couldn't find any relevant code snippets (excluding lock files). Try a more specific technical query.",
            "references": [],
            "tokens_used": 0,
            "response_time_ms": int((time.time() - start_time) * 1000),
        }

    # 3. Synthesize Final Answer
    context_parts = []
    for i, (chunk, score) in enumerate(filtered_retrieved, 1):
        # Cap each snippet to ~100-150 lines to prevent token overflow
        safe_content = chunk['content'][:4000] 
        if len(chunk['content']) > 4000:
            safe_content += "\n... [truncated for brevity] ..."
            
        context_parts.append(
            f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})\n"
            f"```\n{safe_content}\n```"
        )
    context = "\n\n".join(context_parts)

    system_prompt = """You are a senior software engineer assistant. 
Your goal is to answer the user's question accurately using ONLY the provided code snippets as context.
If the snippets don't contain the answer, say you don't know based on the current context.
Always cite file names when explaining code."""

    user_prompt = f"""User Question: {query}

Code Context:
{context}

Final Answer:"""

    try:
        completion = safe_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2048,
            temperature=0.1,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"An error occurred while generating the answer: {str(e)}"

    # 4. Format references for UI
    references = []
    for chunk, score in filtered_retrieved:
        references.append({
            "file_path": chunk["file_path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "language": chunk["language"],
            "score": round(float(score), 4),
        })

    return {
        "rewritten_query": search_query,
        "answer": answer,
        "references": references,
        "tokens_used": 0,
        "response_time_ms": int((time.time() - start_time) * 1000),
    }

def generate_architecture_summary(index_dir: str) -> str:
    """Generate a high-level architecture explanation of the codebase using Groq."""
    from app.services.embedding import load_faiss_index
    _, metadata = load_faiss_index(index_dir)

    # Sample chunks from unique files
    files_seen = set()
    sampled = []
    for chunk in metadata:
        if chunk["file_path"] not in files_seen:
            sampled.append(chunk)
            files_seen.add(chunk["file_path"])
        if len(sampled) >= 30:
            break

    context = "\n\n".join(
        f"[{c['file_path']}]\n```{c['language']}\n{c['content'][:600]}\n```"
        for c in sampled
    )

    prompt = f"""Analyze the following code samples from a repository and provide a comprehensive architecture overview.

Code Samples:
{context}

Provide:
1. **Project Overview**: What does this project do?
2. **Technology Stack**: Languages, frameworks, libraries used
3. **Architecture Pattern**: How is the code organized?
4. **Key Components**: Main modules/files and their roles
5. **Data Flow**: How data moves through the system
6. **Entry Points**: Where execution starts
"""

    response = safe_chat_completion(
        messages=[
            {"role": "system", "content": "You are an expert software architect. Analyze code and provide clear architectural overviews."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    return response.choices[0].message.content
