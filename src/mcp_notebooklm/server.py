"""MCP Server for NotebookLM."""

from typing import AsyncIterator, Optional, Tuple, List, Dict, Any
from contextlib import asynccontextmanager

from fastmcp import FastMCP, Context
from loguru import logger

from .config import config
from .client import NotebookLMClient
from .exceptions import (
    MCPNotebookLMError,
    AuthenticationError,
    NotebookNotFoundError,
    PlaywrightNotConfiguredError,
)
from .tools.notebooks import (
    list_notebooks,
    select_notebook,
    create_notebook,
    get_notebook_info,
    get_current_notebook,
    rename_notebook,
    delete_notebook,
    export_notebook,
)
from .tools.sources import (
    list_sources,
    add_source_url,
    add_source_file,
    delete_source,
    refresh_source,
    rename_source,
    download_all_sources,
)
from .tools.chat import (
    get_chat_history,
)
from .tools.artifacts import (
    generate_audio,
    generate_video,
    generate_quiz,
    generate_flashcards,
    download_artifact,
    generate_slides,
    generate_infographic,
    generate_mind_map,
    generate_study_guide,
    generate_report,
    generate_data_table,
)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[NotebookLMClient]:
    """Manage application lifecycle."""
    # Initialize on startup - don't fail if not authenticated
    client = NotebookLMClient()
    try:
        await client.initialize(raise_on_auth_error=False)
        if client.is_authenticated:
            logger.info("MCP NotebookLM server started (authenticated)")
        else:
            logger.info("MCP NotebookLM server started (not authenticated - run setup_auth)")
        yield client
    except PlaywrightNotConfiguredError as e:
        logger.error(f"Playwright not configured: {e}")
        # Still yield the client even if Playwright is not configured
        # so we can show the error message to the user
        yield client
    except Exception as e:
        logger.error(f"Server initialization error: {e}")
        # Yield client anyway so the server stays up
        yield client
    finally:
        # Cleanup on shutdown
        await client.close()
        logger.info("MCP NotebookLM server stopped")


# Initialize FastMCP server with lifespan
mcp = FastMCP("mcp-notebooklm", lifespan=app_lifespan)


def check_authenticated(ctx: Context) -> tuple[bool, Optional[str]]:
    """
    Check if client is authenticated.
    
    Returns:
        (is_authenticated, error_message)
    """
    try:
        client = ctx.request_context.lifespan_context
        if not client.is_authenticated:
            return False, (
                "🔐 Authentication required!\n\n"
                "Please authenticate by running:\n"
                "  notebooklm login\n\n"
                "Or use the setup_auth tool for more information."
            )
        return True, None
    except Exception as e:
        return False, f"Failed to check authentication: {str(e)}"


@mcp.tool()
async def setup_auth(ctx: Context, headless: bool = False) -> str:
    """
    Set up authentication with NotebookLM.
    
    Opens a browser window for Google authentication.
    1. Run this tool (browser will open)
    2. Log in to your Google account
    3. Wait for the NotebookLM homepage to load
    4. Run 'confirm_auth' tool to finalizing saving tokens.
    
    Args:
        headless: Set to true to run invisible (not recommended for initial login)
    """
    try:
        client = ctx.request_context.lifespan_context
        # We allow re-auth even if authenticated (to switch accounts or refresh)
        if client.is_authenticated:
            logger.info("Client already authenticated, but starting new login flow as requested.")
            
        msg = await client.start_login_flow(headless=headless)
        return f"🚀 {msg}"
    except Exception as e:
        logger.error(f"Auth setup failed: {e}")
        return f"❌ Authentication setup failed: {str(e)}"


@mcp.tool()
async def confirm_auth(ctx: Context) -> str:
    """
    Confirm authentication after logging in via setup_auth.
    
    Call this tool AFTER you have successfully logged in via the browser 
    opened by setup_auth.
    """
    try:
        client = ctx.request_context.lifespan_context
        msg = await client.finish_login_flow()
        return f"✅ {msg}"
    except Exception as e:
        logger.error(f"Auth confirmation failed: {e}")
        return f"❌ Authentication confirmation failed: {str(e)}"


@mcp.tool()
async def check_auth(ctx: Context) -> dict:
    """
    Check authentication status.
    
    Returns:
        Dict with authentication status and details
    """
    try:
        client = ctx.request_context.lifespan_context
        from .profiles import get_current_profile
        return {
            "authenticated": client.is_authenticated,
            "current_notebook": client.current_notebook_id,
            "current_profile": get_current_profile(),
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
        }


# ==================== Profile Management ====================

@mcp.tool()
async def list_profiles(ctx: Context) -> list:
    """
    List all available authentication profiles.
    
    Returns:
        List of profiles with name, active status, and path
    """
    from .profiles import list_profiles as _list_profiles
    return _list_profiles()


