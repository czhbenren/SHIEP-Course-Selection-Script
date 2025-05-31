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


def fix_nonstandard_json(data_str: str) -> str:
    data_str = re.sub(r"(?<!\\)'", '"', data_str)
    data_str = re.sub(r"(?<=[{,])\s*([a-zA-Z_]\w*)\s*:", r'"\1":', data_str)
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


def add_course_to_config(label: str, course_id: str, profile_id: str, courses: list):
    """
    Add a course to USER_CONFIGS if it exists in the query results.
    """
    if not any(str(course["id"]) == course_id for course in courses):
        print(f"Error: Course ID {course_id} not found in the query results.")
        return False

    # Read the current custom.py content
    with open("custom.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Find the last closing bracket of USER_CONFIGS
    last_bracket_pos = content.rfind("]")
    if last_bracket_pos == -1:
        print("Error: Could not find USER_CONFIGS in custom.py")
        return False

    # Check if a config with this label already exists
    label_pattern = f'"label": "{label}"'
    label_pos = content.find(label_pattern)

    if label_pos != -1:
        # Find the course_ids list for this label
        course_ids_start = content.find('"course_ids": [', label_pos)
        if course_ids_start == -1:
            print(f"Error: Could not find course_ids list for label {label}")
            return False

        # Find the closing bracket of the course_ids list
        course_ids_end = content.find("]", course_ids_start)
        if course_ids_end == -1:
            print(f"Error: Could not find end of course_ids list for label {label}")
            return False

        # Check if the course ID already exists
        if course_id in content[course_ids_start:course_ids_end]:
            print(f"Error: Course ID {course_id} already exists for label {label}")
            return False

        # Get the content before the closing bracket
        before_end = content[:course_ids_end].rstrip()
        # Add the new course ID with proper formatting
        if before_end.endswith('"'):
            # If the last item ends with a quote, add a comma and the new ID
            new_content = before_end + f'\n            "{course_id}",\n        ' + content[course_ids_end:]
        else:
            # If there's already a comma or other formatting, just add the new ID
            new_content = before_end + f'\n            "{course_id}",\n        ' + content[course_ids_end:]
    else:
        # Create a new user config
        new_config = f"""
    {{
        "label": "{label}",
        "profileId": "{profile_id}",
        "cookies": {{
            "JSESSIONID": "{INQUIRY_USER_DATA["cookies"]["JSESSIONID"]}",
            "SERVERNAME": "{INQUIRY_USER_DATA["cookies"]["SERVERNAME"]}",
        }},
        "course_ids": [
            "{course_id}",
        ],
    }},\n"""

        # Insert the new config before the last bracket
        # 这里不知道为什么最后多了个换行符，导致json格式错误
        new_content = content[: last_bracket_pos - 1] + new_config + content[last_bracket_pos:]

    # Write back to custom.py
    with open("custom.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully added course {course_id} for user {label}")
    return True


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
        key_mapping = {
            "id": "id",
            "no": "no",
            "name": "name",
            "credits": "credits",
            "courseTypeName": "type",
            "teachers": "teacher",
        }
        courses = [{new_key: course.get(old_key, "") for old_key, new_key in key_mapping.items()} for course in courses]

        print("Fetching enrollment data...")
        enrollments = await get_enrollment_data_async(session, inquiry_cookies)
        if not enrollments:
            print("Could not fetch enrollment data. Exiting inquiry.")
            return

        print("\n--- Course Inquiry Ready ---")
        while True:
            keyword = input("\nInput course name keyword or 'key=value' to search by field ('q' to quit): ").strip().lower()
            if keyword == "q":
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

                # Ask if user wants to add a course to USER_CONFIGS
                match input("\nDo you want to add one or all course filtered to USER_CONFIGS? (Y/n): ").strip().upper():
                    case "Y" | "":
                        label = input("Enter the label for the new user config: ").strip()
                        if not label:
                            print("Failed to add: Label cannot be empty.")
                            continue

                        if len(filtered) == 1:
                            # If there's only one course, use it directly
                            course_id = str(filtered[0]["id"])
                            print(f"Automatically using the only matching course ID: {course_id}")
                            add_course_to_config(label, course_id, profile_id_to_use, courses)
                        else:
                            # If there are multiple courses, ask for the course ID
                            course_id = input("Enter the course ID to add (or 'all' to add all matching courses): ").strip()
                            if not course_id:
                                print("Error: Course ID cannot be empty.")
                                continue

                            if course_id.lower() == "all":
                                # Add all matching courses
                                success_count = 0
                                for course in filtered:
                                    if add_course_to_config(label, str(course["id"]), profile_id_to_use, courses):
                                        success_count += 1
                                print(f"Successfully added {success_count} out of {len(filtered)} courses for user {label}")
                            else:
                                add_course_to_config(label, course_id, profile_id_to_use, courses)
                    case _:
                        pass
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
