import asyncio
import aiohttp
import json
import sys
import re
import warnings
from urllib3.exceptions import InsecureRequestWarning

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None

from config import headers, proxies, USE_PROXY, ENROLLMENT_DATA_API_PARAMS
from custom import INQUIRY_USER_DATA

warnings.simplefilter("ignore", InsecureRequestWarning)


def fix_nonstandard_json(data_str: str):
    data_str = re.sub(r"(?<!\\)'", '"', data_str)
    data_str = re.sub(r"(\b[a-zA-Z_]\w*\b)(?=\s*:)", r'"\1"', data_str)
    return data_str


def parse_course_json(data_str: str):
    try:
        parsed_data = json.loads(data_str)
        return parsed_data
    except json.JSONDecodeError:
        print("Course data is non-standard JSON data! Attempting to fix.")
        fixed_data = fix_nonstandard_json(data_str)
        try:
            parsed_data = json.loads(fixed_data)
            print("Course data parsed successfully after fixing!")
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"Parsing still failed after attempting to fix: {e}")
            sys.exit(1)


async def get_course_data_async(session: aiohttp.ClientSession, profile_id_to_use: str, inquiry_cookies: dict):
    url = f"https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId={profile_id_to_use}"
    try:
        async with session.get(
            url=url,
            headers=headers,
            cookies=inquiry_cookies,
            timeout=10,
            ssl=False,
        ) as response:
            response.raise_for_status()
            raw_data = await response.text(encoding="utf-8")
            raw_data = raw_data.strip()
            json_data_match = re.search(r"\[.*\]", raw_data, re.DOTALL)
            if json_data_match:
                return parse_course_json(json_data_match.group())
            else:
                print("Failed to retrieve valid JSON course data from response.")
                sys.exit(1)
    except aiohttp.ClientError as e:
        print(f"Failed to retrieve course data due to client error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred in get_course_data_async: {e}")
        sys.exit(1)


async def get_enrollment_data_async(session: aiohttp.ClientSession, inquiry_cookies: dict):
    base_url = "https://jw.shiep.edu.cn/eams/stdElectCourse!queryStdCount.action"
    try:
        async with session.get(
            url=base_url,
            headers=headers,
            cookies=inquiry_cookies,
            params=ENROLLMENT_DATA_API_PARAMS,
            timeout=10,
            ssl=False,
        ) as response:
            response.raise_for_status()
            raw_data = await response.text(encoding="utf-8")
            json_data_match = re.search(r"\{.*\}", raw_data, re.DOTALL)
            if json_data_match:
                return parse_course_json(json_data_match.group())
            else:
                print("Failed to retrieve valid JSON enrollment data from response.")
                sys.exit(1)
    except aiohttp.ClientError as e:
        print(f"Failed to retrieve enrollment data due to client error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred in get_enrollment_data_async: {e}")
        sys.exit(1)


def filter_courses(courses: list, keyword: str, enrollments: dict):
    filtered_courses_list = []
    # Check if keyword is in "key=value" format
    if "=" in keyword:
        key, value = keyword.split("=", 1)
        key = key.strip().lower()
        value = value.strip().lower()
    else:
        key = "name"  # Default to searching name
        value = keyword.lower()
    for course in courses:
        search_field = str(course.get(key, "")).lower()
        if value in search_field:
            lesson_id = str(course["id"])
            sc = enrollments.get(lesson_id, {}).get("sc", "N/A")
            lc = enrollments.get(lesson_id, {}).get("lc", "N/A")
            filtered_courses_list.append(
                {
                    "id": course["id"],
                    "no": course["no"],
                    "name": course["name"],
                    "credits": course["credits"],
                    "type": course["type"],
                    "teacher": course["teacher"],
                    "enrolled": sc,
                    "limit": lc,
                }
            )
    return filtered_courses_list


async def inquire_course_info_async():
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

    async with aiohttp.ClientSession(connector=connector) as session:
        inquiry_cookies = INQUIRY_USER_DATA.get("cookies")

        if not inquiry_cookies:
            print("Error: Inquiry cookies not found in custom.py (INQUIRY_USER_DATA). Please configure them.")
            return

        profile_id_to_use = ""
        while True:
            prompt_message = "Input profileId for inquiry (cannot be empty): "
            profile_id_to_use = input(prompt_message).strip()
            if profile_id_to_use:
                break
            else:
                print("Error: profileId cannot be empty. Please enter a valid profileId.")

        print(f"Fetching course data for profileId: {profile_id_to_use}...")
        courses = await get_course_data_async(session, profile_id_to_use, inquiry_cookies)
        if not courses:
            print("Could not fetch course data. Exiting inquiry.")
            return

        # Rename keys in course data
        # print(list(courses[0].keys()))
        key_mapping = {
            "id": "id",
            "no": "no",
            "name": "name",
            "credits": "credits",
            "courseTypeName": "type",
            "teachers": "teacher",
        }
        courses = [{new_key: course.get(old_key, "") for old_key, new_key in key_mapping.items()} for course in courses]
        # print(list(courses[0].keys()))

        print("Fetching enrollment data...")
        enrollments = await get_enrollment_data_async(session, inquiry_cookies)
        if not enrollments:
            print("Could not fetch enrollment data. Exiting inquiry.")
            return

        print("\n--- Course Inquiry Ready ---")
        while True:
            keyword = input("\nInput course name keyword or 'key=value' to search by field ('q' to quit): ").strip()
            if keyword.lower() == "q":
                print("Exiting course inquiry.")
                break

            filtered = filter_courses(courses, keyword, enrollments)
            if filtered:
                filtered.sort(key=lambda x: (x["type"], -x["credits"], x["id"]))
                print("\nThe matching course information is as follows:")
                for course_item in filtered:
                    print(
                        f"ID: {course_item['id']}, No: {course_item['no']}, Type: {course_item['type']}, "
                        f"Credits: {course_item['credits']}, Enrolled: {course_item['enrolled']}/{course_item['limit']}, "
                        f"Name: {course_item['name']}, Teacher: {course_item['teacher']}"
                    )
            else:
                print("No matching course found.")
        print("--- Course Inquiry Ended ---")


if __name__ == "__main__":
    print("--- Independently testing inquire_course_info.py ---")
    print("Ensure INQUIRY_USER_DATA in custom.py is correctly set (cookies).")
    print("Ensure ENROLLMENT_DATA_API_PARAMS in config.py is correctly set.")
    try:
        asyncio.run(inquire_course_info_async())
    except KeyboardInterrupt:
        print("\nInquiry test interrupted by user.")
    finally:
        print("--- Inquiry test finished ---")
