import subprocess

from inquire_course_info import inquire_course_info
from custom import course_ids

if __name__ == "__main__":
    task = input("What do you want to do? [1] Select course [2] inquire_course_info\n").strip()
    match task:
        case "1":
            for course_id in course_ids:
                subprocess.Popen(["start", "python", "./core.py", course_id], shell=True)
                print(f"Assigned course {course_id} selection to a new subprocess.")
        case "2":
            inquire_course_info()
