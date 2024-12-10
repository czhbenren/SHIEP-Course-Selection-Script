import requests
import json
import sys
import re
import warnings
from urllib3.exceptions import InsecureRequestWarning
from config import headers, params, proxies
from custom import cookies

warnings.simplefilter("ignore", InsecureRequestWarning)


def fix_nonstandard_json(data):
    data = re.sub(r"(?<!\\)'", '"', data)  # 替换单引号为双引号
    data = re.sub(r"(\b[a-zA-Z_]\w*\b)(?=\s*:)", r'"\1"', data)  # 为未用引号包裹的属性名添加双引号
    return data


def parse_course_json(data):
    try:
        parsed_data = json.loads(data)
        print("Course data parsed successfully!")
        return parsed_data
    except json.JSONDecodeError:
        print("Course data is non-standard JSON data! Attempting to fix.")
        fixed_data = fix_nonstandard_json(data)
        try:
            parsed_data = json.loads(fixed_data)
            print("Course data parsed successfully after fixing!")
            return parsed_data
        except json.JSONDecodeError:
            print("Parsing still failed after attempting to fix.")
            sys.exit(1)


def get_course_data(profile_id):
    url = f"https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId={profile_id}"
    response = requests.get(
        url=url,
        headers=headers,
        cookies=cookies,
        params=params,
        proxies=proxies,
        verify=False,
    )
    response.encoding = "utf-8"
    if response.status_code == 200:
        raw_data = response.text.strip()
        json_data = re.search(r"\[.*\]", raw_data, re.DOTALL)
        if json_data:
            return parse_course_json(json_data.group())
        else:
            print("Failed to retrieve valid course data.")
            sys.exit(1)
    else:
        print("Failed to retrieve course data.")
        sys.exit(1)


def get_enrollment_data():
    url = "https://jw.shiep.edu.cn/eams/stdElectCourse!queryStdCount.action?projectId=1&semesterId=364"
    response = requests.get(
        url=url,
        headers=headers,
        cookies=cookies,
        params=params,
        proxies=proxies,
        verify=False,
    )
    response.encoding = "utf-8"
    if response.status_code == 200:
        raw_data = response.text
        json_data = re.search(r"\{.*\}", raw_data, re.DOTALL)
        if json_data:
            return parse_course_json(json_data.group())
        else:
            print("Failed to retrieve valid enrollment data.")
            sys.exit(1)
    else:
        print("Failed to retrieve enrollment data.")
        sys.exit(1)


def filter_courses(courses: list, keyword: str, enrollments: dict):
    filtered_courses = []
    for course in courses:
        if keyword.lower() in course["name"].lower():
            lesson_id = str(course["id"])
            sc = enrollments.get(lesson_id, {}).get("sc", "Unknown")
            lc = enrollments.get(lesson_id, {}).get("lc", "Unknown")
            filtered_courses.append(
                {
                    "id": course["id"],
                    "no": course["no"],
                    "name": course["name"],
                    "credits": course["credits"],
                    "course_type": course["courseTypeName"],
                    "teachers": course["teachers"],
                    "enrolled": sc,
                    "limit": lc,
                }
            )
    return filtered_courses


def inquire_course_info():
    profile_id = input("Input profileId: ").strip()
    courses = get_course_data(profile_id)
    enrollments = get_enrollment_data()
    while True:
        keyword = input("\nInput course name keyword (type 'q' to quit): ").strip()
        if keyword.lower() == "q":
            print("Exit the program.")
            sys.exit(0)
        filtered_courses = filter_courses(courses, keyword, enrollments)
        if filtered_courses:
            filtered_courses.sort(key=lambda x: (x["course_type"], -x["credits"], x["id"]))
            print("The matching course information is as follows:")
            for course in filtered_courses:
                print(
                    f"ID: {course['id']}, No: {course['no']}, Type: {course['course_type']}, Credits: {course['credits']}, Enrolled: {course['enrolled']}, Limit: {course['limit']}, Name: {course['name']}, Teacher: {course['teachers']}"
                )
        else:
            print("No matching course found.")


if __name__ == "__main__":
    inquire_course_info()
