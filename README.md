# SHIEP Course Selection Script

This is a script for automating the SHIEP course registration system, supporting asynchronous HTTP requests, making it convenient for batch course selection, course inquiry, cookie validation, and other operations. It is suitable for students who need to quickly select or query course information.

## Features

- **Automatic Course Selection**: Batch register courses for multiple users.
- **Course Inquiry**: Query course information by keyword (e.g., course name) or condition (e.g., `teacher=Smith`). 
- **Cookie Validation**: Check the validity of cookies in user configurations.
- **Course Availability Check**: Verify if specified courses are available for registration.

## Installation and Configuration

### 1. Install Dependencies

- Ensure Python 3.9+ is installed.
- Run the following command to install required libraries:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Configure `custom.py`

- **Prepare the File**:
  - Copy `custom.py.example` to `custom.py` (e.g., `cp custom.py.example custom.py`).
  - Edit `custom.py` to add user information, course configurations, and inquiry user data.
- **Configuration Format**: Organized by user, each user has one configuration object containing `label` (user identifier), `tables` (profile and course information), and `cookies` (login credentials). Example:
  ```python
  USER_CONFIGS = [
      {
          "label": "User_Alice",  # User label for identification
          "tables": [
              {
                  "profileId": "114514",  # Personal profile ID
                  "course_ids": [
                      "COURSEID_A1",  # Course ID
                      "COURSEID_A2",
                  ],
              },
              {
                  "profileId": "1919810",
                  "course_ids": [
                      "COURSEID_B1",
                      "COURSEID_B2",
                  ],
              },
          ],
          "cookies": {
              "JSESSIONID": "ALICE_SESSION_ID_HERE",  # Login session ID
              "SERVERNAME": "c1",  # Server name
          },
      },
      {
          "label": "User_Bob",
          "tables": [
              {
                  "profileId": "233",
                  "course_ids": [
                      "COURSEID_C1",
                      "COURSEID_C2",
                  ],
              },
          ],
          "cookies": {
              "JSESSIONID": "BOB_SESSION_ID_HERE",
              "SERVERNAME": "c2",
          },
      },
      # ... other user configs for selection ...
  ]
  ```
- **Inquiry User Configuration**: Configure a separate `INQUIRY_USER_DATA` for the course inquiry function. Example:
  ```python
  INQUIRY_USER_DATA = {
      "label": "DefaultInquiryUser",
      "profileId": "114514",
      "cookies": {
          "JSESSIONID": "YOUR_INQUIRY_JSESSIONID_HERE",
          "SERVERNAME": "YOUR_INQUIRY_SERVERNAME_HERE",
      },
  }
  ```
- **How to Obtain Cookies**:
  - Open the browser, press F12 to enter developer tools, and follow these steps:
    1. **Preferred**: Switch to the “Application” tab, find “Storage” -> “Cookies” on the left, click `https://jw.shiep.edu.cn`, locate `JSESSIONID` and `SERVERNAME`, and copy their values.
    2. **Alternative**: Switch to the “Network” tab, log into the course registration system, check requests (e.g., login or homepage requests), and find `JSESSIONID` and `SERVERNAME` in the `Cookie` header.
  - Alternatively, use [curlconverter](https://curlconverter.com/) to convert cURL requests to obtain cookies.
- **How to Obtain Course IDs**:
  - Use the script’s “course inquiry” function (run `python main.py --inquire`).
  - Alternatively, visit the course system URL: `https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId=<your_profile_id>` to view the returned course data.
- **How to Obtain `profileId`**:
  - Retrieve it from the above URL or the personal page in the course system, ensuring it matches the cookies.

### 3. Configure `config.py`

- **Proxy Settings**:
  - If using the **official EasyConnect VPN** to connect to the campus network, no proxy is needed. Set:
    ```python
    USE_PROXY = False
    ```
  - If using a **third-party VPN** (e.g., EasierConnect), set `USE_PROXY = True` and configure the proxy address, for example:
    ```python
    USE_PROXY = True
    proxies = {
        "all": "socks5://127.0.0.1:10114",  # Replace with your proxy address and port
    }
    ```
  - Third-party VPNs require `aiohttp-socks` (included in `requirements.txt`).
- **API Parameters**: Configure semester and project parameters. Example:
  ```python
  ENROLLMENT_DATA_API_PARAMS = {
      "projectId": "1",
      "semesterId": "384",
  }
  ```
  - Ensure `projectId` and `semesterId` match the current semester, obtainable from course system requests.

### 4. Run the Script

- Run in the terminal:
  ```bash
  python main.py <command>
  ```
- Available commands:
  - `--start`: Automatically select courses for all users in `USER_CONFIGS`.
  - `--inquire`: Query course information, supporting searches by keyword (e.g., course name) or condition (e.g., `teacher=Smith`). Enter `q` to exit.
  - `--validate`: Batch validate the cookies in `USER_CONFIGS`.
  - `--check`: Check if specified courses are available for registration.
- Examples:
  ```bash
  python main.py --start  # Start course selection
  python main.py --inquire  # Query courses
  ```

### 5. Stop the Script

- Press `Ctrl+C` to interrupt the script at any time. The program will display “Program interrupted by user” and exit safely.

## Notes

- **Cookie Validity**: Ensure `JSESSIONID` and `SERVERNAME` are valid. Expired or incorrect cookies will cause course selection to fail.
- **Proxy Settings**: No proxy is needed with EasyConnect; third-party VPNs require correct proxy address and port configuration.
- **Course ID Accuracy**: Verify `course_ids` and `profileId` before selecting courses to avoid errors.
- **SSL Verification**: The script disables SSL verification by default. Ensure the course system server is trusted.
- **Debugging**: Run `--validate` or `--check` to verify configuration correctness.

## Common Issues

- **What if cookies expire?**  
  Log into the course system again, obtain new `JSESSIONID` and `SERVERNAME`, and update `custom.py`.
- **Can’t find course IDs?**  
  Use the `--inquire` function to query courses or check the course system data interface.
- **Proxy connection failed?**  
  - Confirm whether you’re using EasyConnect (no proxy needed) or a third-party VPN (proxy required).  
  - Check the proxy address and port, or set `USE_PROXY = False` to disable the proxy.

## Contribution

We welcome issues or pull requests to improve the script! For any questions, please provide feedback in the GitHub repository.