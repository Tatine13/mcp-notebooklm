import os
import logging
from mcp.server.fastmcp import FastMCP, Context
from notebooklm.client import NotebookLMClient

# Initialize FastMCP server
# We use the 'notebooklm' name for the server
mcp = FastMCP("notebooklm", dependencies=["notebooklm-py", "playwright"])

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("notebooklm_mcp.log")
    ]
)
logger = logging.getLogger("mcp_notebooklm")

# =============================================================================
# LIFECYCLE MANAGEMENT
# =============================================================================

@mcp.lifespan
async def lifespan_manager():
    """Manage the lifecycle of the NotebookLM client."""
    # This runs when the server starts
    logger.info("Starting NotebookLM MCP server...")
    
    # Check for required environment variables
    # We don't strictly require google creds here as they might be handled by
    # notebooklm login command or existing profiles
    
    # Initialize the client manager (a wrapper to handle profiles and connections)
    # We attach it to the context that is passed to tools
    from mcp_notebooklm.utils.client_manager import ClientManager
    client_manager = ClientManager()
    
    yield client_manager
    
    # This runs when the server stops
    logger.info("Stopping NotebookLM MCP server...")
    await client_manager.close()

# Import all tools
# This approach keeps server.py clean and delegates tool implementation to separate modules
from mcp_notebooklm.tools import (
    auth,
    notebooks,
    sources,
    chat,
    artifacts,
    profiles,
    research_tools,
    sharing,
)

# Register tools from modules
# Auth tools
mcp.tool()(auth.setup_auth)
mcp.tool()(auth.check_auth)
# Confirmation needs to be registered manually or in auth module
mcp.tool()(auth.confirm_auth)

# Profile tools
mcp.tool()(profiles.create_profile)
mcp.tool()(profiles.switch_profile)
mcp.tool()(profiles.list_profiles)
mcp.tool()(profiles.get_current_profile)
mcp.tool()(profiles.delete_profile)
mcp.tool()(profiles.update_profile)

# Notebook tools
mcp.tool()(notebooks.list_notebooks)
mcp.tool()(notebooks.list_all_notebooks)
mcp.tool()(notebooks.search_notebooks)
mcp.tool()(notebooks.select_notebook)
mcp.tool()(notebooks.create_notebook)
mcp.tool()(notebooks.rename_notebook)
mcp.tool()(notebooks.delete_notebook)
mcp.tool()(notebooks.export_notebook)
mcp.tool()(notebooks.get_notebook_info)
mcp.tool()(notebooks.get_current_notebook)

# Source tools
mcp.tool()(sources.list_notebook_sources)
mcp.tool()(sources.list_drive_sources)
mcp.tool()(sources.add_url_source)
mcp.tool()(sources.add_file_source)
mcp.tool()(sources.batch_add_sources)
mcp.tool()(sources.refresh_source)
mcp.tool()(sources.check_source_freshness)
mcp.tool()(sources.rename_source)
mcp.tool()(sources.remove_source)
mcp.tool()(sources.download_all_sources)
mcp.tool()(sources.get_source_content)
mcp.tool()(sources.get_source_guide)

# Research tools
mcp.tool()(research_tools.research_topic)
mcp.tool()(research_tools.import_research_sources)

# Chat tools
mcp.tool()(chat.ask_question)
mcp.tool()(chat.get_conversation_history)
mcp.tool()(artifacts.configure_chat)

# Artifact tools
mcp.tool()(artifacts.create_audio_overview)
mcp.tool()(artifacts.create_video_overview)
mcp.tool()(artifacts.create_quiz)
mcp.tool()(artifacts.create_flashcards)
mcp.tool()(artifacts.generate_slides)
mcp.tool()(artifacts.generate_infographic)
mcp.tool()(artifacts.generate_mind_map)
mcp.tool()(artifacts.generate_study_guide)
mcp.tool()(artifacts.generate_report)
mcp.tool()(artifacts.create_data_table)
mcp.tool()(artifacts.download_generated_content)
mcp.tool()(artifacts.list_notebook_artifacts)
mcp.tool()(artifacts.delete_notebook_artifact)
mcp.tool()(artifacts.monitor_artifact)
mcp.tool()(artifacts.manage_note)

# Sharing tools
mcp.tool()(sharing.share_with_user)
mcp.tool()(sharing.remove_share)
mcp.tool()(sharing.get_share_status)
mcp.tool()(sharing.set_public_sharing)


# Main entry point is managed by FastMCP automatically via 'mcp run server.py' or imported as module
if __name__ == "__main__":
    mcp.run()
