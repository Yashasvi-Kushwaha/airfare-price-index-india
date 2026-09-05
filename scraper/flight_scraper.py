from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re


def scrape_spicejet_fare(destination_code="bom", travel_day=12, travel_month_year="September 2026",
                          origin_code="DEL", destination_display_code="BOM", advance_days=7):
    travel_date_obj = datetime.now() + timedelta(days=advance_days)
    travel_date = travel_date_obj.strftime("%Y-%m-%d")
    observations = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.spicejet.com/")
        print("STEP 1: Page loaded")

        # Click destination field and fill
        page.get_by_test_id("to-testID-destination").get_by_text("To").click()
        page.wait_for_timeout(500)
        page.get_by_test_id("to-testID-destination").get_by_role("textbox").fill(destination_code)
        print("STEP 2: Filled destination")
        page.wait_for_timeout(1000)

        # NOTE: the recorded script's date-selection steps look inconsistent/duplicated —
        # this part needs re-verification, see note below
        page.get_by_text("Select Date").click()
        page.wait_for_timeout(500)

        # Using the reliable test-id pattern found for date selection
        month_test_id = f"undefined-month-{travel_date_obj.strftime('%B-%Y')}"
        page.get_by_test_id(month_test_id).get_by_text(str(travel_date_obj.day), exact=True).click()
        print(f"STEP 3: Clicked date {travel_date_obj.day} in {travel_date_obj.strftime('%B %Y')}")
        page.wait_for_timeout(500)

        # Click search
        page.get_by_test_id("home-page-flight-cta").click()
        print("STEP 4: Clicked search")

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)  # let results render

        # TODO: results page selectors — need inspection, same as before but hopefully
        # SpiceJet also uses data-testid attributes on results, worth checking first
        # before falling back to class-based selectors

        # placeholder — replace once you inspect the results page
        flight_cards = page.query_selector_all("[data-testid*='flight']")  # guess, verify
        print(f"Found {len(flight_cards)} raw cards")

        browser.close()

    return observations


if __name__ == "__main__":
    results = scrape_spicejet_fare()
    print(f"\nFinal result: {len(results)} observations")
    for obs in results:
        print(obs)