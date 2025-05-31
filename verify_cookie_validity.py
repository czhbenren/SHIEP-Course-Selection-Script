import asyncio
import aiohttp
from tqdm.asyncio import tqdm

from config import headers
from custom import USE_PROXY, proxies, USER_CONFIGS, INQUIRY_USER_DATA

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None

check_url = "https://jw.shiep.edu.cn/eams/stdElectCourse.action"


class CheckResult:
    def __init__(self, label: str, success: bool):
        self.label = label
        self.success = success


async def check(label: str, cookies: dict) -> CheckResult:
    connector = None
    if USE_PROXY:
        if ProxyConnector and "all" in proxies:
            proxy_url_val = proxies["all"]
            if proxy_url_val:
                connector = ProxyConnector.from_url(proxy_url_val)
            else:
                print("Warning (Inquiry): USE_PROXY is True, but proxy URL is empty. No proxy.")
        elif not ProxyConnector:
            print("Warning (Inquiry): USE_PROXY is True, aiohttp-socks not installed. No proxy.")
        else:
            print("Warning (Inquiry): USE_PROXY is True, 'all' proxy key missing. No proxy.")

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url=check_url,
                headers=headers,
                cookies=cookies,
                timeout=5,
                ssl=False,
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return CheckResult(label=label, success=False)

    except Exception:
        return CheckResult(label=label, success=False)

    return CheckResult(label=label, success=True)


async def verify_cookie_validity():
    all_cookies_tasks = []
    print("Collecting cookies...")

    all_cookies_tasks.append(
        check(
            label=INQUIRY_USER_DATA.get("label", "Unknown_User"),
            cookies=INQUIRY_USER_DATA.get("cookies"),
        )
    )

    for user_config in USER_CONFIGS:
        user_label = user_config.get("label", "Unknown_User")
        user_cookies = user_config.get("cookies")

        task = check(label=user_label, cookies=user_cookies)
        all_cookies_tasks.append(task)

    if not all_cookies_tasks:
        print("Cannot find any cookies.")
        return

    print(f"Starting verification of all {len(all_cookies_tasks)} cookies...\n")
    results: list[CheckResult] = await tqdm.gather(*all_cookies_tasks, desc="Overall Cookies Verification Progress")

    print("\nAll cookies verification tasks have been processed.")
    await asyncio.sleep(0.1)

    invalid_results = []

    for result in results:
        if not result.success:
            invalid_results.append(result)

    print("\n--- Cookie Verification Summary ---")
    print(f"Total verified: {len(results)}")
    print(f"Valid cookies: {len(results) - len(invalid_results)}")
    print(f"Invalid cookies: {len(invalid_results)}")

    if invalid_results:
        print("\n--- Invalid Cookies Details ---")
        for peer in invalid_results:
            print(f"[INVALID] User: {peer.label}")

    print()
