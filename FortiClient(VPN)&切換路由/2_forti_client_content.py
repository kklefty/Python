# VPN連接成功後，Default Gateway將會預設為VPN的ppp0
# 導致遠端無法SSH進入主機，必須在相同Vlan環境才能訪問
# 設置使腳本用途自動更改主機路由，連線成功後，將單一需訪問IP設置VPN Gateway

import re
import os
import time
import pexpect

# 匿名凾式，ppp0為參數，使用正則表達獲取IP，再是否為撥接'ppp0'。
get_gw = lambda x: re.search('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',x).group() if 'ppp0' in x else False

while True:
    gw = get_gw(os.popen('route').readlines()[2]) # 使用終端指令'route'並選取第三行數據(ppp0連接成功會顯示在此行)
    if gw == False:
        time.sleep(2)
        print('miss')
    else:
        break
print(gw)

# 運行終端更改刪除ppp0的 default，並增加訪問VPN主機的IP路由。
delvpndeful = pexpect.spawn('sudo route del default gw '+gw)
delvpndeful.sendline('Password\r')
time.sleep(0.5)
addh1 = pexpect.spawn('sudo route add 防火牆IP1 gw '+gw)
addh1.sendline('Password\r')
time.sleep(0.5)
addh2 = pexpect.spawn('sudo route add 防火牆IP2 gw '+gw)
addh2.sendline('Password\r')