#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import requests

pixie_user = "<changeme>"
pixie_pwd = "<changeme>"
pixie_sender = "OP5"

def process_smsd_file(file):
    with open(file) as f:
        message = {}
        message['file_name'] = file
        for line in f.readlines():
            if line != "\n":
                line_data = line.split(':')
                if len(line_data) == 2:
                    message[line_data[0]] = line_data[1].strip().replace('\n', '')
            else:
                pass
        # Set the last line as the body.
        message['Body'] = line
    return message

def send_sms(message):

    try:
        r = requests.get('http://smsserver.pixie.se/sendsms?account=' + pixie_user + '&pwd=' + pixie_pwd +'&receivers=' + message['To'] +'&sender=' + pixie_sender + '&message=' + message['Body'])
        if r.status_code == 200:
            return True
        else:
            print r.text
            return False
    except:
        return False

# Looop through all files.
for filename in os.listdir(sys.argv[1] + "/outgoing"):
    message = process_smsd_file(os.path.abspath(sys.argv[1] + "/outgoing/" + filename))
    if send_sms(message):
        os.rename(message['file_name'], os.path.join(sys.argv[1] + "/sent/" + filename))
    else:
        os.rename(message['file_name'], os.path.join(sys.argv[1] + "/failed/" + filename))