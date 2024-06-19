import time
import requests
from requests.packages import urllib3
import psutil
import base64
from urllib.parse import urljoin
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit
from PyQt5.QtCore import QDateTime
from threading import Thread
import sys


#常量定义
BASE_URL  = "https://127.0.0.1:"
Found = "Found" 
Invalid = "Invalid" 
Searching = "Searching"
SEARCH_STATE_URL  = "/lol-lobby/v2/lobby/matchmaking/search-state"
FOUND_ACCEPT_URL  = "/lol-matchmaking/v1/ready-check/accept"
SUMMONER_DATA_URL  = "/lol-summoner/v1/current-summoner"


class MyProgram(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('lol自动点击开始')
        self.setFixedSize(500, 475)

        self.start_button = QPushButton('开始', self)
        self.start_button.setGeometry(50, 400, 160, 50)
        self.start_button.clicked.connect(self.start_auto_click)

        self.stop_button = QPushButton('结束', self)
        self.stop_button.setGeometry(300, 400, 150, 50)
        self.stop_button.clicked.connect(self.stop_auto_click)
        self.stop_button.setEnabled(False)

        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(50, 25, 400, 350)
        
        tishi = [
            '这里显示日志',
            '请启动客户端后点击开始按钮',
            '进入游戏后会自动停止',
            '点击开始后会清空日志'
        ]
        self.text_edit.setText('\n'.join(tishi))
        self.text_edit.setReadOnly(True)
        
        self.auto_click_thread = None
        self.auto_click_running = False


    def start_auto_click(self):
        if not self.auto_click_running:
            self.text_edit.clear()
            current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
            self.text_edit.append(f'{current_time}: 启动')
            self.auto_click_running = True
            self.auto_click_thread = Thread(target=self.run_auto_click)
            self.auto_click_thread.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            

    def stop_auto_click(self):
        current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
        self.text_edit.append(f'{current_time}: 已停止')
        self.auto_click_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def run_auto_click(self):
        #self.text_edit.append('状态: 查找客户端')
        pid = find_league_client_pid()
        if not pid:
            current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
            self.text_edit.append(f'{current_time}: 未找到客户端，请确保客户端已启动后点击开始。')
            self.stop_auto_click()
        else:
            urllib3.disable_warnings()
            port, headers = get_port_token_headers(pid)
        if not port and headers:
            current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
            self.text_edit.append(f'{current_time}: 未能获取到端口和头信息,软件多半需要更新')
            self.stop_auto_click()
        #print(port, headers)
        #self.text_edit.append('状态: 查找队列状态')
        
        while self.auto_click_running:   
            state = get_search_state(port, headers)
            game_pid = find_league_game_pid()
            if game_pid:
                current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
                self.text_edit.append(f'{current_time}: 检测到进入游戏自动停止')
                self.stop_auto_click()
                break
            elif not state:
                current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
                self.text_edit.append(f'{current_time}: 出现异常，自动停止')
                self.stop_auto_click()
                break
            elif state == Invalid:
                current_time = QDateTime.currentDateTime().toString('HH:mm:ss')
                self.text_edit.append(f'{current_time}: 没在队列等待5秒')
                time.sleep(5)
                continue
            elif state == Searching:
                self.text_edit.append('状态: 队列中')
                accept_found(port, headers)
                time.sleep(1)
                continue

            print(state)
    def QLineEdit(self, text):
        self.text_edit.append(text)


#获取客户端pid
def find_league_client_pid():
    process = psutil.pids()
    for pid in process:
        if psutil.Process(pid).name() == 'LeagueClientUx.exe':
            return pid
    else:
        return None
    
#获取游戏客户端pid
def find_league_game_pid():
    process = psutil.pids()
    for pid in process:
        if psutil.Process(pid).name() == 'League of Legends.exe':
            return pid
    else:
        return None

#获取客户端port和headers
def get_port_token_headers(pid):
    port, token= None, None
    process = psutil.Process(pid)
    cmdline = process.cmdline()
    for cmd in cmdline:
        p = cmd.find("--app-port=")
        if p != -1:
            port = cmd[11:]
        p = cmd.find("--remoting-auth-token=")
        if p != -1:
            token = cmd[22:]
        if port and token:
            authorization_header = "Basic " + base64.b64encode(('riot:' + token).encode('utf-8')).decode('utf-8')
            headers = {
	            "Authorization": authorization_header
                }
            break
        
    return port, headers

#【没有使用】获取召唤师信息
def get_summoner(port, headers):
    url = urljoin(BASE_URL + port, SUMMONER_DATA_URL)
    try:
        response =requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"获取召唤师信息时出错: {e}")
        return None

#队列信息 t1
def get_search_state(port, headers):
    url = urljoin(BASE_URL + port, SEARCH_STATE_URL)
    try:
        response = requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        return response.json().get('searchState')
    except requests.exceptions.RequestException as e:
        print(f"获取队列信息时出错: {e}")
        return None

#点击确定
def accept_found(port, headers):
    url = urljoin(BASE_URL + port, FOUND_ACCEPT_URL)
    try:
        response=requests.post(url,headers=headers,verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"点击确定时出错: {e}")

#启动
app = QApplication(sys.argv)
# 设置暗黑模式样式表
dark_stylesheet = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QPushButton {
        background-color: #3a3a3a;
        color: #ffffff;
        border: 1px solid #5a5a5a;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
    QTextEdit {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #3a3a3a;
    }
    """

app.setStyleSheet(dark_stylesheet)
window = MyProgram()
window.show()
sys.exit(app.exec_())
