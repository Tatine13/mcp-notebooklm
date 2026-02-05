# Guide for AI Assistants

This document helps AI assistants understand how to use the MCP NotebookLM tools effectively.

## Quick Reference

### Getting Started
1. `check_auth` - Verify authentication status
2. `list_profiles` - See available Google accounts
3. `list_notebooks` - List notebooks in current profile
4. `select_notebook` - Choose a notebook to work with

### Working with Sources
- `list_notebook_sources` - See all sources in a notebook
- `add_url_source` - Add a website or YouTube video
- `add_file_source` - Add a local file (PDF, text)

### Asking Questions
- `ask_question` - Get answers with citations from sources

### Content Generation
- `create_audio_overview` - Generate a podcast
- `create_quiz` - Create study quiz
- `create_flashcards` - Generate flashcards
- `generate_slides` - Create presentation

### Cross-Profile Features (Unique!)
- `list_all_notebooks` - See ALL notebooks from ALL profiles
- `search_notebooks` - Search across ALL profiles by title

## Example Workflows

### Basic Query
```
1. check_auth
2. list_notebooks
3. select_notebook(notebook_id="...")
4. ask_question(question="What is the main topic?")
```

### Multi-Profile Research
```
1. list_all_notebooks (see everything across profiles)
2. search_notebooks(query="machine learning")
3. select_notebook(notebook_id="...")
```

### Content Creation
```
1. select_notebook(notebook_id="...")
2. create_audio_overview(format_type="deep-dive")
3. download_generated_content(content_type="audio", output_path="/tmp/podcast.mp3")
```
