from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import quote_from_bytes
import json

local_path = Path("/mnt/data/4c826644-e8f8-4e3f-9656-83bef612fea3.png")
if not local_path.exists():
    raise SystemExit(f"File not found: {local_path}")

file_url = "file://" + quote_from_bytes(str(local_path).encode("utf-8"))

output_shot = Path("screenshot_from_container.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width":1280, "height":800})
    print("Opening:", file_url)
    page.goto(file_url, wait_until="load", timeout=20000)
    page.screenshot(path=str(output_shot), full_page=True)
    title = page.title()
    try:
        content = page.content()
    except Exception:
        content = ""
    browser.close()

result = {
    "file_url": file_url,
    "screenshot": str(output_shot),
    "title": title,
    "content_snippet": (content[:300] + "...") if content else ""
}
print(json.dumps(result, indent=2))
