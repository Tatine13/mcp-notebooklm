#!/usr/bin/env python3
"""
CLI utility script for MCP NotebookLM.
Provides quick commands for common operations.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp_notebooklm.utils.helpers import check_health, get_environment_info
from mcp_notebooklm.config import config


def cmd_health(args):
    """Check system health."""
    print("🏥 Checking system health...\n")
    
    health = check_health()
    
    print(f"Overall Status: {health['status'].upper()}")
    print(f"All Healthy: {'✅ Yes' if health['all_healthy'] else '❌ No'}\n")
    
    print("Checks:")
    for check, status in health['checks'].items():
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {check}")
    
    if not health['all_healthy']:
        print("\n⚠️  Some checks failed. Run 'setup' to fix configuration.")
        return 1
    
    return 0


def cmd_env(args):
    """Show environment information."""
    print("🌍 Environment Information\n")
    
    info = get_environment_info()
    
    print(f"Python Version: {info['python_version']}")
    print(f"Python Env: {info['python_env']}")
    print(f"Base Dir: {info['base_dir']}")
    print(f"\nPlaywright:")
    print(f"  Browsers Path: {info['playwright_browsers_path'] or '❌ Not set'}")
    print(f"\nNotebookLM Config:")
    print(f"  Timeout: {info['notebooklm_timeout']}s")
    print(f"  Headless: {info['notebooklm_headless']}")


def cmd_cache(args):
    """Cache management commands."""
    from mcp_notebooklm.utils.cache import get_cache
    
    cache = get_cache()
    
    if args.clear:
        print("🧹 Clearing cache...")
        cache.clear()
        print("✅ Cache cleared")
    elif args.stats:
        print("📊 Cache Statistics\n")
        stats = cache.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif args.cleanup:
        print("🧹 Cleaning up expired entries...")
        cache.cleanup_expired()
        print("✅ Cleanup complete")
    else:
        print("📦 Cache Commands:")
        print("  --stats    Show cache statistics")
        print("  --clear    Clear all cache entries")
        print("  --cleanup  Remove expired entries")


def cmd_setup(args):
    """Setup and configure the environment."""
    print("🔧 MCP NotebookLM Setup\n")
    
    # Check directories
    print("1. Creating directories...")
    config.ensure_directories()
    print("   ✅ Directories created\n")
    
    # Check Playwright
    print("2. Checking Playwright configuration...")
    browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
    if browsers_path:
        print(f"   ✅ PLAYWRIGHT_BROWSERS_PATH set: {browsers_path}")
    else:
        print("   ❌ PLAYWRIGHT_BROWSERS_PATH not set")
        print(f"   💡 Add to ~/.bashrc:")
        print(f'      export PLAYWRIGHT_BROWSERS_PATH="{config.playwright_browsers_path}"')
    
    print("\n3. Configuration complete!")
    print("   Next steps:")
    print("   - Run 'health' to verify everything works")
    print("   - Authenticate with: notebooklm login")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP NotebookLM CLI Utilities",
        prog="mcp-notebooklm-utils"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.set_defaults(func=cmd_health)
    
    # Environment command
    env_parser = subparsers.add_parser("env", help="Show environment info")
    env_parser.set_defaults(func=cmd_env)
    
    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_parser.add_argument("--stats", action="store_true", help="Show cache stats")
    cache_parser.add_argument("--clear", action="store_true", help="Clear cache")
    cache_parser.add_argument("--cleanup", action="store_true", help="Cleanup expired entries")
    cache_parser.set_defaults(func=cmd_cache)
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup environment")
    setup_parser.set_defaults(func=cmd_setup)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
