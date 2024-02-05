import asyncio
import willump
import time
import requests
import sys
import os
from requests.packages import urllib3

#状态
Found = "Found" 
Invalid = "Invalid" 
Searching = "Searching"
searchStateURL = "/lol-lobby/v2/lobby/matchmaking/search-state"
foundacceptURL = "/lol-matchmaking/v1/ready-check/accept"
ingameURL = "https://127.0.0.1:2999/liveclientdata/eventdata?eventID=0"

#队列信息 t1
async def get_summoner_data():
    state = await (await wllp.request("GET", searchStateURL)).json()
    return state['searchState']

#点击确定
async def Found():
    global wllp
    wllp = await willump.start()
    await wllp.request('POST', foundacceptURL)
    await wllp.close()

#游戏内信息 t2
def ingamecheck():
    try:
        urllib3.disable_warnings()
        state=requests.get(ingameURL,verify=False,timeout=1.000)
        return(200)
    except BaseException:
        return(0)

async def main():
    global wllp
    wllp = await willump.start()
    t1 = await get_summoner_data()
    await wllp.close()
    return t1

#启动
if __name__ == '__main__':
    while True:
        t1 = asyncio.run(main())
        t2 = ingamecheck()
        if t2 == 200:
            os._exit(0)
            sys.exit()
        elif t1 == Found:
            asyncio.run(Found())
            time.sleep(10)
            continue
        elif t1 == Invalid:
            time.sleep(2)
            continue
        elif t1 == Searching:
            time.sleep(1)
            continue
        else:
            break
