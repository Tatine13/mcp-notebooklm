"""Chat tools for MCP NotebookLM."""

from typing import List, Dict, Any, Optional

from fastmcp import Context
from loguru import logger

from ..exceptions import NotebookNotFoundError


async def get_chat_history(
    ctx: Context,
    notebook_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get chat history for a notebook.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        limit: Maximum number of messages to return
        
    Returns:
        List of chat messages
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        # Use the wrapper method which handles attribute extraction and logging
        messages = await client.get_chat_history(notebook_id)
        
        # Limit results (get_chat_history returns full history)
        if limit > 0:
            return messages[-limit:]
        return messages
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise


# Note: clear_chat removed - API notebooklm-py does not support clearing chat history server-side
# This functionality is available in the NotebookLM web UI but not exposed via the RPC API
