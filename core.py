import requests
import threading
import sys
import time

import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

from config import url, headers, params, data, proxies, failed_words, error_words
from custom import cookies

current_course_data = data

succeed = threading.Event ()

def select_course ():
    try:
        response = requests.post (url=url, headers=headers, cookies=cookies, params=params, data=current_course_data, proxies=proxies, timeout=3, verify=False)
        if response.status_code == 200:
            print (response.text)
            if any (i in response.text for i in failed_words):
                print ("Cannot select this course, maybe it's full or due to other reasons.\n")
            elif any (i in response.text for i in error_words):
                print ("Selection failed.\n")
            elif '已经选过' in response.text:
                print ("Already succeeded!\n")
                succeed.set ()
            else:
                print ("Succeeded!\n")
                succeed.set ()
        else:
            print (response.status_code)
            print ("Non-200 return.\n")
    except Exception as e:
        print (e)
        print ("Exception Occurred.\n")
    return False

def repeat_selection ():
    while not succeed.is_set ():
        thread = threading.Thread (target=select_course)
        thread.start ()
        time.sleep (0.2)

if __name__ == "__main__":
    if len (sys.argv) < 2:
        print ("Missing parameter! Usage: python core.py <course_id>")
        sys.exit (1)
    if len (sys.argv) > 2:
        print ("Too many parameters! Usage: python core.py <course_id>")
        sys.exit (1)
    course_id = sys.argv[1]
    current_course_data['operator0'] = f"{course_id}:true:0"
    repeat_selection ()
    wait = input ("The course selection has ended. Press any key and enter to exit.")