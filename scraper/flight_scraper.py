from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re


def parse_fare(text):
    match = re.search(r"[\d,]+", text)

    if not match:
        return None

    return float(match.group().replace(",", ""))


def print_observations_table(observations):
    if not observations:
        print("\nNo flight observations found.")
        return

    print("\n")
    print("=" * 120)
    print("                         SPICEJET FARE OBSERVATIONS")
    print("=" * 120)

    print(
        f"{'Flight':<12}"
        f"{'Route':<12}"
        f"{'Travel Date':<15}"
        f"{'Departure':<12}"
        f"{'Arrival':<12}"
        f"{'Fare Type':<15}"
        f"{'Fare (INR)':>15}"
    )

    print("-" * 120)

    for obs in observations:

        route = f"{obs['origin']}-{obs['destination']}"

        fare = obs["total_fare"]

        if fare is not None:
            fare_display = f"₹{fare:,.2f}"
        else:
            fare_display = "N/A"

        print(
            f"{obs['flight_number']:<12}"
            f"{route:<12}"
            f"{obs['travel_date']:<15}"
            f"{obs['departure_time']:<12}"
            f"{obs['arrival_time']:<12}"
            f"{obs['fare_type']:<15}"
            f"{fare_display:>15}"
        )

    print("=" * 120)
    print(f"Total observations: {len(observations)}")
    print("=" * 120)


def extract_flight_cards(result_page):

    observations = []

    flight_numbers = result_page.locator("#aircraft-no")

    count = flight_numbers.count()

    print(f"\nFlight cards found: {count}")

    for i in range(count):

        try:

            flight_number_element = flight_numbers.nth(i)

            flight_number = flight_number_element.inner_text().strip()

            # Move upward from flight number to the complete flight card.
            flight_card = flight_number_element

            for _ in range(8):
                flight_card = flight_card.locator("..")

            # Get complete card text.
            card_text = flight_card.inner_text()

            # Find departure and arrival times.
            times = re.findall(
                r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
                card_text
            )

            departure_time = times[0] if len(times) >= 1 else None
            arrival_time = times[1] if len(times) >= 2 else None
        def select_observations(observations):

    if not observations:
        print("\nNo observations available.")
        return []

    print("\n")
    print("=" * 110)
    print("                  AVAILABLE FLIGHT OBSERVATIONS")
    print("=" * 110)

    print(
        f"{'No.':<5}"
        f"{'Flight':<12}"
        f"{'Route':<12}"
        f"{'Departure':<12}"
        f"{'Arrival':<12}"
        f"{'Fare Type':<15}"
        f"{'Fare (INR)':>15}"
    )

    print("-" * 110)

    for index, obs in enumerate(observations, start=1):

        route = (
            f"{obs['origin']}-"
            f"{obs['destination']}"
        )

        fare = obs["total_fare"]

        print(
            f"{index:<5}"
            f"{obs['flight_number']:<12}"
            f"{route:<12}"
            f"{obs['departure_time']:<12}"
            f"{obs['arrival_time']:<12}"
            f"{obs['fare_type']:<15}"
            f"₹{fare:>13,.2f}"
        )

    print("=" * 110)

    while True:

        selection = input(
            "\nEnter observation numbers to store "
            "(example: 1,3,5): "
        ).strip()

        if not selection:
            print("No selection made.")
            return []

        try:

            selected_numbers = [
                int(x.strip())
                for x in selection.split(",")
            ]

            # Remove duplicates
            selected_numbers = list(
                dict.fromkeys(selected_numbers)
            )

            # Validate numbers
            if any(
                number < 1
                or number > len(observations)
                for number in selected_numbers
            ):
                print(
                    "Invalid selection. "
                    "Choose numbers from the table."
                )
                continue

            selected = [
                observations[number - 1]
                for number in selected_numbers
            ]

            print("\nSelected observations:")

            for obs in selected:

                print(
                    f"  {obs['flight_number']} | "
                    f"{obs['fare_type']} | "
                    f"₹{obs['total_fare']:,.2f}"
                )

            confirm = input(
                "\nStore these observations? (y/n): "
            ).strip().lower()

            if confirm == "y":
                return selected

            print("\nSelection cancelled.")
            print("Please select again.")

        except ValueError:

            print(
                "Invalid input. "
                "Use numbers separated by commas."
            )
            # ---------------------------------------------------------
            # Extract all fare prices from the fare-bundle section.
            # ---------------------------------------------------------

            fare_types = [
                "SpiceSaver",
                "SpiceFlex",
                "SpiceMax"
            ]

            fares = []

            fare_section = flight_card.locator("#fare-bundle-val")

            if fare_section.count() > 0:

                fare_text = fare_section.first.inner_text()

                fares = re.findall(
                    r"₹\s*[\d,]+",
                    fare_text
                )

            # Fallback if the fare section was not found.
            if not fares:

                fares = re.findall(
                    r"₹\s*[\d,]+",
                    card_text
                )

            print(
                f"\nFlight {flight_number}: "
                f"{len(fares)} fare(s) found"
            )

            # Create one observation for every fare type.
            for index, fare_type in enumerate(fare_types):

                if index < len(fares):

                    fare = parse_fare(fares[index])

                    observation = {
                        "flight_number": flight_number,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time,
                        "total_fare": fare,
                        "fare_type": fare_type
                    }

                    observations.append(observation)

                    print(
                        f"  {fare_type}: "
                        f"₹{fare:,.2f}"
                    )

                else:

                    print(
                        f"  {fare_type}: "
                        f"NOT AVAILABLE"
                    )

        except Exception as e:

            print(
                f"\nCould not extract flight "
                f"{i + 1}: {e}"
            )

    return observations


