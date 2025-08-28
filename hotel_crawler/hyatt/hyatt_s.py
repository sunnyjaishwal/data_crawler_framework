import asyncio
import json
import random
import time
import logging
from urllib.parse import urlparse
from .proxy_manager import ProxyManager
from datetime import datetime
from playwright.async_api import async_playwright
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("hyatt.log"),
        logging.StreamHandler()
    ]
)

# Log variable for access log
logger = logging.getLogger(__name__)

logger.info("Starting application...")

# ---------------- Required Functions ----------------
def human_delay(a, b):
    time.sleep(random.uniform(a, b))

# ---------------- Main Function ----------------
class ExtractHyatt:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        while browser_family != "chromium":
            browser_family, headers = get_random_sec_ch_headers(USER_AGENT)

        self._headers = headers
        print(self._headers)

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()

        if not _proxy_url:
            raise "ERROR-101 : Proxy url not retrieved from the server"

        parsed = urlparse(_proxy_url)
        proxy = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password
        }

        logger.info("Proxy url dict created for request")

        logger.info("Setting up crawler to extract data")

        # Convert strings to datetime objects
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")

        # Calculate length of stay in days
        length_of_stay = int((check_out - check_in).days)

        if not hotel_id or length_of_stay <=0 or guest_count <= 0:
            raise("hotel_id/no_of_stays/guest must have some values.")
            return

        # ---- Retry mechanism ----
        int_count = 1
        for icount in range(3):
            is_all_requests_passed = True

            try:
                async with async_playwright() as p:
                    chromium = p.chromium
                    browser = await chromium.launch(
                        headless=True,
                        proxy=proxy,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-infobars",
                            "--disable-dev-shm-usage",
                            "--disable-extensions",
                            '--start-maximized',
                        ]
                    )

                    try:
                        rand = random.Random()
                        logger.info("Sending Home page request....")
                        extra_headers = {k: v for k, v in self._headers.items() if k.lower() != "user-agent"}

                        context = await browser.new_context(
                            user_agent=self._headers["user-agent"],
                            locale="en-US",
                            extra_http_headers=extra_headers
                        )

                        page = await context.new_page()
                        page.set_default_timeout(100000)

                        await page.goto("https://www.hyatt.com/", wait_until="load",timeout=120000)
                        human_delay(12, 30)

                        await page.locator('input[data-id="location"]').wait_for(timeout=80000)
                        await page.get_by_role("button", name="Find Hotels").wait_for(timeout=80000)

                        logger.info("Home page request completed successfully.....")

                        # ---- Mouse movement ----
                        logger.info("Sleeping for few seconds for mouse movement.....")
                        await asyncio.sleep(rand.randint(9, 16))
                        await page.mouse.move(rand.randint(0, 2), rand.randint(3, 8))
                        await page.mouse.down()
                        await page.mouse.move(0, rand.randint(100, 120))
                        await page.mouse.move(rand.randint(100, 120), rand.randint(100, 120))
                        await page.mouse.move(rand.randint(100, 120), 0)
                        await page.mouse.move(0, 0)
                        await page.mouse.up()

                        await page.keyboard.press("PageDown")
                        await asyncio.sleep(rand.randint(3, 9))
                        await page.keyboard.press("PageUp")
                        await asyncio.sleep(rand.randint(4, 8))

                        logger.info("Mouse movement completed.....")

                        # ---- Room rates API calls ----
                        url = (f"https://www.hyatt.com/shop/service/rooms/roomrates/{hotel_id}"
                               f"?spiritCode={hotel_id}&rooms=1&adults={guest_count}"
                               f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                               f"&kids=0&rate=Standard&rateFilter=woh&suiteUpgrade=true")

                        logger.info(f"Navigating to roomrate API:: {url}")

                        response = await page.goto(url)
                        await page.wait_for_load_state("load")

                        text_resp = await response.text()
                        if '"invalidSpiritCode"' in text_resp:
                            logging.error("Property Code is invalid.")
                            return

                        file_path = f"hyatt_{hotel_id}_{check_in_date}_{check_out_date}_response.json"

                        logger.info(f"Saving API Response at Path:- {file_path}")

                        try:
                            json_data = json.loads(text_resp)
                        except json.JSONDecodeError:
                            logger.info("Response is not valid JSON")
                            json_data = {"raw_response": text_resp}

                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=4, ensure_ascii=False)

                        int_count += 1


                    except Exception as ex:
                        logger.info(f"Exception occurred: {ex}")
                        is_all_requests_passed = False
                    finally:
                        logger.info("Closing application...")
                        await browser.close()

            except Exception as ex:
                logger.info(f"Critical Error: {ex}")
                is_all_requests_passed = False

            if is_all_requests_passed:
                break

        return json_data


async def main():
    crawl = ExtractHyatt()
    await crawl.get_search_data("dpsbl", "2026-01-15", "2026-01-16", 1)

if __name__ == "__main__":
    asyncio.run(main())