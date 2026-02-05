import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.mcp_notebooklm.server import mcp

async def main():
    print(f"FastMCP instance: {mcp}")
    
    # FastMCP v2 usually has list_tools()
    if hasattr(mcp, "list_tools"):
        try:
            tools = await mcp.list_tools()
            print(f"Successfully called list_tools(). Count: {len(tools)}")
            for t in tools:
                # t might be a Tool object with name attribute
                name = getattr(t, "name", str(t))
                print(f"- {name}")
        except Exception as e:
            print(f"Error calling list_tools: {e}")
            
    # Fallback: inspect _tool_registry if it exists (common in FastMCP)
    if hasattr(mcp, "_tool_registry"):
         print(f"Direct registry check: {len(mcp._tool_registry)} tools")
         
    # Fallback: inspect _tools
    if hasattr(mcp, "_tools"):
         print(f"Direct _tools check: {len(mcp._tools)}")

if __name__ == "__main__":
    asyncio.run(main())