@mcp.tool()
async def get_current_profile(ctx: Context) -> dict:
    """
    Get the currently active profile.
    
    Returns:
        Dict with profile name and path
    """
    from .profiles import get_current_profile as _get_current, get_profile_dir
    name = _get_current()
    return {
        "name": name,
        "path": str(get_profile_dir(name)),
    }


@mcp.tool()
async def create_profile(name: str, ctx: Context) -> str:
    """
    Create a new authentication profile and launch browser for login.
    
    Args:
        name: Name for the new profile (e.g., 'work', 'personal')
        
    Returns:
        Status message
    """
    try:
        client = ctx.request_context.lifespan_context
        msg = await client.start_login_flow(headless=False, profile_name=name)
        return f"🚀 {msg}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error(f"Create profile failed: {e}")
        return f"❌ Failed to create profile: {str(e)}"


@mcp.tool()
async def switch_profile(name: str, ctx: Context) -> str:
    """
    Switch to a different authentication profile.
    
    Args:
        name: Profile name to switch to
        
    Returns:
        Status message
    """
    from .profiles import profile_exists, set_current_profile, get_profile_storage_path
    
    if not profile_exists(name):
        return f"❌ Profile '{name}' does not exist. Use create_profile first."
    
    storage = get_profile_storage_path(name)
    if not storage.exists():
        return f"❌ Profile '{name}' exists but is not authenticated. Run create_profile to authenticate."
    
    try:
        set_current_profile(name)
        
        # Re-initialize client with new profile
        client = ctx.request_context.lifespan_context
        await client.initialize()
        
        return f"✅ Switched to profile '{name}'. Client re-initialized."
    except Exception as e:
        logger.error(f"Switch profile failed: {e}")
        return f"❌ Failed to switch profile: {str(e)}"


@mcp.tool()
async def update_profile(name: str = None, email: str = None, display_name: str = None, description: str = None, ctx: Context = None) -> str:
    """
    Update metadata for a profile.
    
    Args:
        name: Profile name to update (defaults to current active profile if omitted)
        email: Email address associated with the profile
        display_name: Friendly name to display
        description: Short description of the profile
    
    Returns:
        Status message with updated info
    """
    from .profiles import update_profile_metadata, get_current_profile, profile_exists
    
    target_name = name or get_current_profile()
    
    if not profile_exists(target_name):
        return f"❌ Profile '{target_name}' does not exist."
        
    updates = {}
    if email is not None:
        updates["email"] = email
    if display_name is not None:
        updates["display_name"] = display_name
    if description is not None:
        updates["description"] = description
        
    if not updates:
        return f"⚠️ No updates provided for profile '{target_name}'."
        
    try:
        new_meta = update_profile_metadata(target_name, updates)
        return f"✅ Updated profile '{target_name}': {new_meta}"
    except Exception as e:
        logger.error(f"Update profile failed: {e}")
        return f"❌ Failed to update profile: {str(e)}"


@mcp.tool()
async def delete_profile(name: str, ctx: Context) -> str:
    """
    Delete an authentication profile.
    
    Args:
        name: Profile name to delete
        
    Returns:
        Status message
    """
    from .profiles import delete_profile as _delete_profile
    
    try:
        _delete_profile(name)
        return f"✅ Profile '{name}' deleted."
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error(f"Delete profile failed: {e}")
        return f"❌ Failed to delete profile: {str(e)}"


# ==================== Unified Cross-Profile Tools ====================

@mcp.tool()
async def list_all_notebooks(ctx: Context) -> list:
    """
    List notebooks from ALL profiles (unified view).
    
    Iterates through all authenticated profiles and aggregates notebooks.
    Each notebook includes a 'profile' field indicating which account it belongs to.
    
    Returns:
        List of all notebooks from all profiles
    """
    from .profiles import list_profiles as _list_profiles, get_profile_storage_path, set_current_profile, get_current_profile
    from .tools.notebooks import list_notebooks as _list_notebooks_impl
    
    original_profile = get_current_profile()
    all_notebooks = []
    
    profiles = _list_profiles()
    
    for profile in profiles:
        profile_name = profile["name"]
        storage = get_profile_storage_path(profile_name)
        
        if not storage.exists():
            # Profile not authenticated, skip
            all_notebooks.append({
                "profile": profile_name,
                "error": "Not authenticated"
            })
            continue
            
        try:
            # Switch to this profile
            set_current_profile(profile_name)
            
            # Re-initialize client for this profile
            client = ctx.request_context.lifespan_context
            await client.initialize()
            
            # Get notebooks
            notebooks = await _list_notebooks_impl(ctx)
            
            # Tag each notebook with profile
            for nb in notebooks:
                if isinstance(nb, dict):
                    nb["profile"] = profile_name
            
            all_notebooks.extend(notebooks)
            
        except Exception as e:
            logger.error(f"Failed to list notebooks for profile {profile_name}: {e}")
            all_notebooks.append({
                "profile": profile_name,
                "error": str(e)
            })
    
    # Restore original profile
    try:
        set_current_profile(original_profile)
        client = ctx.request_context.lifespan_context
        await client.initialize()
    except Exception:
        pass
    
    return all_notebooks


