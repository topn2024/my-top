#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

cmd = f"echo {PASSWORD} | sudo -S journalctl -u topn -n 50 --no-pager"
stdin, stdout, stderr = ssh.exec_command(cmd)

print(stdout.read().decode('utf-8'))

ssh.close()
