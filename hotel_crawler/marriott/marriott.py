import requests
import json
import re
import logging
from .proxy_manager import ProxyManager
from datetime import datetime, timedelta
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("marriott.log"),
        logging.StreamHandler()
    ]
)

# Log variable for access log
logger = logging.getLogger(__name__)

logger.info("Starting application...")

class ExtractMarriott:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        while browser_family not in ("chromium", "firefox"):
            browser_family, headers = get_random_sec_ch_headers(USER_AGENT)

        self._headers = headers
        print(self._headers)

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()

        if not _proxy_url:
            raise "ERROR-101 : Proxy url not retrieved from the server"

        proxies = {
            'http':_proxy_url,
            'https':_proxy_url
        }
        logger.info("Proxy url dict created for request")

        # ---------- Session Setup ----------
        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(self._headers)

        logger.info("proxy & headers set in request session")

        logger.info("Setting up crawler to extract data")

        # Convert strings to datetime objects
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")

        # Calculate length of stay in days
        length_of_stay = int((check_out - check_in).days)


        if not hotel_id or length_of_stay <=0 or guest_count <= 0:
            raise("hotel_id/no_of_stays/guest must have some values.")
            return

        current_date = datetime.today().strftime("%Y-%m-%d")
        next_day_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        check_in_dd = check_in.strftime("%d")
        check_in_mm = check_in.strftime("%m")
        check_in_yyyy = check_in.strftime("%Y")

        check_out_dd = check_out.strftime("%d")
        check_out_mm = check_out.strftime("%m")
        check_out_yyyy = check_out.strftime("%Y")

        # ---- Retry mechanism ----
        int_count = 1
        for icount in range(3):
            is_all_requests_passed = True

            try:

                # ---------- 1: Marriott Homepage ----------
                url = "https://www.marriott.com/default.mi"
                headers = {
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp1 = session.get(url, headers=headers)
                logger.info(f"1 - Home_Page: {resp1.status_code}")

                # ---------- 2: Hotel page ----------
                url = f"https://www.marriott.com/en-us/hotels/{hotel_id}/overview/"
                headers = {
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'none',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp2 = session.get(url, headers=headers)
                logger.info(f"2 - Hotel_Page: {resp2.status_code}")
                ref_url = resp2.url
                logger.info(f"Referer URL: {ref_url}")
                if "The hotel is currently closed" in resp2.text:
                    logging.error("The hotel is currently closed.")
                    return ("The hotel is currently closed.")
                if resp2.status_code != 200:
                    logging.error("Error Occured.")
                    return ("Error Occured.")

                # ---------- 3: JS page ----------
                url = "https://www.marriott.com/etc.clientlibs/mcom-hws/clientlibs/clientlib-sitev2.min.25dfc6cf6a8b94135a28f9b03e6ed02d.js"
                headers = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp3 = session.get(url, headers=headers)
                logger.info(f"3 - JS_Page: {resp3.status_code}")

                pattern_phoenix_hws = r':"([^"]+)","apollographql-client-version":"v1","apollographql-client-name":"phoenix_hws"'
                match_phoenix_hws = re.search(pattern_phoenix_hws, resp3.text)

                if match_phoenix_hws:
                    phoenix_hws_signature = match_phoenix_hws.group(1)

                    # ---------- 4: Standard hotel form page ----------
                url = "https://www.marriott.com/mi/query/phoenixHWSLAR"
                payload = json.dumps({
                  "query": "\n    query phoenixHWSLAR($search: LowestAvailableRatesPropertyIdsSearchInput) {\n        searchLowestAvailableRatesByPropertyIds(search: $search) {\n            edges {\n                node {\n                    property {\n                        id\n                        basicInformation {\n                            name\n                            __typename\n                        }\n                        __typename\n                    }\n                    rates {\n                        rateAmounts {\n                            amount {\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            points\n                            mandatoryFees {\n                                origin {\n                                    valueDecimalPoint\n                                    value\n                                    currency\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            amountPlusMandatoryFees {\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            totalAmount {\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            rateMode {\n                                code\n                                label\n                                description\n                                __typename\n                            }\n                            __typename\n                        }\n                        rateCategory {\n                            type {\n                                code\n                                label\n                                description\n                                __typename\n                            }\n                            value\n                            __typename\n                        }\n                        status {\n                            code\n                            description\n                            __typename\n                        }\n                        __typename\n                    }\n                    __typename\n                }\n                __typename\n            }\n            __typename\n        }\n    }\n",
                  "variables": {
                    "search": {
                      "ids": [
                        hotel_id.upper()
                      ],
                      "options": {
                        "startDate": current_date,
                        "endDate": next_day_date,
                        "includeTaxesAndFees": True,
                        "quantity": 1,
                        "numberInParty": guest_count,
                        "rateRequestTypes": [
                          {
                            "type": "STANDARD",
                            "value": ""
                          }
                        ],
                        "includeMandatoryFees": True
                      }
                    }
                  }
                })
                headers = {
                    'x-request-id': '',
                    'accept-language': 'en-us',
                    'graphql-operation-signature': phoenix_hws_signature,
                    'apollographql-client-version': 'v1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_hws',
                    'accept': '*/*',
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': ref_url
                }
                resp4 = session.post(url, headers=headers, data=payload)
                logger.info(f"4 - Standard_Form_Page: {resp4.status_code}")
                if "Invalid Property Code" in resp4.text:
                    logging.error("Property Code is invalid.")
                    return ("Property Code is invalid.")

                # ---------- 5: Submit form page ----------
                url = f"https://www.marriott.com/reservation/availabilitySearch.mi?destinationAddress.country=&lengthOfStay={length_of_stay}&fromDate={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDate={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&numberOfRooms=1&numberOfAdults={guest_count}&guestCountBox={guest_count}+Adults+Per+Room&childrenCountBox=0+Children+Per+Room&roomCountBox=1+Rooms&childrenCount=0&childrenAges=&clusterCode=none&corporateCode=&groupCode=&isHwsGroupSearch=true&propertyCode={hotel_id.upper()}&useRewardsPoints=true&flexibleDateSearch=false&t-start={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&t-end={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromDateDefaultFormat={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDateDefaultFormat={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate_submit={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate="
                headers = {
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp5 = session.get(url, headers=headers)
                logger.info(f"5 - Submit_Form_Page: {resp5.status_code}")

                # ---------- 6: Rate List Menu ----------
                url = "https://www.marriott.com/reservation/rateListMenu.mi"
                headers = {
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp6 = session.get(url, headers=headers)
                logger.info(f"6 - Rate_List_Menu: {resp6.status_code}")

                # ---------- 7: Next JS Page ----------
                url = "https://www.marriott.com/mi-assets/mi-static/mi-book-renderer/phx-rel-R25.8.2-12aug20259pmist/_next/static/chunks/2424-b7ef29505ec20836.js"
                headers = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp7 = session.get(url, headers=headers)
                logger.info(f"7 - Next_JS_Page: {resp7.status_code}")

                pattern_PhoenixBookProperty = r'"operationName":"PhoenixBookProperty","signature":"([^"]+)"'
                match_PhoenixBookProperty = re.search(pattern_PhoenixBookProperty, resp7.text)

                if match_PhoenixBookProperty:
                    signature_PhoenixBookProperty = match_PhoenixBookProperty.group(1)

                pattern_PhoenixBookSearchProductsByProperty = r'"operationName":"PhoenixBookSearchProductsByProperty","signature":"([^"]+)"'
                match_PhoenixBookSearchProductsByProperty = re.search(pattern_PhoenixBookSearchProductsByProperty, resp7.text)

                if match_PhoenixBookSearchProductsByProperty:
                    signature_PhoenixBookSearchProductsByProperty = match_PhoenixBookSearchProductsByProperty.group(1)

                # ---------- 8: Book Property Page ----------
                url = "https://www.marriott.com/mi/query/PhoenixBookProperty"
                payload = json.dumps({
                  "operationName": "PhoenixBookProperty",
                  "variables": {
                    "propertyId": hotel_id.upper()
                  },
                  "query": "query PhoenixBookProperty($propertyId: ID!) {\n  property(id: $propertyId) {\n    ... on Hotel {\n      basicInformation {\n        ... on HotelBasicInformation {\n          descriptions {\n            type {\n              code\n              __typename\n            }\n            text\n            __typename\n          }\n          isAdultsOnly\n          resort\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                headers = {
                    'application-name': 'book',
                    'x-request-id': '',
                    'graphql-operation-name': 'PhoenixBookProperty',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': signature_PhoenixBookProperty,
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi'
                }
                resp8 = session.post(url, headers=headers, data=payload)
                logger.info(f"8 - Book_Property_Page: {resp8.status_code}")

                # ---------- 9: Standard Rate Page ----------
                url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
                payload = json.dumps({
                  "operationName": "PhoenixBookSearchProductsByProperty",
                  "variables": {
                    "search": {
                      "options": {
                        "startDate": check_in_date,
                        "endDate": check_out_date,
                        "quantity": 1,
                        "numberInParty": guest_count,
                        "childAges": [],
                        "productRoomType": [
                          "ALL"
                        ],
                        "productStatusType": [
                          "AVAILABLE"
                        ],
                        "rateRequestTypes": [
                          {
                            "value": "",
                            "type": "MEMBER"
                          }
                        ],
                        "isErsProperty": True
                      },
                      "propertyId": hotel_id.upper()
                    },
                    "offset": 0,
                    "limit": None
                  },
                  "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                headers = {
                    'application-name': 'book',
                    'x-request-id': '',
                    'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': signature_PhoenixBookSearchProductsByProperty,
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi'
                }
                resp9 = session.post(url, headers=headers, data=payload)
                logger.info(f"9 - Standard_Rate_Page: {resp9.status_code}")

                # ---------- 10: Promotional Rate Page ----------
                url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
                payload = json.dumps({
                  "operationName": "PhoenixBookSearchProductsByProperty",
                  "variables": {
                    "search": {
                      "options": {
                        "startDate": check_in_date,
                        "endDate": check_out_date,
                        "quantity": 1,
                        "numberInParty": guest_count,
                        "childAges": [],
                        "productRoomType": [
                          "ALL"
                        ],
                        "productStatusType": [
                          "AVAILABLE"
                        ],
                        "rateRequestTypes": [
                          {
                            "value": "",
                            "type": "STANDARD"
                          },
                          {
                            "value": "",
                            "type": "PREPAY"
                          },
                          {
                            "value": "",
                            "type": "PACKAGES"
                          },
                          {
                            "value": "MRM",
                            "type": "CLUSTER"
                          },
                          {
                            "value": "",
                            "type": "REDEMPTION"
                          },
                          {
                            "value": "",
                            "type": "REGULAR"
                          }
                        ],
                        "isErsProperty": True
                      },
                      "propertyId": hotel_id.upper()
                    },
                    "offset": 0,
                    "limit": None
                  },
                  "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                headers = {
                    'application-name': 'book',
                    'x-request-id': '',
                    'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': signature_PhoenixBookSearchProductsByProperty,
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi'
                }
                resp10 = session.post(url, headers=headers, data=payload)
                logger.info(f"10 - Promotional_Rate_Page: {resp10.status_code}")
                if "\"Invalid Property Code\"" in resp10.text:
                    logging.error("Property Code is invalid.")
                    return ("Property Code is invalid.")
                if '"code":"standard"' in resp10.text and '"code":"redemption"' not in resp10.text:
                    logging.error("There are no redemption rates available for the dates you selected.")
                    return("There are no redemption rates available for the dates you selected.")

                text_resp = resp10.text
                file_path = f"marriott_{hotel_id}_{check_in_date}_{check_out_date}_response.json"

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
                logging.error(f"Exception occurred: {ex}")
                is_all_requests_passed = False
            finally:
                logger.info("Closing application...")

            if is_all_requests_passed:
                break

        return json_data

if __name__ =="__main__":
    crawl = ExtractMarriott()
    crawl.get_search_data("sellc", "2026-02-15", "2026-02-16",1)