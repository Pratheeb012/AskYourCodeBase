import os
import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from app.services.embedding import search_index
from app.core import storage

# Create an MCP server
server = Server("AskYourCodebase")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="search_codebase",
            description="Search the indexed codebase for relevant code snippets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_id": {"type": "string", "description": "The ID of the repository to search"},
                    "query": {"type": "string", "description": "The search query"},
                    "top_k": {"type": "integer", "default": 5}
                },
                "required": ["repo_id", "query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    if name == "search_codebase":
        repo_id = arguments.get("repo_id")
        query = arguments.get("query")
        top_k = arguments.get("top_k", 5)
        
        repo = storage.get_repo(repo_id)
        if not repo or not repo.get("faiss_index_path"):
            return [types.TextContent(type="text", text=f"Repository {repo_id} not found or not indexed.")]
        
        # Perform search
        results = search_index(repo["faiss_index_path"], query, top_k=top_k)
        
        # Format results
        output = []
        for chunk, score in results:
            output.append(
                f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})\n"
                f"Score: {score:.4f}\n"
                f"```\n{chunk['content']}\n```"
            )
        
        return [types.TextContent(type="text", text="\n\n".join(output))]
    
    raise ValueError(f"Unknown tool: {name}")

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="AskYourCodebase",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities()
                )
            )
    asyncio.run(main())
