import subprocess

from custom import course_ids

if __name__ == "__main__":
    for course_id in course_ids:
        subprocess.Popen ([
            "start", "python", "./core.py", course_id
        ], shell=True)
        print (f"Assigned course {course_id} selection to a new subprocess.")