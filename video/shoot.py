import asyncio, sys
from playwright.async_api import async_playwright
CASES = [("invoice_nile_trading.pdf", "What is the total amount?\nWho is the customer?"),
         ("receipt_cairo_coffee.jpg", "What is the total amount?\nWhen was it issued?"),
         ("invoice_scan_poor_quality.jpg", "What is the total amount?\nWhat is the status?"),
         ("flyer_unknown.png", "What is the total amount?")]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 810})
        await pg.goto("http://localhost:8765/")
        await pg.select_option("#eng", "local")
        await pg.screenshot(path="video/shots/00_empty.png")
        for i, (f, q) in enumerate(CASES, 1):
            await pg.set_input_files("#file", f"samples/{f}")
            await pg.fill("#q", q)
            await pg.screenshot(path=f"video/shots/{i}a_ready.png")
            await pg.click("#go")
            await pg.wait_for_selector(".banner")
            await pg.wait_for_function("document.querySelector('#go').textContent.startsWith('Analyze')")
            await pg.screenshot(path=f"video/shots/{i}b_result.png")
            await pg.evaluate("document.querySelector('#out pre').scrollIntoView({block:'start'})")
            await pg.screenshot(path=f"video/shots/{i}c_json.png")
            await pg.evaluate("window.scrollTo(0,0)")
        await b.close()
asyncio.run(main())
