import time
from typing import List, Tuple, Dict, Any
from groq import Groq
from smolagents import Tool, ToolCallingAgent, LiteLLMModel
from app.core.config import settings
from app.services.embedding import search_index
from app.services.observability import log_llm_transaction

# Groq Client for utility tasks
client = Groq(api_key=settings.GROQ_API_KEY)

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
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
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
    Multi-Agent RAG pipeline using smolagents:
    1. Researcher Agent: Specializes in using the search_codebase tool.
    2. Manager Agent: Coordinates the researcher and provides the final answer.
    """
    start_time = time.time()

    # Guardrail 1: Input Safety/Relevance
    if not check_query_safety(query):
        return {
            "rewritten_query": query,
            "answer": "I'm sorry, I can only answer technical questions related to the codebase. Please ask about code structure, logic, or implementation.",
            "references": [],
            "tokens_used": 0,
            "response_time_ms": int((time.time() - start_time) * 1000),
        }

    # 1. Setup Model
    model = LiteLLMModel(
        model_id=f"groq/{settings.GROQ_MODEL}",
        api_key=settings.GROQ_API_KEY,
    )

    # 2. Setup Tools
    search_tool = SearchCodebaseTool(index_dir=index_dir, top_k=top_k)

    # 3. Setup Researcher Agent
    researcher = ToolCallingAgent(
        tools=[search_tool],
        model=model,
        name="code_researcher",
        description="A specialist that searches the codebase to find relevant code snippets for a query.",
    )

    # 4. Setup Manager (Synthesis)
    # We use a direct model call for the manager to avoid tool-calling overhead/errors
    def run_manager(findings, original_query):
        synthesis_prompt = f"""You are a senior technical lead reviewing a researcher's findings.
Based on the code snippets found below, provide a final, polished answer to the user.
Ensure the answer is accurate, well-formatted, and cites the correct files.

Researcher's Findings:
{findings}

User Original Question: {original_query}"""
        
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": synthesis_prompt}],
            max_tokens=2048,
            temperature=0.1,
        )
        return response.choices[0].message.content

    # 5. Run Multi-Agent Flow
    try:
        # Agent 1: Researcher (Finds the code)
        research_start = time.time()
        research_task = f"Find and explain the most relevant code for: {query}"
        research_output = researcher.run(research_task)
        log_llm_transaction(
            "code_researcher", 
            research_task, 
            research_output, 
            int((time.time() - research_start) * 1000)
        )
        
        # Step 2: Manager (Synthesizes the final answer)
        manager_start = time.time()
        answer = run_manager(research_output, query)
        
        log_llm_transaction(
            "manager", 
            "Synthesis", 
            answer, 
            int((time.time() - manager_start) * 1000)
        )
        
    except Exception as e:
        answer = f"An error occurred while processing your request: {str(e)}"

    elapsed_ms = int((time.time() - start_time) * 1000)

    # 6. Extract references from the tool's last run
    references = []
    for chunk, score in search_tool.retrieved_chunks:
        references.append({
            "file_path": chunk["file_path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "language": chunk["language"],
            "score": round(score, 4),
        })

    return {
        "rewritten_query": query,
        "answer": answer,
        "references": references,
        "tokens_used": 0,
        "response_time_ms": elapsed_ms,
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

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert software architect. Analyze code and provide clear architectural overviews."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    return response.choices[0].message.content
