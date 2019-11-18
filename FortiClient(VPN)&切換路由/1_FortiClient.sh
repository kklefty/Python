#!/usr/bin/expect
spawn /home/alex/FortiSSL_VPN/forticlientsslvpn/64bit/forticlientsslvpn_cli --server FW_IP:port --vpnuser UserName
expect "Password for VPN:"
send "Password*****\r"
expect "Would you like to connect to this server? (Y/N)"
send "Y\r"
interact