@mcp.tool()
async def search_notebooks(
    ctx: Context,
    query: str,
    profiles: Optional[List[str]] = None,
    min_sources: int = 0,
    sort_by: str = "recency"
) -> list:
    """
    Search for notebooks across multiple profiles.
    
    Args:
        query: Search term to match in notebook titles (case-insensitive)
        profiles: Optional list of profile names to search. If omitted, searches all profiles.
        min_sources: Minimum number of sources required (default: 0)
        sort_by: Sort order, either "recency" (default) or "title"
        
    Returns:
        List of matching notebooks with metadata (profile, owner, etc.)
    """
    from .profiles import list_profiles as _list_profiles, get_profile_storage_path, set_current_profile, get_current_profile
    from .tools.notebooks import list_notebooks as _list_notebooks_impl
    
    # Validate sort_by
    if sort_by not in ["recency", "title"]:
        return [{"error": f"Invalid sort_by value: {sort_by}. Must be 'recency' or 'title'."}]

    original_profile = get_current_profile()
    all_results = []
    
    # Determine profiles to search
    available_profiles = _list_profiles()
    target_profiles = []
    
    if profiles:
        # Filter available profiles to match requested ones
        target_names = set(profiles)
        target_profiles = [p for p in available_profiles if p["name"] in target_names]
        
        # Check for invalid profiles
        found_names = {p["name"] for p in target_profiles}
        missing = target_names - found_names
        if missing:
            all_results.append({"error": f"Profiles not found: {', '.join(missing)}"})
    else:
        target_profiles = available_profiles

    # Search loop
    query_lower = query.lower()
    
    for profile in target_profiles:
        profile_name = profile["name"]
        storage = get_profile_storage_path(profile_name)
        
        if not storage.exists():
            # Skip unauthenticated profiles silently or add warning?
            # Let's add a warning result but continue
            all_results.append({
                "profile": profile_name,
                "warning": "Profile not authenticated, skipped."
            })
            continue
            
        try:
            # Switch context
            set_current_profile(profile_name)
            
            # Re-initialize client
            client = ctx.request_context.lifespan_context
            await client.initialize()
            
            # Fetch notebooks
            notebooks = await _list_notebooks_impl(ctx)
            
            # Filter and Process
            for nb in notebooks:
                # Handle potential error dicts from list_notebooks
                if not isinstance(nb, dict) or "error" in nb:
                    continue
                    
                title = nb.get("title", "")
                sources_count = nb.get("sources_count", 0)
                
                # Apply Filters
                if query_lower not in title.lower():
                    continue
                
                if sources_count < min_sources:
                    continue
                
                # Tag with profile and add to results
                nb["profile"] = profile_name
                all_results.append(nb)
                
        except Exception as e:
            logger.error(f"Search failed for profile {profile_name}: {e}")
            all_results.append({
                "profile": profile_name,
                "error": str(e)
            })
    
    # Restore original profile
    try:
        set_current_profile(original_profile)
        client = ctx.request_context.lifespan_context
        await client.initialize()
    except Exception:
        pass
    
    # Sort Results
    # created_at is strictly expected to be ISO string or datetime, but list_notebooks returns strings usually
    # We'll try to sort safely
    
    def get_sort_key(item):
        if "error" in item or "warning" in item:
            return "" # Push errors to end/start depending on order
            
        if sort_by == "title":
            return item.get("title", "").lower()
        else: # recency
            # created_at might be string, let's rely on string comparison for ISO dates or 0
            return item.get("created_at", "") or ""

    reverse_sort = (sort_by == "recency")
    
    try:
        all_results.sort(key=get_sort_key, reverse=reverse_sort)
    except Exception as e:
        logger.warning(f"Sort failed: {e}")
    
    return all_results


@mcp.tool()
async def list_notebooks(ctx: Context) -> list:
    """
    List all available notebooks with metadata.
    
    This automatically discovers all your notebooks without needing manual URLs.
    
    Returns:
        List of notebooks with id, title, sources_count, and created_at
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return [{"error": error_msg}]
    
    from .tools.notebooks import list_notebooks as _list_notebooks
    return await _list_notebooks(ctx)


@mcp.tool()
async def select_notebook(notebook_id: str, ctx: Context) -> str:
    """
    Select a notebook as the current active notebook.
    
    Args:
        notebook_id: The ID of the notebook to select
        
    Returns:
        Confirmation message
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.notebooks import select_notebook as _select_notebook
    return await _select_notebook(ctx, notebook_id)


