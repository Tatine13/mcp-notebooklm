# Contributing to MCP NotebookLM

Thank you for your interest in contributing! This project is an MCP server bridge for Google NotebookLM.

## 🚧 Architecture Note

Currently, this project relies on a **forked version** of `notebooklm-py` to provide critical fixes for source addition (URL, Files).
- **Upstream Library**: `teng-lin/notebooklm-py`
- **Current Fork**: `Tatine13/notebooklm-py` (branch `main`)

If you are contributing fixes to the underlying library logic, please perform them on the fork (or submit to upstream and let us know).

## 🛠️ Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Tatine13/mcp-notebooklm.git
   cd mcp-notebooklm
   ```

2. **Set up Python environment** (using uv is recommended)
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. **Install Playwright Browsers**
   ```bash
   playwright install chromium
   ```

## 🧪 Running Tests

```bash
pytest tests/
```

## 📝 Submission Guidelines

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Issue that pull request!

## 📜 License

By contributing, you agree that your contributions will be licensed under its MIT License.