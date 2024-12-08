import requests
import json
import re
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

from config import headers, params, proxies
from custom import cookies


def fix_nonstandard_json(data):
    """
    修复非标准JSON格式：
    1. 替换单引号为双引号（同时保留JSON内的有效单引号）。
    2. 为属性名添加双引号。
    """
    # 替换单引号为双引号
    data = re.sub(r"(?<!\\)'", '"', data)
    # 为未用引号包裹的属性名添加双引号
    data = re.sub(r'(\b[a-zA-Z_]\w*\b)(?=\s*:)', r'"\1"', data)
    return data


def parse_lesson_json(data):
    """
    修复并解析非标准JSON数据。
    """
    try:
        # 尝试直接解析
        return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"初次解析失败: {e}")
        # 修复后重新解析
        fixed_data = fix_nonstandard_json(data)
        try:
            print("修复后解析成功!")
            return json.loads(fixed_data)
        except json.JSONDecodeError as e:
            print(f"修复后解析失败: {e}")
            return []


def get_course_data(profile_id):
    """
    请求课程数据, 返回解析后的JSON对象。
    """
    url = f"https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId={profile_id}"
    response = requests.get(url=url, headers=headers, cookies=cookies, params=params, proxies=proxies, verify=False)
    response.encoding = 'utf-8'
    if response.status_code == 200:
        raw_data = response.text.strip()
        json_data = re.search(r'\[.*\]', raw_data, re.DOTALL)  # 提取数组部分
        if json_data:
            return parse_lesson_json(json_data.group())
        else:
            print("未找到有效的课程数据部分!")
            return []
    else:
        print("获取课程数据失败!")
        return []


def get_enrollment_data():
    """
    请求报名人数数据, 返回lessonId与人数信息的映射。
    """
    url = "https://jw.shiep.edu.cn/eams/stdElectCourse!queryStdCount.action?projectId=1&semesterId=364"
    response = requests.get(url=url, headers=headers, cookies=cookies, params=params, proxies=proxies, verify=False)
    response.encoding = 'utf-8'
    if response.status_code == 200:
        raw_data = response.text
        json_data = re.search(r'\{.*\}', raw_data, re.DOTALL)  # 提取对象部分
        if json_data:
            return parse_lesson_json(json_data.group())
        else:
            print("未找到有效的报名数据部分!")
            return {}
    else:
        print("获取报名人数数据失败!")
        return {}


def filter_courses(courses, keyword, enrollments):
    """
    根据关键字过滤课程, 并补充报名人数信息。
    """
    filtered_courses = []
    for course in courses:
        if keyword in course['name']:
            lesson_id = str(course['id'])
            sc = enrollments.get(lesson_id, {}).get('sc', '未知')
            lc = enrollments.get(lesson_id, {}).get('lc', '未知')
            filtered_courses.append({
                'id': course['id'],
                'no': course['no'],
                'name': course['name'],
                'course_type': course['courseTypeName'],
                'credits': course['credits'],
                'enrolled': sc,
                'limit': lc
            })
    return filtered_courses


def main():
    profile_id = input("请输入profileId: ")
    courses = get_course_data(profile_id)
    enrollments = get_enrollment_data()

    while True:
        keyword = input("请输入课程名称的关键字(输入'q'退出): ")
        if keyword.lower() == 'q':
            print("退出程序。")
            break
        filtered_courses = filter_courses(courses, keyword, enrollments)
        if filtered_courses:
            print("\n匹配的课程信息如下:")
            for course in filtered_courses:
                print(f"ID: {course['id']}, No: {course['no']}, 类型: {course['course_type']}, 学分: {course['credits']}, 当前人数: {course['enrolled']}, 限制人数: {course['limit']}, 名称: {course['name']}")
        else:
            print("未找到匹配的课程。")


if __name__ == "__main__":
    main()