@mcp.tool()
async def create_notebook(title: str, ctx: Context) -> dict:
    """
    Create a new notebook.
    
    Args:
        title: Title for the new notebook
        
    Returns:
        Dict with notebook details including id and title
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.notebooks import create_notebook as _create_notebook
    return await _create_notebook(ctx, title)


@mcp.tool()
async def get_notebook_info(notebook_id: str, ctx: Context) -> dict:
    """
    Get detailed information about a specific notebook.
    
    Args:
        notebook_id: The ID of the notebook
        
    Returns:
        Dict with notebook details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.notebooks import get_notebook_info as _get_notebook_info
    return await _get_notebook_info(ctx, notebook_id)


@mcp.tool()
async def ask_question(
    question: str,
    ctx: Context,
    notebook_id: Optional[str] = None,
    citation_format: str = "inline"
) -> dict:
    """
    Ask a question to the notebook and get an answer with citations.
    
    Args:
        question: The question to ask
        notebook_id: Optional notebook ID (uses current if not provided)
        citation_format: Format for citations (inline, footnotes, json, expanded)
        
    Returns:
        Dict with answer and citations
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    try:
        client = ctx.request_context.lifespan_context
        result = await client.ask_question(
            question=question,
            notebook_id=notebook_id,
            citation_format=citation_format
        )
        return result
    except NotebookNotFoundError as e:
        return {
            "error": str(e),
            "message": "Please select a notebook first using select_notebook"
        }
    except Exception as e:
        logger.error(f"Failed to ask question: {e}")
        raise


@mcp.tool()
async def get_current_notebook(ctx: Context) -> dict:
    """
    Get the currently selected notebook.
    
    Returns:
        Dict with current notebook ID and info
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.notebooks import get_current_notebook as _get_current_notebook
    return await _get_current_notebook(ctx)


@mcp.tool()
async def rename_notebook(notebook_id: str, title: str, ctx: Context) -> dict:
    """
    Rename a notebook.
    
    Args:
        notebook_id: The ID of the notebook
        title: New title
        
    Returns:
        Dict with notebook details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.notebooks import rename_notebook as _rename_notebook
    return await _rename_notebook(ctx, notebook_id, title)


@mcp.tool()
async def delete_notebook(notebook_id: str, ctx: Context) -> str:
    """
    Delete a notebook.
    
    Args:
        notebook_id: The ID of the notebook
        
    Returns:
        Confirmation message
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.notebooks import delete_notebook as _delete_notebook
    return await _delete_notebook(ctx, notebook_id)


@mcp.tool()
async def export_notebook(notebook_id: str, ctx: Context) -> dict:
    """
    Export all data from a notebook (metadata, sources, chat history).
    
    Args:
        notebook_id: The ID of the notebook
        
    Returns:
        Dict containing all notebook data
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.notebooks import export_notebook as _export_notebook
    return await _export_notebook(ctx, notebook_id)


# ==================== Source Tools ====================

@mcp.tool()
async def list_notebook_sources(
    ctx: Context,
    notebook_id: Optional[str] = None
) -> list:
    """
    List all sources in a notebook.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        List of sources with metadata
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return [{"error": error_msg}]
    
    return await list_sources(ctx, notebook_id)


@mcp.tool()
async def add_url_source(
    ctx: Context,
    url: str,
    name: Optional[str] = None,
    notebook_id: Optional[str] = None
) -> dict:
    """
    Add a URL source to a notebook.
    
    Args:
        url: URL to add (website, YouTube, etc.)
        name: Optional name for the source
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Source details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await add_source_url(ctx, url, name, notebook_id)


@mcp.tool()
async def add_file_source(
    ctx: Context,
    file_path: str,
    name: Optional[str] = None,
    notebook_id: Optional[str] = None
) -> dict:
    """
    Add a file source to a notebook.
    
    Args:
        file_path: Path to the file (PDF, text, etc.)
        name: Optional name for the source
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Source details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await add_source_file(ctx, file_path, name, notebook_id)


