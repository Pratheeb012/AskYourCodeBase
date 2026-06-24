# AskYourCodeBase (RepoMind) - Project Documentation

## 1. What the Project Does
AskYourCodeBase (also referred to as RepoMind) is a premium, AI-native developer tool designed to transform how developers interact with complex codebases. It allows users to query any GitHub repository or local ZIP archive using natural language. By combining Retrieval-Augmented Generation (RAG) with deep static code analysis, the project provides context-aware answers, architectural insights, and dependency information to help developers understand codebases rapidly.

## 2. What We Have Done (Completed Features)
We have built a fully decoupled, full-stack application with the following completed features:
*   **User Authentication & Isolation:** Strict data partitioning and JWT-based authentication to ensure repository data and chat histories are private.
*   **Intelligent RAG Engine:** Implementation of an advanced RAG pipeline powered by Groq Llama-3 for real-time code understanding.
*   **AI Failover System:** Automatic fallback to a secondary model (Llama-3-8B) if the primary model (70B) hits a rate limit, ensuring 100% uptime.
*   **Code Ingestion Service:** Robust pipeline to handle ZIP uploads and GitHub cloning, converting raw code into semantic embeddings.
*   **Snippet Compression:** Smart truncation and filtering engine that reduces token usage (up to 90%) while maintaining context accuracy.
*   **Static Code Analysis:** AST-based static scanning to provide structural insights without consuming LLM tokens.
*   **Premium Developer Interface:** A React-based frontend utilizing a high-fidelity glassmorphism design system, supporting both dark and light modes with proactive UI intelligence (e.g., auto-switching tabs based on chat context).
*   **Model Context Protocol (MCP):** A fully functional MCP server integrated into the backend.

## 3. Technologies Used
### Backend
*   **Framework:** FastAPI (Python 3.10+) for high-speed, asynchronous API endpoints.
*   **AI/LLM:** Groq API (Llama-3-70B and Llama-3-8B).
*   **Vector Database:** FAISS for local, high-speed semantic search and embedding storage.
*   **Testing:** Pytest.

### Frontend
*   **Core:** React 18, Vite.
*   **State Management:** Zustand.
*   **Animations:** Framer Motion.
*   **Styling:** Vanilla CSS tailored for a premium Glassmorphism aesthetic.

## 4. MCP Tools Present
The backend includes an integrated MCP (Model Context Protocol) Server (`mcp_server.py`) with the following tool:
*   **`search_codebase`**: 
    *   **Description:** Searches the indexed codebase for relevant code snippets.
    *   **Parameters:** `repo_id` (string) and `query` (string), with an optional `top_k` (integer) for the number of results.
    *   **Functionality:** It retrieves the local FAISS index for the specific repository and performs a vector search against the provided natural language query, returning the file paths, line numbers, relevance scores, and code chunks.

## 5. Lags (Limitations and Current Issues)
*   **Scalability of Vector Search:** Currently using FAISS locally. While extremely fast, storing indices locally restricts horizontal scaling across multiple backend server instances.
*   **Ingestion Bottlenecks:** Indexing massive monolithic repositories or giant ZIP files can be CPU/memory intensive and may cause delays during the ingestion phase.
*   **Rate Limits:** High reliance on the Groq API means the system is subject to external rate limits, though the failover system mitigates this partially.
*   **AST Analysis Limits:** Static scanning via AST is language-dependent and may not fully support all esoteric or modern syntaxes uniformly.

## 6. Future Features That Can Be Added
*   **Cloud Vector Database Integration:** Migrating from local FAISS to Pinecone, Qdrant, or Weaviate for robust, distributed vector storage.
*   **GitHub Webhooks (Auto-Sync):** Adding webhook listeners to automatically re-index repositories when new commits or pull requests are pushed to the target GitHub repository.
*   **IDE Extensions:** Building VS Code or JetBrains plugins so developers can use the tool natively within their editors.
*   **Advanced Visualizations:** Generating dynamic dependency graphs and architecture diagrams directly in the UI.
*   **Multi-Agent Workflows:** Introducing specialized agents for specific tasks (e.g., a "Debugger Agent" vs an "Architecture Agent").

## 7. Cons
*   **Maintenance of Custom CSS:** The use of purely custom Vanilla CSS for the glassmorphism UI creates a higher maintenance burden compared to using established component libraries (like Tailwind or MUI).
*   **Resource Intensive Locally:** Running the FAISS index and local file extraction requires solid disk space and memory, which can bloat the server requirements as the user base grows.
*   **Vendor Lock-in Risk:** Heavy optimization for Groq's specific Llama-3 implementation might require refactoring if switching to another LLM provider (like OpenAI or Anthropic).
