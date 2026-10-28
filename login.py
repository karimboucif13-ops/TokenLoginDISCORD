import json
from playwright.sync_api import sync_playwright

APP_URL = "https://discord.com/channels/@me"

KEY = "token"
VALUE = input("Write The Token To LOGIN: ")

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=False
    )

    context = browser.new_context()

    key_js = json.dumps(KEY)
    value_js = json.dumps(f'"{VALUE}"')

    context.add_init_script(f"""
        try {{
            if (localStorage.getItem({key_js}) === null) {{
                localStorage.setItem({key_js}, {value_js});
            }}
        }} catch (e) {{
            console.error(e);
        }}
    """)

    page = context.new_page()
    page.goto(APP_URL, wait_until="load")

    print("SUCCES")
    input("Press Enter To EXIT...")

    browser.close()