@mcp.tool()
async def remove_source(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> str:
    """
    Remove a source from a notebook.
    
    Args:
        source_id: ID of the source to remove
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.sources import delete_source as _delete_source
    return await _delete_source(ctx, source_id, notebook_id)


@mcp.tool()
async def refresh_source(
    source_id: str,
    ctx: Context,
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
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.sources import refresh_source as _refresh_source
    return await _refresh_source(ctx, source_id, notebook_id)


@mcp.tool()
async def rename_source(
    source_id: str,
    title: str,
    ctx: Context,
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
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.sources import rename_source as _rename_source
    return await _rename_source(ctx, source_id, title, notebook_id)


@mcp.tool()
async def download_all_sources(
    output_path: str,
    ctx: Context,
    notebook_id: Optional[str] = None
) -> str:
    """
    Download text content of all sources to a directory.
    
    Args:
        output_path: Directory path where to save the files
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message with count of downloaded files
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    from .tools.sources import download_all_sources as _download_all_sources
    return await _download_all_sources(ctx, output_path, notebook_id)


@mcp.tool()
async def batch_add_sources(
    sources: List[Dict[str, Any]],
    ctx: Context,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add multiple sources (URL or File) in a single batch.
    
    Args:
        sources: List of source objects. Each object must have:
                 - type: "url" or "file"
                 - path: The URL or file path
                 - name: (Optional) Name/title for the source
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Summary of results
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
        
    results = {
        "success": [],
        "failed": [],
        "total": len(sources)
    }
    
    for item in sources:
        src_type = item.get("type", "").lower()
        path = item.get("path") or item.get("url")
        name = item.get("name")
        
        if not path:
            results["failed"].append({"item": item, "error": "Missing path/url"})
            continue
            
        try:
            res = None
            if src_type == "url":
                res = await add_source_url(ctx, path, name, notebook_id=notebook_id)
            elif src_type == "file":
                res = await add_file_source(ctx, path, name, notebook_id=notebook_id)
            else:
                results["failed"].append({"item": item, "error": f"Unknown type: {src_type}"})
                continue
                
            if isinstance(res, dict) and "error" in res:
                results["failed"].append({"item": item, "error": res["error"]})
            else:
                results["success"].append(res)
                
        except Exception as e:
            results["failed"].append({"item": item, "error": str(e)})
            
    return results


# ==================== Chat Tools ====================

@mcp.tool()
async def get_conversation_history(
    ctx: Context,
    notebook_id: Optional[str] = None,
    limit: int = 50
) -> list:
    """
    Get chat conversation history for a notebook.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        limit: Maximum number of messages to return (default: 50)
        
    Returns:
        List of chat messages
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return [{"error": error_msg}]
    
    return await get_chat_history(ctx, notebook_id, limit)


# Note: clear_conversation removed - API notebooklm-py does not support clearing chat history server-side

# ==================== Generation Tools ====================

@mcp.tool()
async def create_audio_overview(
    ctx: Context,
    instructions: str = "",
    format_type: str = "deep-dive",
    length: str = "medium",
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Create an audio overview (podcast) from notebook sources.
    
    Args:
        instructions: Custom instructions for the audio (e.g., "make it engaging")
        format_type: Audio format (deep-dive, brief, critique, debate)
        length: Audio length (short, medium, long)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await generate_audio(ctx, instructions, format_type, length, notebook_id)


@mcp.tool()
async def create_video_overview(
    ctx: Context,
    format_type: str = "detailed",
    style: str = "classic",
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Create a video overview from notebook sources.
    
    Args:
        format_type: Video format (detailed, brief)
        style: Visual style (classic, whiteboard, kawaii, anime, etc.)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await generate_video(ctx, format_type, style, notebook_id)


@mcp.tool()
async def generate_slides(
    ctx: Context,
    length: str = "medium",
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Generate a slide deck from notebook sources.
    
    Args:
        length: Length of the presentation (short, medium, long)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.artifacts import generate_slides as _generate_slides
    return await _generate_slides(ctx, notebook_id, length)


@mcp.tool()
async def create_quiz(
    ctx: Context,
    quantity: str = "medium",
    difficulty: str = "medium",
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Create a quiz from notebook sources.
    
    Args:
        quantity: Number of questions (few, medium, many)
        difficulty: Difficulty level (easy, medium, hard)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await generate_quiz(ctx, quantity, difficulty, notebook_id)


@mcp.tool()
async def create_flashcards(
    ctx: Context,
    quantity: str = "medium",
    difficulty: str = "medium",
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Create flashcards from notebook sources.
    
    Args:
        quantity: Number of flashcards (few, medium, many)
        difficulty: Difficulty level (easy, medium, hard)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    return await generate_flashcards(ctx, quantity, difficulty, notebook_id)


@mcp.tool()
async def generate_infographic(
    ctx: Context,
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Generate an infographic from notebook sources.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.artifacts import generate_infographic as _generate_infographic
    return await _generate_infographic(ctx, notebook_id)


@mcp.tool()
async def generate_mind_map(
    ctx: Context,
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Generate a mind map from notebook sources.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.artifacts import generate_mind_map as _generate_mind_map
    return await _generate_mind_map(ctx, notebook_id)


@mcp.tool()
async def generate_study_guide(
    ctx: Context,
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Generate a study guide from notebook sources.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.artifacts import generate_study_guide as _generate_study_guide
    return await _generate_study_guide(ctx, notebook_id)


@mcp.tool()
async def generate_report(
    instructions: str,
    ctx: Context,
    notebook_id: Optional[str] = None,
) -> dict:
    """
    Generate a report from notebook sources.
    
    Args:
        instructions: Instructions for the report (e.g. topic, style, focus)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and task details
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
    
    from .tools.artifacts import generate_report as _generate_report
    return await _generate_report(ctx, instructions, notebook_id)


@mcp.tool()
async def download_generated_content(
    ctx: Context,
    content_type: str,
    output_path: str,
    notebook_id: Optional[str] = None,
    output_format: Optional[str] = None,
) -> str:
    """
    Download generated content (audio, video, quiz, flashcards, etc.).
    
    Args:
        content_type: Type of content (audio, video, quiz, flashcards)
        output_path: Path where to save the file
        notebook_id: Notebook ID (uses current if not provided)
        output_format: Output format for non-media files (json, markdown, html)
        
    Returns:
        Path to downloaded file or error message
    """
    # Check authentication
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return error_msg
    
    return await download_artifact(ctx, content_type, output_path, notebook_id, output_format)


def main():
    """Run the MCP server."""
    # Ensure directories exist
    config.ensure_directories()
    
    # Configure logging
    logger.add(
        config.logs_dir / "mcp_notebooklm.log",
        rotation="10 MB",
        retention="7 days",
        level=config.mcp_log_level.upper()
    )
    
    # Run the server
    mcp.run(transport=config.mcp_transport)


if __name__ == "__main__":
    main()

@mcp.tool()
async def research_topic(
    ctx: Context,
    query: str,
    notebook_id: Optional[str] = None,
    source: str = "web",
    mode: str = "deep",
    auto_import: bool = False,
    max_sources: int = 5
) -> Dict[str, Any]:
    """
    Perform a Deep or Fast research on a topic (Web or Drive) and optionally import sources.
    
    Args:
        query: Similar to a search query or research topic.
        notebook_id: Optional notebook ID. Uses current if omitted.
        source: 'web' (default) or 'drive'.
        mode: 'deep' (default, web only) or 'fast'. Drive research mandates 'fast'.
        auto_import: If True, automatically imports the top found sources.
        max_sources: Max sources to import if auto_import is True.
        
    Returns:
        Research results with summary and sources, and import status.
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
        
    # Validation
    if source.lower() == "drive" and mode.lower() == "deep":
        return {"error": "Deep Research is not available for Drive sources. Please use mode='fast'."}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Provide notebook_id or select one first."}

    try:
        # 1. Start Research
        task_data = None
        async with await client._get_client() as c:
             task_data = await c.research.start(nb_id, query, source=source, mode=mode)
             
        if not task_data:
            return {"error": "Failed to start research task."}
            
        task_id = task_data["task_id"]
        
        # 2. Poll for Results
        # Polling loop with timeout
        import asyncio
        start_time = asyncio.get_event_loop().time()
        # Timeout adjustment based on mode
        timeout = 300 if mode == "deep" else 60  # Drive/Fast is faster
        
        result = None
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return {"error": "Research timed out."}
            
            async with await client._get_client() as c:
                result = await c.research.poll(nb_id)
                
            status = result.get("status")
            
            if status == "completed":
                break
            
            await asyncio.sleep(2)
            
        # 3. Process Results
        sources = result.get("sources", [])
        summary = result.get("summary", "")
        
        response = {
            "query": query,
            "source": source,
            "mode": mode,
            "summary": summary,
            "sources_found": len(sources),
            "sources": sources,
            "imported_sources": []
        }
        
        # 4. Auto Import
        if auto_import and sources:
            to_import = sources[:max_sources]
            async with await client._get_client() as c:
                imported = await c.research.import_sources(nb_id, task_id, to_import)
            response["imported_sources"] = imported
            
        return response

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return {"error": str(e)}

@mcp.tool()
async def import_research_sources(
    ctx: Context,
    task_id: str,
    sources: List[Dict[str, str]],
    notebook_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Import sources discovered by a previous research task.
    
    Args:
        task_id: The research task ID returned by research_topic.
        sources: List of source objects (must contain 'url', optional 'title').
        notebook_id: Optional notebook ID. Uses current if omitted.
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return [{"error": error_msg}]

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return [{"error": "No notebook selected."}]
        
    try:
        async with await client._get_client() as c:
            return await c.research.import_sources(nb_id, task_id, sources)
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return [{"error": str(e)}]


# =============================================================================
# SHARING TOOLS
# =============================================================================

@mcp.tool()
async def get_share_status(
    ctx: Context,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get current sharing settings and collaborators.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        is_public, access_level, collaborators list, and public_link if public
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            status = await c.sharing.get_status(nb_id)
            return {
                "notebook_id": nb_id,
                "is_public": status.is_public,
                "access": status.access.name if status.access else "UNKNOWN",
                "view_level": status.view_level.name if status.view_level else "UNKNOWN",
                "share_url": status.share_url,
                "shared_users": [
                    {
                        "email": u.email,
                        "permission": u.permission.name if u.permission else "UNKNOWN",
                    }
                    for u in (status.shared_users or [])
                ],
                "user_count": len(status.shared_users or []),
            }
    except Exception as e:
        logger.error(f"Get share status failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def set_public_sharing(
    ctx: Context,
    is_public: bool = True,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enable or disable public link access.
    
    Args:
        is_public: True to enable public link, False to disable (default: True)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        public_link if enabled, confirmation if disabled
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            status = await c.sharing.set_public(nb_id, is_public)
            if is_public:
                return {
                    "status": "success",
                    "is_public": True,
                    "share_url": status.share_url,
                    "message": "Public link access enabled.",
                }
            else:
                return {
                    "status": "success",
                    "is_public": False,
                    "message": "Public link access disabled.",
                }
    except Exception as e:
        logger.error(f"Set public sharing failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def share_with_user(
    ctx: Context,
    email: str,
    permission: str = "viewer",
    notify: bool = True,
    message: str = "",
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Share notebook with a user by email.
    
    Args:
        email: Email address to invite
        permission: "viewer" or "editor" (default: viewer)
        notify: Send email notification (default: True)
        message: Optional welcome message
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Success status
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    # Map string to enum
    from notebooklm.rpc.types import SharePermission
    perm_map = {
        "viewer": SharePermission.VIEWER,
        "editor": SharePermission.EDITOR,
    }
    perm = perm_map.get(permission.lower())
    if not perm:
        return {"error": f"Invalid permission '{permission}'. Use: viewer, editor"}
        
    try:
        async with await client._get_client() as c:
            await c.sharing.add_user(nb_id, email, perm, notify=notify, welcome_message=message)
            return {
                "status": "success",
                "email": email,
                "permission": permission,
                "notified": notify,
                "message": f"Invited {email} as {permission}.",
            }
    except Exception as e:
        logger.error(f"Share with user failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def remove_share(
    ctx: Context,
    email: str,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Remove a user's access to the notebook.
    
    Args:
        email: Email address to remove
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Confirmation message
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            await c.sharing.remove_user(nb_id, email)
            return {
                "status": "success",
                "email": email,
                "message": f"Removed {email}'s access to the notebook.",
            }
    except Exception as e:
        logger.error(f"Remove share failed: {e}")
        return {"error": str(e)}


# =============================================================================
# NOTES TOOLS
# =============================================================================

@mcp.tool()
async def manage_note(
    ctx: Context,
    action: str,
    note_id: Optional[str] = None,
    content: Optional[str] = None,
    title: Optional[str] = None,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage notes in a notebook (list, create, update, delete).
    
    Args:
        action: Operation to perform: list, create, get, update, delete
        note_id: Note ID (required for get/update/delete)
        content: Note content (required for create, optional for update)
        title: Note title (optional for create/update)
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Action-specific response with status
        
    Examples:
        manage_note(action="list")
        manage_note(action="create", title="My Note", content="Content here")
        manage_note(action="update", note_id="xyz", content="Updated content")
        manage_note(action="delete", note_id="xyz")
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    valid_actions = ["list", "create", "get", "update", "delete"]
    if action not in valid_actions:
        return {"error": f"Unknown action '{action}'. Valid: {', '.join(valid_actions)}"}
        
    try:
        async with await client._get_client() as c:
            if action == "list":
                notes = await c.notes.list(nb_id)
                return {
                    "action": "list",
                    "notes": [
                        {"id": n.id, "title": n.title, "content_preview": n.content[:100] if n.content else ""}
                        for n in notes
                    ],
                    "count": len(notes),
                }
                
            elif action == "create":
                if not content:
                    return {"error": "content is required for action='create'"}
                note = await c.notes.create(nb_id, title or "New Note", content)
                return {
                    "action": "create",
                    "note_id": note.id,
                    "title": note.title,
                    "content_preview": content[:100] if len(content) > 100 else content,
                }
                
            elif action == "get":
                if not note_id:
                    return {"error": "note_id is required for action='get'"}
                note = await c.notes.get(nb_id, note_id)
                if not note:
                    return {"error": f"Note {note_id} not found"}
                return {
                    "action": "get",
                    "note_id": note.id,
                    "title": note.title,
                    "content": note.content,
                }
                
            elif action == "update":
                if not note_id:
                    return {"error": "note_id is required for action='update'"}
                if content is None and title is None:
                    return {"error": "Must provide content or title to update"}
                existing = await c.notes.get(nb_id, note_id)
                if not existing:
                    return {"error": f"Note {note_id} not found"}
                await c.notes.update(
                    nb_id, 
                    note_id, 
                    content if content is not None else existing.content,
                    title if title is not None else existing.title
                )
                return {
                    "action": "update",
                    "note_id": note_id,
                    "updated": True,
                }
                
            elif action == "delete":
                if not note_id:
                    return {"error": "note_id is required for action='delete'"}
                await c.notes.delete(nb_id, note_id)
                return {
                    "action": "delete",
                    "note_id": note_id,
                    "message": f"Note {note_id} has been deleted.",
                }
                
    except Exception as e:
        logger.error(f"Note operation failed: {e}")
        return {"error": str(e)}


# =============================================================================
# ENHANCED SOURCE TOOLS
# =============================================================================

@mcp.tool()
async def get_source_guide(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get AI-generated summary and keywords for a specific source.
    
    Args:
        source_id: Source ID to get guide for
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        summary: AI-generated summary with **bold** keywords (markdown)
        keywords: List of topic keyword strings
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            guide = await c.sources.get_guide(nb_id, source_id)
            return {
                "source_id": source_id,
                "summary": guide.get("summary", ""),
                "keywords": guide.get("keywords", []),
            }
    except Exception as e:
        logger.error(f"Get source guide failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_source_content(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the full indexed text content of a source.
    
    Args:
        source_id: Source ID to get content for
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        title, source_type, url, content, char_count
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            fulltext = await c.sources.get_fulltext(nb_id, source_id)
            return {
                "source_id": source_id,
                "title": fulltext.title,
                "source_type": fulltext.source_type,
                "url": fulltext.url,
                "content": fulltext.content,
                "char_count": fulltext.char_count,
            }
    except Exception as e:
        logger.error(f"Get source content failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def check_source_freshness(
    ctx: Context,
    source_id: str,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if a source needs to be refreshed.
    
    Args:
        source_id: Source ID to check
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        is_fresh: True if source is up-to-date, False if it needs refresh
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            is_fresh = await c.sources.check_freshness(nb_id, source_id)
            return {
                "source_id": source_id,
                "is_fresh": is_fresh,
                "needs_refresh": not is_fresh,
                "message": "Source is up-to-date." if is_fresh else "Source needs refresh. Use refresh_source to update.",
            }
    except Exception as e:
        logger.error(f"Check source freshness failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_drive_sources(
    ctx: Context,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    List sources with types and Drive freshness status.
    
    Args:
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        drive_sources: List of Drive-linked sources with freshness
        other_sources: List of other source types
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}

    client = ctx.request_context.lifespan_context
    nb_id = notebook_id or client.current_notebook_id
    
    if not nb_id:
        return {"error": "No notebook selected. Use select_notebook first."}
        
    try:
        async with await client._get_client() as c:
            sources = await c.sources.list(nb_id)
            
            drive_sources = []
            other_sources = []
            
            for source in sources:
                source_info = {
                    "id": source.id,
                    "title": source.title,
                    "type": source.source_type,
                    "status": source.status,
                }
                
                # Check if it's a Drive source (type codes 1 or 2 are Google Docs/Other)
                if source._type_code in (1, 2):
                    try:
                        is_fresh = await c.sources.check_freshness(nb_id, source.id)
                        source_info["is_fresh"] = is_fresh
                        source_info["stale"] = not is_fresh
                    except Exception:
                        source_info["stale"] = None
                    drive_sources.append(source_info)
                else:
                    other_sources.append(source_info)
                    
            return {
                "notebook_id": nb_id,
                "drive_sources": drive_sources,
                "other_sources": other_sources,
                "drive_count": len(drive_sources),
                "stale_count": sum(1 for s in drive_sources if s.get("stale")),
            }
    except Exception as e:
        logger.error(f"List drive sources failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_data_table(
    ctx: Context,
    instructions: str,
    notebook_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a data table from notebook sources.
    
    Args:
        instructions: Description of the desired table structure and content
        notebook_id: Notebook ID (uses current if not provided)
        
    Returns:
        Generation status and details
    """
    is_auth, error_msg = check_authenticated(ctx)
    if not is_auth:
        return {"error": error_msg}
        
    return await generate_data_table(ctx, instructions, notebook_id)
