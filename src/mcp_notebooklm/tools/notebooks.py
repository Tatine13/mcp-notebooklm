"""Notebook management tools for MCP NotebookLM."""

from typing import List, Dict, Any, Optional
from fastmcp import Context
from loguru import logger
from ..exceptions import NotebookNotFoundError

async def list_notebooks(ctx: Context) -> List[Dict[str, Any]]:
    """List all available notebooks."""
    try:
        client = ctx.request_context.lifespan_context
        return await client.list_notebooks()
    except Exception as e:
        logger.error(f"Failed to list notebooks: {e}")
        raise

async def select_notebook(ctx: Context, notebook_id: str) -> str:
    """Select a notebook."""
    try:
        client = ctx.request_context.lifespan_context
        
        # Verify notebook exists
        notebook_info = await client.get_notebook_info(notebook_id)
        client.set_notebook(notebook_id)
        
        return f"✅ Selected notebook: {notebook_info['title']} (ID: {notebook_id})"
    except NotebookNotFoundError:
        return f"❌ Notebook not found: {notebook_id}"
    except Exception as e:
        logger.error(f"Failed to select notebook: {e}")
        return f"❌ Error: {str(e)}"

async def create_notebook(ctx: Context, title: str) -> Dict[str, Any]:
    """Create a new notebook."""
    try:
        client = ctx.request_context.lifespan_context
        return await client.create_notebook(title)
    except Exception as e:
        logger.error(f"Failed to create notebook: {e}")
        raise

async def get_notebook_info(ctx: Context, notebook_id: str) -> Dict[str, Any]:
    """Get notebook details."""
    try:
        client = ctx.request_context.lifespan_context
        return await client.get_notebook_info(notebook_id)
    except NotebookNotFoundError:
        return {"error": f"Notebook not found: {notebook_id}"}
    except Exception as e:
        logger.error(f"Failed to get notebook info: {e}")
        raise

async def get_current_notebook(ctx: Context) -> Dict[str, Any]:
    """Get current notebook."""
    try:
        client = ctx.request_context.lifespan_context
        notebook_id = client.current_notebook_id
        
        if not notebook_id:
            return {
                "current_notebook": None,
                "message": "No notebook selected. Use select_notebook to choose one."
            }
        
        info = await client.get_notebook_info(notebook_id)
        return {
            "current_notebook": notebook_id,
            "info": info
        }
    except Exception as e:
        logger.error(f"Failed to get current notebook: {e}")
        raise

async def rename_notebook(ctx: Context, notebook_id: str, title: str) -> Dict[str, Any]:
    """Rename a notebook."""
    try:
        client = ctx.request_context.lifespan_context
        return await client.rename_notebook(notebook_id, title)
    except Exception as e:
        logger.error(f"Failed to rename notebook: {e}")
        raise

async def delete_notebook(ctx: Context, notebook_id: str) -> str:
    """Delete a notebook."""
    try:
        client = ctx.request_context.lifespan_context
        success = await client.delete_notebook(notebook_id)
        if success:
            return f"✅ Notebook deleted: {notebook_id}"
        return f"❌ Failed to delete notebook: {notebook_id}"
    except Exception as e:
        logger.error(f"Failed to delete notebook: {e}")
        return f"❌ Error: {str(e)}"

async def export_notebook(ctx: Context, notebook_id: str) -> Dict[str, Any]:
    """Export notebook data."""
    try:
        client = ctx.request_context.lifespan_context
        return await client.export_notebook(notebook_id)
    except Exception as e:
        logger.error(f"Failed to export notebook: {e}")
        raise
