import random

def get_random_sec_ch_headers(user_agents: list) -> dict:

    user_agent = random.choice(user_agents)
    ua = user_agent.lower()

    headers = {
        'user-agent': user_agent,
        'accept-encoding': 'gzip, deflate, br, zstd'
    }

    browser_family = "other"

    # Chrome (but not Edge)
    if "chrome" in ua and "edg" not in ua:
        version = user_agent.split("Chrome/")[1].split(".")[0]
        if "windows" in ua:
            platform = '"Windows"'
        elif "macintosh" in ua or "mac os" in ua:
            platform = '"macOS"'
        elif "linux" in ua:
            platform = '"Linux"'
        else:
            platform = '"Windows"'
        headers.update({
            'sec-ch-ua': f'"Not;A=Brand";v="99", "Google Chrome";v="{version}", "Chromium";v="{version}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': platform,
        })
        browser_family = "chromium"

    # Edge (Chromium-based)
    elif "edg" in ua:
        version = user_agent.split("Edg/")[1].split(".")[0]
        if "windows" in ua:
            platform = '"Windows"'
        elif "macintosh" in ua or "mac os" in ua:
            platform = '"macOS"'
        elif "linux" in ua:
            platform = '"Linux"'
        else:
            platform = '"Unknown"'
        headers.update({
            'sec-ch-ua': f'"Not;A=Brand";v="99", "Microsoft Edge";v="{version}", "Chromium";v="{version}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': platform,
        })
        browser_family = "chromium"

        # Firefox
    elif "firefox" in ua:
        browser_family = "firefox"

    # Safari
    elif "safari" in ua and "chrome" not in ua:
        browser_family = "webkit"

    return browser_family, headers


# --- Example Usage ---

USER_AGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
]

if __name__ == "__main__":
    headers = get_random_sec_ch_headers(USER_AGENT)
    print("Headers:", headers)
