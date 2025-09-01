import json
import os
import random
import time
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
PROXY_PROVIDER_ENDPOINT=os.getenv('PROXY_PROVIDER_ENDPOINT')
X_API_TOKEN=os.getenv('X_API_TOKEN')
PROXY_PROVIDER = ['proxyrack','privateproxy']

print(PROXY_PROVIDER_ENDPOINT)

def _build_proxy_url(conn):
    if conn:
        return f"http://{conn.get('user')}:{conn.get('password')}@{conn.get('host')}:{conn.get('port')}"
    raise("Proxy not generated. Please check your proxy provider and try again.")


class ProxyManager:
    """
    ProxyManager class to manage and cache proxies, with region support and retry logic.
    """
    def __init__(self):
        self.proxy_data: dict = {}
        self.proxy_provider = random.choice(PROXY_PROVIDER)
        self.proxy_endpoint = PROXY_PROVIDER_ENDPOINT
        self.x_api_token = X_API_TOKEN

    def fetch_proxy(self, region_code: str = 'us', max_retries: int = 3):
        """
        Fetch proxy from provider with retry and exponential backoff.
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.x_api_token,
        }

        for attempt in range(max_retries):
            try:
                payload = json.dumps({
                    "provider": self.proxy_provider,
                    "region_code": region_code
                })
                response = requests.post(
                    self.proxy_endpoint,
                    headers=headers,
                    data=payload,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                conn = data.get('proxy_connection')
                if not conn:
                    raise "No proxy details available"
                return _build_proxy_url(conn)
            except requests.RequestException as e:
                print(f"Attempt {attempt} to get the proxy")
                wait = 2 ** attempt
                time.sleep(wait)
# # tEST CODE
if __name__ == "__main__":
    proxy_manager = ProxyManager()
    proxy = proxy_manager.fetch_proxy()
    print(proxy)