def scrape_spicejet_fare(
    origin_code="DEL",
    destination_code="BOM",
    advance_days=7
):

    travel_date_obj = (
        datetime.now()
        + timedelta(days=advance_days)
    )

    observations = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context()

        page = context.new_page()

        # ---------------------------------------------------------
        # STEP 1: Open SpiceJet
        # ---------------------------------------------------------

        page.goto(
            "https://www.spicejet.com",
            wait_until="domcontentloaded"
        )

        print("STEP 1: Page loaded")

        page.wait_for_timeout(2000)

        # ---------------------------------------------------------
        # STEP 2: Fill destination
        # ---------------------------------------------------------

        page.get_by_test_id(
            "to-testID-destination"
        ).get_by_text("To").click()

        page.wait_for_timeout(500)

        page.get_by_test_id(
            "to-testID-destination"
        ).get_by_role("textbox").fill(
            destination_code
        )

        print("STEP 2: Filled destination")

        page.wait_for_timeout(1500)

        # ---------------------------------------------------------
        # STEP 3: Open date picker
        # ---------------------------------------------------------

        page.locator(
            "div"
        ).filter(
            has_text="Select Date"
        ).first.click()

        print("STEP 3: Opened date picker")

        page.wait_for_timeout(1500)

        # ---------------------------------------------------------
        # STEP 4: Verify travel date
        # ---------------------------------------------------------

        expected_date = travel_date_obj.strftime(
            "%d %b %Y"
        )

        body_text = page.locator(
            "body"
        ).inner_text()

        print("\nLooking for departure date:")
        print(expected_date)

        if expected_date in body_text:

            print(
                "STEP 4: Correct departure date "
                "is already selected"
            )

        else:

            print(
                "STEP 4: Could not verify "
                "departure date"
            )

        page.keyboard.press("Escape")

        page.wait_for_timeout(1000)

        # ---------------------------------------------------------
        # STEP 5: Search
        # ---------------------------------------------------------

        print(
            "\nSTEP 5: Clicking Search Flight..."
        )

        page.get_by_test_id(
            "home-page-flight-cta"
        ).click()

        print(
            "STEP 6: Waiting for "
            "flight-results page..."
        )

        # ---------------------------------------------------------
        # STEP 6: Find correct results page
        # ---------------------------------------------------------

        result_page = None

        for _ in range(30):

            for current_page in context.pages:

                try:

                    if (
                        "spicejet.com/search?"
                        in current_page.url
                    ):

                        result_page = current_page

                        break

                except Exception:
                    pass

            if result_page:
                break

            page.wait_for_timeout(500)

        if result_page is None:

            print(
                "\nERROR: Flight-results "
                "page was not found."
            )

            print("\nOpen pages:")

            for i, current_page in enumerate(
                context.pages
            ):

                try:

                    print(
                        f"Page {i}: "
                        f"{current_page.url}"
                    )

                except Exception:

                    print(
                        f"Page {i}: "
                        "URL unavailable"
                    )

            page.wait_for_timeout(5000)

            browser.close()

            return observations

        print(
            "SUCCESS: Correct "
            "flight-results page found"
        )

        result_page.wait_for_timeout(5000)

        print("\nRESULT URL:")

        print(result_page.url)

        # ---------------------------------------------------------
        # STEP 7: Extract flights and all fares
        # ---------------------------------------------------------

        print(
            "\nSTEP 7: Extracting "
            "flight cards and fares..."
        )

        observations = extract_flight_cards(
            result_page
        )

        # ---------------------------------------------------------
        # STEP 8: Add common information
        # ---------------------------------------------------------

        for observation in observations:

            observation["source"] = "SpiceJet"

            observation["origin"] = origin_code

            observation["destination"] = destination_code

            observation["travel_date"] = (
                travel_date_obj.strftime(
                    "%Y-%m-%d"
                )
            )

            observation["advance_days"] = (
                advance_days
            )

            observation["collection_timestamp"] = (
                datetime.now().isoformat()
            )

        # ---------------------------------------------------------
        # STEP 9: Print final table
        # ---------------------------------------------------------

        print_observations_table(
            observations
        )

        print(
            "\nKeeping browser open "
            "for 5 seconds..."
        )

        result_page.wait_for_timeout(5000)

        browser.close()

    return observations


if __name__ == "__main__":

    results = scrape_spicejet_fare(
        origin_code="DEL",
        destination_code="BOM",
        advance_days=7
    )

    print(
        "\nScraper finished successfully."
    )