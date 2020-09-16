#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python example script showing proper use of the Cisco Sample Code header.
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by pytthe License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


from handler import *
import requests
import datetime
import json
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Authentication:
    global header

    @staticmethod
    def get_jsessionid(vmanage_host, username, password):
        api = "/j_security_check"
        base_url = "https://%s" % (vmanage_host)
        url = base_url + api
        payload = {'j_username': username, 'j_password': password}

        response = requests.post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")
            return (jsessionid[0])
        except:
            print("No valid JSESSION ID returned\n")
            exit()

    @staticmethod
    def get_token(vmanage_host, jsessionid):
        headers = {'Cookie': jsessionid}
        base_url = "https://%s" % (vmanage_host)
        api = "/dataservice/client/token"
        url = base_url + api
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            return (response.text)
        else:
            return None


def what_time_day():
    current = datetime.datetime.now()
    now = {}
    now['time'] = current.strftime("%H:%M")
    now['day'] = current.strftime("%A").lower()
    return now


def check_policy(url, username, password):
    VMANAGE = url
    J_USERNAME = username
    J_PASSWORD = password

    # Check time
    now = what_time_day()
    time = now['time']
    day = now['day']
    print('Time:', time)
    print('Day:', day)

    #auth to vmanage
    Auth = Authentication()
    jsessionid = Auth.get_jsessionid(VMANAGE, J_USERNAME, J_PASSWORD)
    token = Auth.get_token(VMANAGE, jsessionid)

    if token is not None:
        header = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
    else:
        header = {'Content-Type': "application/json", 'Cookie': jsessionid}

    pp.pprint(header)

    # check policies to be activated/deactivated
    starting = Policy.query.filter_by(day=day).filter_by(start=time).first()
    ending = Policy.query.filter_by(day=day).filter_by(end=time).first()

    if ending:
        try:
            payload = {}
            deactivation_url = f"dataservice/template/policy/vsmart/deactivate/{ending.policyId}?confirm=true"
            print(f"Deactivating Policy {ending.policyName} with ID {ending.policyId}")
            deactivation_response = requests.post(
                url=f"https://{VMANAGE}/{deactivation_url}", headers=header, verify=False, data=json.dumps(payload)
            )
            if deactivation_response.status_code == 200:
                process_id = deactivation_response.json()['id']
                url = f"dataservice/device/action/status/{process_id}"
                while (1):
                    policy_status_res = requests.get(url=f"https://{VMANAGE}/{url}", headers=header, verify=False)
                    if policy_status_res.status_code == 200:
                        policy_push_status = policy_status_res.json()
                        if policy_push_status['summary']['status'] == "done":
                            if 'Success' in policy_push_status['summary']['count']:
                                print(f"Successfully deactivated vSmart Policy {ending.policyName}")
                            elif 'Failure' in policy_push_status['summary']['count']:
                                print(f"Failed to deactivate vSmart Policy {ending.policyName}")
                            break
            else:
                print(f"Failed to deactivate vSmart Policy {ending.policyName}")
        except Exception as e:
            print("ending error")
            print(e)

    if starting:
        try:
            payload = {}
            activation_url = f"dataservice/template/policy/vsmart/activate/{starting.policyId}?confirm=true"
            print(f"Activating Policy {starting.policyName} with ID {starting.policyId}")
            activation_response = requests.post(
                url=f"https://{VMANAGE}/{activation_url}", headers=header, verify=False, data=json.dumps(payload)
            )
            if activation_response.status_code == 200:
                process_id = activation_response.json()['id']
                url = f"dataservice/device/action/status/{process_id}"
                while (1):
                    policy_status_res = requests.get(url=f"https://{VMANAGE}/{url}", headers=header, verify=False)
                    if policy_status_res.status_code == 200:
                        policy_push_status = policy_status_res.json()
                        if policy_push_status['summary']['status'] == "done":
                            if 'Success' in policy_push_status['summary']['count']:
                                print(f"Successfully activated vSmart Policy {starting.policyName}")
                            elif 'Failure' in policy_push_status['summary']['count']:
                                print(f"Failed to activate vSmart Policy {starting.policyName}")
                            break
            else:
                print(f"Failed to activate vSmart Policy {starting.policyName}")
        except Exception as e:
            print("starting error")
            print(e)
