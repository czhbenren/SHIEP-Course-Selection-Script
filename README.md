# SHIEP 选课脚本

这是一个用于自动化处理上海电力大学 (SHIEP) 课程注册系统的脚本, 支持异步 HTTP 请求, 方便批量选课、查询课程、验证 Cookie 等操作适合需要快速选课或查询课程信息的同学

## 功能

- **自动选课**: 为多个用户批量注册课程
- **课程查询**: 按关键字 (如课程名) 或条件 (如 `teacher=张三`) 查询课程信息
- **Cookie 验证**: 检查用户配置中的 Cookie 是否有效
- **课程可用性检查**: 验证指定课程是否可注册

## 安装与配置

### 1. 安装依赖

- 确保已安装 Python 3.9+
- 运行以下命令安装所需库:
  ```bash
  pip install -r requirements.txt
  ```

### 2. 配置 `custom.py`

- **准备文件**:
  - 将 `custom.py.example` 复制为 `custom.py` (例如: `cp custom.py.example custom.py`)
  - 编辑 `custom.py`, 添加用户信息、课程配置和查询用户数据
- **配置格式**: 以人为单位, 每人一个配置对象, 包含 `label` (用户标识) 、`tables` (档案和课程信息) 、`cookies` (登录凭证)示例:
  ```python
  USER_CONFIGS = [
      {
          "label": "User_Alice",  # 用户标签, 方便区分
          "tables": [
              {
                  "profileId": "114514",  # 个人档案 ID
                  "course_ids": [
                      "COURSEID_A1",  # 课程 ID
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
              "JSESSIONID": "ALICE_SESSION_ID_HERE",  # 登录会话 ID
              "SERVERNAME": "c1",  # 服务器名称
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
- **查询用户配置**: 为课程查询功能配置单独的 `INQUIRY_USER_DATA`, 示例:
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
- **如何获取 Cookie**:
  - 打开浏览器, 按 F12 进入开发者工具, 推荐以下步骤:
    1. **首选**: 切换到“应用程序” (Application) 标签页, 在左侧找到“存储” (Storage) ->“Cookie”, 点击 `https://jw.shiep.edu.cn`, 找到 `JSESSIONID` 和 `SERVERNAME`, 复制其值
    2. **备选**: 切换到“网络” (Network) 标签页, 登录教务系统后, 检查请求 (如登录或主页请求), 找到 `Cookie` 头中的 `JSESSIONID` 和 `SERVERNAME`
  - 或者使用 [curlconverter](https://curlconverter.com/) 转换 cURL 请求获取 Cookie
- **如何获取课程 ID**:
  - 使用脚本的“查询课程”功能 (运行 `python main.py --inquire`)
  - 或者访问教务系统 URL: `https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId=<your_profile_id>`, 查看返回的课程数据
- **如何获取 `profileId`**:
  - 从上述 URL 或教务系统个人页面中获取, 确保与 Cookie 对应

### 3. 配置 `config.py`

- **代理设置**:
  - 如果使用**官方 EasyConnect VPN**连接校内网络, 无需设置代理, 直接设置:
    ```python
    USE_PROXY = False
    ```
  - 如果使用**第三方 VPN** (如 EasierConnect 等), 需设置 `USE_PROXY = True` 并配置代理地址, 例如:
    ```python
    USE_PROXY = True
    proxies = {
        "all": "socks5://127.0.0.1:10114",  # 替换为你的代理地址和端口
    }
    ```
  - 第三方 VPN 需要安装 `aiohttp-socks` (已包含在 `requirements.txt` 中)
- **API 参数**: 配置学期和项目参数, 示例:
  ```python
  ENROLLMENT_DATA_API_PARAMS = {
      "projectId": "1",
      "semesterId": "384",
  }
  ```
  - 确认 `projectId` 和 `semesterId` 与当前学期一致, 可从教务系统请求中获取

### 4. 运行脚本

- 在终端运行:
  ```bash
  python main.py <命令>
  ```
- 可用命令:
  - `--start`: 为 `USER_CONFIGS` 中的所有用户自动选课
  - `--inquire`: 查询课程信息, 支持按关键字 (如课程名) 或条件 (如 `teacher=张三`) 搜索, 输入 `q` 退出
  - `--validate`: 批量验证 `USER_CONFIGS` 中 Cookie 的有效性
  - `--check`: 检查指定课程是否可注册
- 示例:
  ```bash
  python main.py --start  # 开始选课
  python main.py --inquire  # 查询课程
  ```

### 5. 中止运行

- 按 `Ctrl+C` 随时中断脚本, 程序会显示“Program interrupted by user”并安全退出

## 注意事项

- **Cookie 有效性**: 确保 `JSESSIONID` 和 `SERVERNAME` 有效, 过期或错误的 Cookie 会导致选课失败
- **代理设置**: 使用 EasyConnect 时无需代理；第三方 VPN 需正确配置代理地址和端口
- **课程 ID 准确性**: 选课前确认 `course_ids` 和 `profileId` 正确, 避免选错课程
- **SSL 验证**: 脚本默认禁用 SSL 验证, 请确保教务系统服务器可信
- **调试**: 运行 `--validate` 或 `--check` 检查配置是否正确

## 常见问题

- **Cookie 失效怎么办？**
  重新登录教务系统, 获取新的 `JSESSIONID` 和 `SERVERNAME`, 更新 `custom.py`
- **课程 ID 找不到？**
  使用 `--inquire` 功能查询课程, 或检查教务系统数据接口
- **代理连接失败？**
  - 确认是否使用 EasyConnect (无需代理) 或第三方 VPN (需配置代理)
  - 检查代理地址和端口, 或设置 `USE_PROXY = False` 禁用代理

## 贡献

欢迎提交 issue 或 pull request 改进脚本！如有问题, 请在 GitHub 仓库反馈
