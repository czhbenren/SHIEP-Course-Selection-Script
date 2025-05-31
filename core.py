import asyncio
import aiohttp
import warnings
from urllib3.exceptions import InsecureRequestWarning

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None

from config import url, headers, data as base_data_payload, failed_words, error_words
from custom import USE_PROXY, proxies

warnings.simplefilter("ignore", InsecureRequestWarning)


async def attempt_single_course_selection(
    session: aiohttp.ClientSession,
    course_id_to_select: str,
    user_cookies: dict,
    user_params: dict,
    succeed_event: asyncio.Event,
):
    """
    Makes a single attempt to select a course for a specific user.
    Sets the provided succeed_event if successful.
    """

    current_data_payload = base_data_payload.copy()
    current_data_payload["operator0"] = f"{course_id_to_select}:true:0"

    request_kwargs = {
        "headers": headers,
        "cookies": user_cookies,
        "params": user_params,
        "data": current_data_payload,
        "timeout": 1,
        "ssl": False,  # disables SSL cert verification
    }

    # print(f"\n{request_kwargs}\n")  # DEBUG

    try:
        async with session.post(url, **request_kwargs) as response:
            response_text = await response.text()
            print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Status {response.status}")

            if response.status == 200:
                if "已经选过" in response_text or not (any(word in response_text for word in failed_words) or any(word in response_text for word in error_words)):
                    if "已经选过" in response_text:
                        print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Already selected.\n")
                    else:
                        print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Selection Succeeded!\n")
                    succeed_event.set()
                    return True
                elif any(word in response_text for word in failed_words):
                    print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Failed (reason: {response_text.strip()}).\n")
                elif "当前选课不开放" in response_text:
                    print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Failed (error: 操作失败:当前选课不开放).\n")
                elif "请不要过快点击" in response_text:
                    print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Failed (error: 请不要过快点击).\n")
                elif any(word in response_text for word in error_words):
                    print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Failed (error: {response_text.strip()}).\n")
                else:
                    print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: 200 OK, outcome unclear (response: {response_text.strip()}).\n")
            else:
                print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Non-200 Status {response.status} (response: {response_text.strip()}).\n")

    except asyncio.TimeoutError:
        print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Request timed out.\n")
    except aiohttp.ClientError as e:
        print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Network ClientError: {e}\n")
    except Exception as e:
        print(f"User ({user_params.get('profileId', 'N/A')}) - Course ID {course_id_to_select}: Exception: {e}\n")

    return False


async def run_course_selection_loop_for_user(
    course_id_to_select: str,
    user_label: str,
    user_cookies: dict,
    user_profile_id: str,
):
    """
    Public function to be called by main.py for each course of each user.
    Repeatedly attempts to select a course until successful.
    """
    succeed_event = asyncio.Event()
    connector = None

    user_params = {"profileId": user_profile_id}

    if USE_PROXY:
        if ProxyConnector and "all" in proxies:
            proxy_url_val = proxies["all"]
            if proxy_url_val:
                connector = ProxyConnector.from_url(proxy_url_val)
            else:
                print(f"Warning (User {user_label}, Course {course_id_to_select}): USE_PROXY is True, but proxy URL is empty. No proxy.")
        elif not ProxyConnector:
            print(f"Warning (User {user_label}, Course {course_id_to_select}): USE_PROXY is True, but aiohttp-socks not installed. No proxy.")
        else:
            print(f"Warning (User {user_label}, Course {course_id_to_select}): USE_PROXY is True, but 'all' proxy key missing. No proxy.")

    async with aiohttp.ClientSession(connector=connector) as session:
        attempt_count = 0
        while not succeed_event.is_set():
            attempt_count += 1
            print(f"User {user_label} - Course ID {course_id_to_select}: Starting attempt {attempt_count}...")
            await attempt_single_course_selection(
                session,
                course_id_to_select,
                user_cookies,
                user_params,
                succeed_event,
            )
            if not succeed_event.is_set():
                await asyncio.sleep(0.2)

    print(f"User {user_label} - Course selection process for {course_id_to_select} has concluded.")
