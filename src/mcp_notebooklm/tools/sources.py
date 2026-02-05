"""Source management tools for MCP NotebookLM."""

from typing import List, Dict, Any, Optional
from pathlib import Path

from fastmcp import Context
from loguru import logger

from ..exceptions import NotebookNotFoundError


async def list_sources(
    ctx: Context,
    notebook_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all sources in a notebook.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        List of sources with metadata
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        async with await client._get_client() as nl_client:
            sources = await nl_client.sources.list(nb_id)
            return [
                {
                    "id": getattr(source, "id", "unknown"),
                    "name": getattr(source, "name", getattr(source, "title", "Unnamed Source")),
                    "type": getattr(source, "type", "unknown"),
                    "status": getattr(source, "status", "active"),
                }
                for source in sources
            ]
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise


async def add_source_url(
    ctx: Context,
    url: str,
    notebook_id: Optional[str] = None,
    wait: bool = True,
) -> Dict[str, Any]:
    """
    Add a URL source to a notebook.
    
    Args:
        url: URL to add (website, YouTube, etc.)
        notebook_id: Notebook ID (uses current if not provided)
        wait: If True, wait for source to be processed (default: True)
        
    Returns:
        Source details
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        async with await client._get_client() as nl_client:
            result = await nl_client.sources.add_url(
                nb_id, 
                url, 
                wait=wait,
            )
            
            return {
                "id": result.id,
                "name": getattr(result, "title", url),
                "url": url,
                "status": "added",
            }
    except Exception as e:
        logger.error(f"Failed to add source: {e}")
        raise


async def add_source_file(
    ctx: Context,
    file_path: str,
    notebook_id: Optional[str] = None,
    wait: bool = True,
) -> Dict[str, Any]:
    """
    Add a file source to a notebook.
    
    Args:
        file_path: Path to the file (PDF, text, etc.)
        notebook_id: Notebook ID (uses current if not provided)
        wait: If True, wait for source to be processed (default: True)
        
    Returns:
        Source details
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        path = Path(file_path)
        if not path.exists():
            return {
                "error": f"File not found: {file_path}",
                "status": "failed"
            }
        
        async with await client._get_client() as nl_client:
            result = await nl_client.sources.add_file(
                nb_id,
                str(path),
                wait=wait,
            )
            
            return {
                "id": result.id,
                "name": getattr(result, "title", path.name),
                "file": file_path,
                "status": "added",
            }
    except Exception as e:
        logger.error(f"Failed to add file source: {e}")
        raise


async def refresh_source(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> str:
    """
    Refresh a source.
    
    Args:
        source_id: ID of the source to refresh
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message
    """
    try:
        client = ctx.request_context.lifespan_context
        await client.refresh_source(source_id, notebook_id)
        return f"✅ Source refreshed: {source_id}"
    except Exception as e:
        logger.error(f"Failed to refresh source: {e}")
        return f"❌ Failed to refresh source: {str(e)}"


async def rename_source(
    ctx: Context,
    source_id: str,
    title: str,
    notebook_id: Optional[str] = None
) -> str:
    """
    Rename a source.
    
    Args:
        source_id: ID of the source to rename
        title: New title
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message
    """
    try:
        client = ctx.request_context.lifespan_context
        await client.rename_source(source_id, title, notebook_id)
        return f"✅ Source renamed to: {title}"
    except Exception as e:
        logger.error(f"Failed to rename source: {e}")
        return f"❌ Failed to rename source: {str(e)}"



async def delete_source(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> str:
    """
    Delete a source from a notebook.
    
    Args:
        source_id: ID of the source to delete
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        async with await client._get_client() as nl_client:
            await nl_client.sources.delete(nb_id, source_id)
            return f"✅ Source deleted: {source_id}"
    except Exception as e:
        logger.error(f"Failed to delete source: {e}")
        return f"❌ Failed to delete source: {str(e)}"


async def download_all_sources(
    ctx: Context,
    output_path: str,
    notebook_id: Optional[str] = None
) -> str:
    """
    Download text content of all sources to a directory.
    
    Args:
        output_path: Directory path where to save the files
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message with list of downloaded files or error
    """
    try:
        client = ctx.request_context.lifespan_context
        
        nb_id = notebook_id or client.current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        downloaded = await client.download_sources(output_path, nb_id)
        
        if not downloaded:
            return "⚠️ No sources downloaded (sources might be empty or content not retrievable)."
            
        return f"✅ Downloaded {len(downloaded)} sources to: {output_path}"
    except Exception as e:
        logger.error(f"Failed to download sources: {e}")
        return f"❌ Failed to download sources: {str(e)}"
