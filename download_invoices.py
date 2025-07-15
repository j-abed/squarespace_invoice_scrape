import asyncio, os, csv
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

import extract_invoice_data

# ── Load env vars ────────────────────────────────────────────────────
load_dotenv()
SITE_SLUG      = os.getenv("SS_SITE_SLUG")
STORAGE_PATH   = os.getenv("SS_STORAGE_PATH")      # full_storage.json
if not SITE_SLUG or not STORAGE_PATH:
    raise RuntimeError("Set SS_SITE_SLUG and SS_STORAGE_PATH in .env or env vars")

# ── Selectors ────────────────────────────────────────────────────────
ROW_SEL    = 'button[data-test$="invoice-container"]'
DETAIL_SEL = 'div[data-test="invoice-content"]'
PRINT_BTN  = 'button:has-text("PRINT")'             # label is all‑caps in UI

# ── Output paths ─────────────────────────────────────────────────────
DEST_DIR = Path("invoices"); DEST_DIR.mkdir(exist_ok=True)
CSV_PATH = DEST_DIR / "index.csv"

def csv_row_exists(inv_id: str) -> bool:
    if not CSV_PATH.exists():
        return False
    with CSV_PATH.open() as f:
        return any(r["InvoiceID"] == inv_id for r in csv.DictReader(f))

def csv_append(date_iso, inv_id, amount, fname):
    header = ["InvoiceDate", "InvoiceID", "AmountUSD", "FileName"]
    write_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerow([date_iso, inv_id, amount, fname])

async def scroll_until_loaded(page):
    while True:
        prev = await page.locator(ROW_SEL).count()
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(600)
        if await page.locator(ROW_SEL).count() == prev:
            break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(storage_state=STORAGE_PATH)
        page    = await ctx.new_page()

        list_url = f"https://{SITE_SLUG}.squarespace.com/config/settings/billing/invoices"
        await page.goto(list_url, wait_until="networkidle")
        await scroll_until_loaded(page)

        rows  = page.locator(ROW_SEL)
        total = await rows.count()
        print(f"Found {total} invoices")

        for idx in range(total):
            row   = rows.nth(idx)
            text  = (await row.inner_text()).strip().splitlines()
            date_txt, amount_line, id_line = text[0], text[1], text[-1]
            inv_id = id_line.lstrip("#")

            if csv_row_exists(inv_id):
                continue

            amount = amount_line.lstrip("$")
            dt     = datetime.strptime(date_txt, "%B %d, %Y")
            fname  = f"{dt.strftime('%Y_%b_%d')}_{inv_id}.pdf"
            fpath  = DEST_DIR / fname

            print(f"[{idx+1}/{total}] {fname}")

            # Open detail
            async with page.expect_navigation(wait_until="networkidle"):
                await row.click()

            await page.wait_for_selector(DETAIL_SEL, timeout=15000)
            await page.wait_for_selector(PRINT_BTN, timeout=10000)

            # ---- click PRINT (same tab) ----
            await page.locator(PRINT_BTN).click()
            await page.wait_for_selector('text="Invoice"', timeout=15000)
            await page.wait_for_timeout(500)   # settle

            # Full PDF – uses Squarespace's print stylesheet (includes Paid)
            await page.pdf(
                path=str(fpath),
                width="8.5in",
                height="12in",
                print_background=True,
                margin={"top": "0.75in", "bottom": "1in",
                        "left": "0.75in", "right": "0.75in"}
            )


            # ── Parse amount (and other fields) from the newly‑saved PDF ──
            info = extract_invoice_data.extract_invoice_data(fpath)

            csv_append(
                dt.date().isoformat(),       # date column
                info["invoice_number"],      # ID column (matches inv_id)
                info["amount_paid"],         # amount from PDF
                fname                        # filename
            )
            print(f"✅  Saved & indexed {fname} – Paid ${info['amount_paid']}")


            # back to list and continue
            await page.go_back(wait_until="networkidle")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
