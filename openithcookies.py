import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="cookies.json")
        page = await context.new_page()
        await page.goto("https://khaki-pelican-5k6d.squarespace.com/config/settings/billing/invoices")
        await page.screenshot(path="debug.png", full_page=True)
        await asyncio.sleep(15)  # gives you time to look around manually
        await browser.close()

asyncio.run(main())
