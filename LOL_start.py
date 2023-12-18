import asyncio
import willump
import time
import sys
import os

#获取lol信息
async def get_summoner_data():
    summoner = await (await wllp.request("GET", "/lol-summoner/v1/current-summoner")).json()
    state = await (await wllp.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
    print(f"summonerName:    {summoner['displayName']}")
    print(f"summonerLevel:   {summoner['summonerLevel']}")
    print(f"searchState:     {state['searchState']}")
    print(f"---")
    return state['searchState']

#检测现在队列状态
async def main():
    global wllp
    wllp = await willump.start()
    t1 = await get_summoner_data()
    await wllp.close()
    return t1

#匹配到人后点击确定
async def Found():
    global wllp
    wllp = await willump.start()
    await wllp.request('POST', '/lol-matchmaking/v1/ready-check/accept')
    await asyncio.sleep(10)
    await wllp.close()

#启动
def search():
    while True:
        t1 = asyncio.run(main())
        print(t1)
        if t1 == 'Found':
            asyncio.run(Found())
            t1 = asyncio.run(main())
            if t1 == 'Invalid':
                os._exit(0)
                sys.exit()
            else:
                continue
        elif t1 == 'Invalid':
            time.sleep(2)
            continue
        elif t1 == 'Searching':
            continue
        else:
            break

if __name__ == '__main__':
    search()