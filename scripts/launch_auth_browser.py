
import sys
import os
import asyncio
from pathlib import Path

# Add src to path to reuse profile logic if needed, but simple is better
# We receive profile_dir as argument

async def launch_browser(profile_dir: str):
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        print(f"Launching persistent browser in: {profile_dir}")
        
        # Launch persistent context that won't close automatically
        # actually, if this script ends, browser closes. 
        # We need to keep this script running until user closes browser window manually.
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://notebooklm.google.com/")
        
        print("Browser launched. Waiting for user to close window...")
        
        # Wait for close event logic or just infinite wait
        # The user will run confirm_auth from the agent while this is open
        # But confirm_auth creates a NEW context/lock conflict?
        # NO. Chrome allows only one instance per user-data-dir usually.
        #
        # ALTERNATIVE STRATEGY:
        # confirm_auth should NOT open a new browser. It should assume the user has logged in
        # and checking tokens involves just reading cookies? No, cookies are in memory.
        # It needs to persist to disk.
        #
        # Chrome persists cookies to disk periodically or on close.
        # If confirm_auth tries to open same profile, it crashes if locked.
        #
        # SO: user must CLOSE browser manually, THEN run confirm_auth?
        # OR: We use one script that opens browser, waits for "signal" to save?
        #
        # Let's keep it simple: "Please close the browser window when done, then run confirm_auth"
        # If user closes browser, Playwright context closes, cookies are flushed to disk.
        # Then confirm_auth opens HEADLESS context to read them and save storage_state.json.
        
        try:
            # wait until all pages are closed
            while context.pages:
                await asyncio.sleep(1)
        except Exception:
            pass
            
        print("Browser closed by user. Exiting.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python launch_auth_browser.py <profile_dir>")
        sys.exit(1)
        
    asyncio.run(launch_browser(sys.argv[1]))
