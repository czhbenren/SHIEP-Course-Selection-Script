# SHIEP-Course-Selection-Script
Course Selection Script for SHIEP

**本项目目标平台仅为Windows, 若Linux或Mac用户要运行此项目, 则需要根据自己终端环境修改main.py中subprocess.Popen函数的传参列表**  

## 使用方式
**修改custom.py.example并保存为custom.py文件, 在里面存放cookies与课程id列表,** cookies可通过浏览器F12的网络页抓取选课的包 (其实只有**JSESSIONID**和**SERVERNAME**是关键的，直接在包里找到复制也可以), 右键复制为cURL(bash), 粘贴到[curlconverter](https://curlconverter.com/)网站的文本框中, 下方选择Python(默认)直接复制整个cookies字典写入custom.py即可, 课程id也可通过此方法获取, 不过太费力, 每个课程都要来一遍, 可以直接通过此[API](https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId=1614)便捷获取所有可选课程信息, 随后通过课程序号昵称或老师等关键信息来快速定位课程id, 并填入custom.py的course_ids列表中

要使用第三方VPN, 将config.py中的proxies修改为自己的代理协议和地址, **若使用官方VPN或校园网直连, 则删去core.py中函数requests.post传参列表内的proxies=proxies方可使用**

**用Python运行main.py以开始**