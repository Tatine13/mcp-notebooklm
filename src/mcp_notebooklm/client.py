"""Client wrapper for notebooklm-py."""

import os
import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from loguru import logger

from .config import config
from .exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    PlaywrightNotConfiguredError,
)


class NotebookLMClient:
    """Wrapper client for notebooklm-py library."""
    
    def __init__(self):
        self._client_class = None
        self._authenticated = False
        self._current_notebook_id: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self, raise_on_auth_error: bool = True) -> None:
        """Initialize the client with authentication check.
        
        Args:
            raise_on_auth_error: If False, don't raise exception on auth failure
                                 (allows server to start without auth)
        """
        # Check PLAYWRIGHT_BROWSERS_PATH
        browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
        if not browsers_path:
            error_msg = (
                "PLAYWRIGHT_BROWSERS_PATH environment variable must be set. "
                f"Expected: {config.playwright_browsers_path}"
            )
            if raise_on_auth_error:
                raise PlaywrightNotConfiguredError(error_msg)
            else:
                logger.warning(error_msg)
                return
        
        # Import notebooklm-py here to avoid import issues
        try:
            from notebooklm import NotebookLMClient as NLClient
            # Store the client class and create context manager on demand
            self._client_class = NLClient
            self._authenticated = True
            logger.info("NotebookLM client initialized successfully")
            
            # Restore current notebook from cache
            try:
                from .utils.cache import get_cache
                cache = get_cache()
                cached_id = cache.get("current_notebook_id")
                if cached_id:
                    self._current_notebook_id = cached_id
                    logger.info(f"Restored current notebook from cache: {cached_id}")
            except Exception as e:
                logger.warning(f"Failed to restore notebook selection: {e}")
        except Exception as e:
            logger.warning(f"NotebookLM client not authenticated: {e}")
            self._authenticated = False
            self._client_class = None
            if raise_on_auth_error:
                raise AuthenticationError(f"Authentication required: {e}")
    
    async def _get_client(self):
        """Get an initialized client using async context manager."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        # Determine correct storage path based on current profile
        from .profiles import get_current_profile, get_profile_storage_path
        
        current_profile = get_current_profile()
        storage_path = get_profile_storage_path(current_profile)
        
        # Check if profile has storage, otherwise fallback or error
        if not storage_path.exists() and current_profile != "default":
             logger.warning(f"Storage not found for profile {current_profile}, trying default")
             # Fallback logic or just let it fail naturally
        
        # Create and return client from storage path
        # Assuming from_storage accepts path, or we load it manually
        # Note: notebooklm-py's from_storage takes 'storage_path' arg usually
        try:
            return await self._client_class.from_storage(path=str(storage_path))
        except TypeError:
            # Fallback if argument not supported (should not happen with recent versions)
            logger.warning("from_storage() does not support path arg, using default")
            return await self._client_class.from_storage()
    
    async def close(self) -> None:
        """Close the client connection."""
        self._client_class = None
        self._authenticated = False
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._authenticated and self._client_class is not None
    
    @property
    def current_notebook_id(self) -> Optional[str]:
        """Get current notebook ID."""
        return self._current_notebook_id
    
    def set_notebook(self, notebook_id: str) -> None:
        """Set the current notebook ID."""
        self._current_notebook_id = notebook_id
        
        # Persist to cache (24h TTL)
        try:
            from .utils.cache import get_cache
            cache = get_cache()
            cache.set("current_notebook_id", notebook_id, ttl=86400)
            logger.info(f"Current notebook set to: {notebook_id} (persisted)")
        except Exception as e:
            logger.warning(f"Failed to persist notebook selection: {e}")
    
    # ==================== Notebook Operations ====================
    
    async def list_notebooks(self) -> List[Dict[str, Any]]:
        """List all notebooks with metadata."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            async with await self._get_client() as client:
                notebooks = await client.notebooks.list()
                return [
                    {
                        "id": nb.id,
                        "title": nb.title,
                        "sources_count": getattr(nb, "sources_count", 0),
                        "created_at": getattr(nb, "created_at", None),
                    }
                    for nb in notebooks
                ]
        except Exception as e:
            logger.error(f"Failed to list notebooks: {e}")
            raise
    
    async def create_notebook(self, title: str) -> Dict[str, Any]:
        """Create a new notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            async with await self._get_client() as client:
                notebook = await client.notebooks.create(title)
                return {
                    "id": notebook.id,
                    "title": notebook.title,
                    "created_at": getattr(notebook, "created_at", None),
                }
        except Exception as e:
            logger.error(f"Failed to create notebook: {e}")
            raise
    
    async def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            async with await self._get_client() as client:
                await client.notebooks.delete(notebook_id)
                return True
        except Exception as e:
            logger.error(f"Failed to delete notebook {notebook_id}: {e}")
            raise
    
    async def get_notebook_info(self, notebook_id: str) -> Dict[str, Any]:
        """Get detailed information about a notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            async with await self._get_client() as client:
                notebook = await client.notebooks.get(notebook_id)
                return {
                    "id": notebook.id,
                    "title": notebook.title,
                    "sources_count": getattr(notebook, "sources_count", 0),
                    "created_at": getattr(notebook, "created_at", None),
                }
        except Exception as e:
            logger.error(f"Failed to get notebook info {notebook_id}: {e}")
            raise NotebookNotFoundError(f"Notebook not found: {notebook_id}")

    async def export_notebook(self, notebook_id: str) -> Dict[str, Any]:
        """Export notebook data (metadata, sources, chat history)."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            # 1. Get info
            info = await self.get_notebook_info(notebook_id)
            
            # 2. Get sources
            async with await self._get_client() as client:
                sources = await client.sources.list(notebook_id)
                source_list = [
                    {
                        "id": getattr(s, "id", "unknown"),
                        "title": getattr(s, "title", getattr(s, "name", "unknown")),
                        "type": getattr(s, "type", "unknown"),
                        "source": str(getattr(s, "source", "")), 
                    }
                    for s in sources
                ]
                
            # 3. Get chat history (uses client wrapper method)
            chat_list = await self.get_chat_history(notebook_id)
                
            return {
                "metadata": info,
                "sources": source_list,
                "chat_history": chat_list,
                "exported_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to export notebook {notebook_id}: {e}")
            raise

    async def rename_notebook(self, notebook_id: str, title: str) -> Dict[str, Any]:
        """Rename a notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        try:
            async with await self._get_client() as client:
                notebook = await client.notebooks.rename(notebook_id, title)
                return {
                    "id": notebook.id,
                    "title": notebook.title,
                    "created_at": getattr(notebook, "created_at", None),
                }
        except Exception as e:
            logger.error(f"Failed to rename notebook {notebook_id}: {e}")
            raise
    
    # ==================== Source Operations ====================
    
    async def refresh_source(self, source_id: str, notebook_id: Optional[str] = None) -> bool:
        """Refresh a source."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                await client.sources.refresh(nb_id, source_id)
                return True
        except Exception as e:
            logger.error(f"Failed to refresh source {source_id}: {e}")
            raise

    async def rename_source(self, source_id: str, title: str, notebook_id: Optional[str] = None) -> bool:
        """Rename a source."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                await client.sources.rename(nb_id, source_id, title)
                return True
        except Exception as e:
            logger.error(f"Failed to rename source {source_id}: {e}")
            raise
    
    # ==================== Artifact Operations ====================
    
    async def generate_slides(self, notebook_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a slide deck."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                task = await client.artifacts.generate_slide_deck(nb_id, **kwargs)
                return {
                    "task_id": getattr(task, "id", "unknown"),
                    "status": "started",
                    "type": "slide_deck"
                }
        except Exception as e:
            logger.error(f"Failed to generate slides: {e}")
            raise

    async def generate_infographic(self, notebook_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate an infographic."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                task = await client.artifacts.generate_infographic(nb_id, **kwargs)
                return {
                    "task_id": getattr(task, "id", "unknown"),
                    "status": "started",
                    "type": "infographic"
                }
        except Exception as e:
            logger.error(f"Failed to generate infographic: {e}")
            raise

    async def generate_mind_map(self, notebook_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a mind map."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                task = await client.artifacts.generate_mind_map(nb_id, **kwargs)
                return {
                    "task_id": getattr(task, "id", "unknown"),
                    "status": "started",
                    "type": "mind_map"
                }
        except Exception as e:
            logger.error(f"Failed to generate mind map: {e}")
            raise

    async def generate_study_guide(self, notebook_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a study guide."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            async with await self._get_client() as client:
                task = await client.artifacts.generate_study_guide(nb_id, **kwargs)
                return {
                    "task_id": getattr(task, "id", "unknown"),
                    "status": "started",
                    "type": "study_guide"
                }
        except Exception as e:
            logger.error(f"Failed to generate study guide: {e}")
            raise

    async def generate_report(self, instructions: str, notebook_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a report."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            # Signature: (notebook_id, report_format=..., source_ids=..., language=..., custom_prompt=...)
            async with await self._get_client() as client:
                task = await client.artifacts.generate_report(
                    nb_id, 
                    custom_prompt=instructions, 
                    **kwargs
                )
                return {
                    "task_id": getattr(task, "id", "unknown"),
                    "status": "started",
                    "type": "report"
                }
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    async def download_sources(self, output_dir: str, notebook_id: Optional[str] = None) -> List[str]:
        """Download text content of all sources to a directory."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
            
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
            
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            downloaded_files = []

            async with await self._get_client() as client:
                sources = await client.sources.list(nb_id)
                for source in sources:
                    try:
                        # Try to get full text content
                        fulltext_obj = await client.sources.get_fulltext(nb_id, source.id)
                        content = getattr(fulltext_obj, "content", None)
                        
                        if content:
                            title = getattr(source, "title", source.id)
                            # Sanitize filename
                            filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                            filename = filename or source.id
                            file_path = output_path / f"{filename}.txt"
                            
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            
                            downloaded_files.append(str(file_path))
                    except Exception as s_e:
                        logger.warning(f"Failed to download source {source.id}: {s_e}")
                        continue
                        
            return downloaded_files
        except Exception as e:
            logger.error(f"Failed to download sources: {e}")
            raise
    
    async def ask_question(
        self, 
        question: str, 
        notebook_id: Optional[str] = None,
        citation_format: str = "inline"
    ) -> Dict[str, Any]:
        """Ask a question to the notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        try:
            async with await self._get_client() as client:
                result = await client.chat.ask(nb_id, question)
                return {
                    "answer": result.answer,
                    "citations": getattr(result, "citations", []),
                    "sources": getattr(result, "sources", []),
                }
        except Exception as e:
            logger.error(f"Failed to ask question: {e}")
            raise
    
    async def get_chat_history(self, notebook_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get chat history for a notebook."""
        if not self._client_class:
            raise AuthenticationError("Client not initialized")
        
        nb_id = notebook_id or self._current_notebook_id
        if not nb_id:
            raise NotebookNotFoundError("No notebook selected")
        
        try:
            async with await self._get_client() as client:
                history = await client.chat.get_history(nb_id)
                messages = []
                for msg in history:
                    # Debug logging
                    logger.debug(f"Chat message type: {type(msg)}")
                    try:
                        logger.debug(f"Chat message attrs: {dir(msg)}")
                    except:
                        pass
                        
                    # Extract fields with fallbacks
                    q = getattr(msg, "question", "") or getattr(msg, "user_message", "") or ""
                    a = getattr(msg, "answer", "") or getattr(msg, "model_message", "") or getattr(msg, "text", "") or ""
                    
                    messages.append({
                        "question": q,
                        "answer": a,
                        "timestamp": getattr(msg, "timestamp", None),
                        "citations": getattr(msg, "citations", []),
                    })
                return messages
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            raise

    # ==================== Interactive Auth Flow ====================

    async def start_login_flow(self, headless: bool = False, profile_name: str = None) -> str:
        """Start interactive login flow by opening a detached browser.
        
        Args:
            headless: Ignored (always False for detached auth)
            profile_name: Profile name to authenticate (creates if doesn't exist)
            
        Returns:
            Instructions for user.
        """
        try:
            from .profiles import (
                get_profile_browser_dir, 
                get_current_profile,
                create_profile,
                profile_exists,
            )
            import subprocess
            import sys
            
            # Determine profile
            if profile_name is None:
                profile_name = get_current_profile()
            
            # Create profile if needed
            if not profile_exists(profile_name):
                create_profile(profile_name)
            
            # Store name for finish_login_flow
            self._auth_profile_name = profile_name
            
            browser_dir = str(get_profile_browser_dir(profile_name))
            
            root_dir = Path(__file__).parent.parent.parent
            script_path = root_dir / "scripts" / "launch_auth_browser.py"
            
            if not script_path.exists():
                logger.error(f"Auth script not found at {script_path}")
                raise FileNotFoundError("Auth launcher script missing")

            # Launch detached process
            subprocess.Popen(
                [sys.executable, str(script_path), browser_dir],
                start_new_session=True, # Detach from parent
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return (
                f"🚀 Browser launched for profile '{profile_name}'.\n"
                "1. Log in to Google NotebookLM.\n"
                "2. CLOSE the browser window when done (Important! Forces save).\n"
                "3. Run 'confirm_auth' tool."
            )
            
        except Exception as e:
            logger.error(f"Failed to start login flow: {e}")
            raise

    async def _extract_user_email(self, page) -> Optional[str]:
        """Attempt to extract user email from Google Account avatar."""
        try:
            # Common selectors for Google Account button/avatar
            selectors = [
                "a[aria-label*='Google Account']",
                "a[aria-label*='Compte Google']",
                "img.gb_A",
                "div[aria-label*='Google Account']",
                "div[aria-label*='Compte Google']"
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        label = await element.get_attribute("aria-label")
                        if label:
                            # Extract email from format "Name  (email@gmail.com)" or similar
                            import re
                            match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', label)
                            if match:
                                return match.group(0)
                except:
                    continue
            return None
        except Exception as e:
            logger.warning(f"Failed to extract email: {e}")
            return None

    async def finish_login_flow(self) -> str:
        """Finish login flow by extracting tokens from the now-closed browser profile."""
        try:
            from playwright.async_api import async_playwright
            from .profiles import (
                get_profile_browser_dir,
                get_profile_storage_path, 
                set_current_profile,
                get_current_profile,
            )
            
            profile_name = getattr(self, "_auth_profile_name", get_current_profile())
            if not profile_name:
                profile_name = "default"
                
            browser_dir = get_profile_browser_dir(profile_name)
            
            # Launch HEADLESS to start session from persisted data and dump tokens
            async with async_playwright() as p:
                try:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=str(browser_dir),
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled"]
                    )
                except Exception as e:
                    return f"❌ Could not open browser profile. Is the window still open? Please close it first. Error: {e}"

                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    await page.goto("https://notebooklm.google.com/")
                    await page.wait_for_load_state("networkidle")
                    
                    # Try to extract email (for metadata, not renaming anymore per user request)
                    email = await self._extract_user_email(page)
                    
                    # Save tokens
                    storage_path = get_profile_storage_path(profile_name)
                    storage_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    
                    await context.storage_state(path=str(storage_path))
                    os.chmod(storage_path, 0o600)
                    
                    await context.close()
                    
                    # Update metadata if email found
                    if email:
                        from .profiles import update_profile_metadata
                        update_profile_metadata(profile_name, {"email": email})

                except Exception as inner_e:
                    await context.close()
                    raise inner_e
            
            # Finalize
            set_current_profile(profile_name)
            self._auth_profile_name = None
            await self.initialize()
            
            msg = f"✅ Authentication successful for '{profile_name}'! Tokens saved."
            if email:
                msg += f" (Detected email: {email})"
            return msg
            
        except Exception as e:
            logger.error(f"Finish login failed: {e}")
            raise
