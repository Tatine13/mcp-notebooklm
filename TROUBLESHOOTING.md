# Troubleshooting Guide

## 🔧 Common Issues and Solutions

### 1. PLAYWRIGHT_BROWSERS_PATH Not Set

**Error:**
```
PlaywrightNotConfiguredError: PLAYWRIGHT_BROWSERS_PATH environment variable must be set
```

**Solution:**
Ensure the environment variable is passed in your MCP client configuration or set globally in your shell.

```bash
# Example in .bashrc
export PLAYWRIGHT_BROWSERS_PATH="/path/to/ms-playwright"
```

### 2. Authentication Required

**Error:**
```
AuthenticationError: Client not initialized
```

**Solution:**
The headless browser cannot log in automatically. You must run the manual login flow once:
```bash
notebooklm login
```

### 3. Module Not Found Errors

**Error:**
```
ModuleNotFoundError: No module named 'mcp_notebooklm'
```

**Solution:**
Ensure you are using the python interpreter from the virtual environment where the package is installed.
```bash
/path/to/venv/bin/python -m mcp_notebooklm
```

### 4. Connection Timeout

**Error:**
```
TimeoutError: Operation timed out after 60 seconds
```

**Solution:**
Generation tasks (Video, Audio) can be slow.
- Increase timeout via env var: `export NOTEBOOKLM_TIMEOUT=120`
- Use `monitor_artifact` to poll for completion asynchronously instead of waiting.

---

## 🧪 Diagnostic Commands

### Check System Health
```bash
python scripts/utils.py health
```

### Check Cache Status
```bash
python scripts/utils.py cache --stats
```

---

## 🐛 Debug Mode

Enable debug logging to see full request/response traces:

```bash
export MCP_NOTEBOOKLM_LOG_LEVEL=debug
export MCP_NOTEBOOKLM_DEBUG=true
```

Logs are typically written to `logs/mcp_notebooklm.log` in the project directory.

---

## 🔄 Cache Management

If you experience stale data (notebooks not appearing):

```bash
# Clear Cache
python scripts/utils.py cache --clear
```
