#!/usr/bin/env python3
"""
Test script for MCP NotebookLM server.
This tests the basic functionality without requiring authentication.
"""

import sys
import os

# Ensure PLAYWRIGHT_BROWSERS_PATH is set for testing
os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    "/mnt/windows/App_Wubuntu/playraightNav/ms-playwright"
)

def test_imports():
    """Test that all imports work."""
    print("🧪 Testing imports...")
    try:
        from mcp_notebooklm import mcp, config, NotebookLMClient
        from mcp_notebooklm.server import main
        from mcp_notebooklm.client import NotebookLMClient
        from mcp_notebooklm.config import Config
        from mcp_notebooklm.exceptions import (
            MCPNotebookLMError,
            AuthenticationError,
            NotebookNotFoundError,
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration."""
    print("\n🧪 Testing configuration...")
    try:
        from mcp_notebooklm.config import Config
        cfg = Config()
        
        assert cfg.base_dir.exists(), f"Base dir not found: {cfg.base_dir}"
        assert cfg.python_env_dir.exists(), f"Python env not found: {cfg.python_env_dir}"
        
        print(f"✅ Base dir: {cfg.base_dir}")
        print(f"✅ Python env: {cfg.python_env_dir}")
        print(f"✅ Playwright path: {cfg.playwright_browsers_path}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_server_loading():
    """Test server loading."""
    print("\n🧪 Testing server loading...")
    try:
        from mcp_notebooklm.server import mcp
        print(f"✅ Server name: {mcp.name}")
        print(f"✅ Server loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Server loading failed: {e}")
        return False

def test_exceptions():
    """Test custom exceptions."""
    print("\n🧪 Testing exceptions...")
    try:
        from mcp_notebooklm.exceptions import (
            MCPNotebookLMError,
            AuthenticationError,
            NotebookNotFoundError,
            PlaywrightNotConfiguredError,
        )
        
        # Test raising and catching
        try:
            raise NotebookNotFoundError("Test notebook")
        except MCPNotebookLMError as e:
            print(f"✅ Exception hierarchy works: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Exception test failed: {e}")
        return False

def test_directory_structure():
    """Test that required directories exist."""
    print("\n🧪 Testing directory structure...")
    try:
        from mcp_notebooklm.config import config
        
        # Ensure directories
        config.ensure_directories()
        
        assert config.config_dir.exists(), "Config dir not created"
        assert config.data_dir.exists(), "Data dir not created"
        assert config.logs_dir.exists(), "Logs dir not created"
        
        print(f"✅ Config dir: {config.config_dir}")
        print(f"✅ Data dir: {config.data_dir}")
        print(f"✅ Logs dir: {config.logs_dir}")
        return True
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 MCP NotebookLM - Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_server_loading,
        test_exceptions,
        test_directory_structure,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
