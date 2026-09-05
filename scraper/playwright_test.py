from playwright.sync_api import sync_playwright


def test_indigo():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            slow_mo=300
        )

        page = browser.new_page(
            viewport={"width": 1440, "height": 900}
        )

        # -----------------------------
        # Browser diagnostics
        # -----------------------------

        page.on(
            "console",
            lambda msg: print(
                f"[CONSOLE {msg.type}] {msg.text}"
            )
        )

        page.on(
            "pageerror",
            lambda error: print(
                f"[PAGE ERROR] {error}"
            )
        )

        page.on(
            "requestfailed",
            lambda request: print(
                f"[REQUEST FAILED] {request.url}\n"
                f"    ERROR: {request.failure}"
            )
        )

        print("Opening IndiGo...")

        response = page.goto(
            "https://www.goindigo.in/",
            wait_until="domcontentloaded",
            timeout=60000
        )

        print(
            "HTTP:",
            response.status if response else None
        )

        print("URL:", page.url)
        print("Title:", page.title())

        print("\nWaiting 30 seconds...\n")

        page.wait_for_timeout(30000)

        # -----------------------------
        # DOM diagnostics
        # -----------------------------

        print("\n========== DOM ==========")

        print(
            "Input count:",
            page.locator("input").count()
        )

        print(
            "Button count:",
            page.locator("button").count()
        )

        print(
            "Select count:",
            page.locator("select").count()
        )

        print(
            "Iframe count:",
            page.locator("iframe").count()
        )

        # Check actual visible inputs
        print("\n========== VISIBLE INPUTS ==========")

        inputs = page.locator("input")

        for i in range(inputs.count()):

            element = inputs.nth(i)

            try:

                print(
                    i,
                    "| visible:",
                    element.is_visible(),
                    "| placeholder:",
                    element.get_attribute("placeholder"),
                    "| type:",
                    element.get_attribute("type"),
                    "| value:",
                    element.input_value()
                )

            except Exception as e:

                print(i, "| ERROR:", e)

        # -----------------------------
        # Buttons
        # -----------------------------

        print("\n========== VISIBLE BUTTONS ==========")

        buttons = page.locator("button")

        for i in range(min(buttons.count(), 30)):

            button = buttons.nth(i)

            try:

                print(
                    i,
                    "| visible:",
                    button.is_visible(),
                    "| text:",
                    repr(button.inner_text()[:100])
                )

            except Exception as e:

                print(i, "| ERROR:", e)

        # -----------------------------
        # Screenshot
        # -----------------------------

        page.screenshot(
            path="indigo_diagnostic.png",
            full_page=True
        )

        print("\nScreenshot saved.")

        print("\nBrowser remains open.")
        input("Press ENTER to close...")

        browser.close()


if __name__ == "__main__":
    test_indigo()