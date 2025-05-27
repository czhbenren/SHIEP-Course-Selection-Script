# SHIEP Course Selection Script

Automates course selection and inquiry for SHIEP's course registration system using asynchronous HTTP requests.

## Usage
1. **Install Dependencies**: Run `pip install -r requirements.txt`.
2. **Configure `custom.py`**:
   - Add user configs (`label`, `profileId`, `cookies`, `course_ids`) and `INQUIRY_USER_DATA` with valid cookies (`JSESSIONID`, `SERVERNAME`).
   - Get cookies via browser dev tools (F12, Network tab) or [curlconverter](https://curlconverter.com/).
   - Get course IDs from `[2] Inquire courses` or `https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId=<your_profile_id>`.
3. **Configure `config.py`**:
   - Set `USE_PROXY` and `proxies` if using a VPN; otherwise, set `USE_PROXY = False`.
   - Verify `ENROLLMENT_DATA_API_PARAMS` (`projectId`, `semesterId`).
4. **Run**: Execute `python main.py`, choose:
   - `[1] Select courses`: Registers courses in `USER_CONFIGS`.
   - `[2] Inquire courses`: Search courses by keyword or `key=value` (e.g., `teacher=Smith`). Type `q` to quit.
5. **Interrupt**: Press `Ctrl+C` to stop.

## Notes
- Ensure valid cookies and profile IDs.
- Proxy requires `aiohttp-socks` if `USE_PROXY` is True.
- SSL verification is disabled; ensure server trust.