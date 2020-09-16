#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python example script showing proper use of the Cisco Sample Code header.
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template, redirect, url_for, request

from DETAILS import *
from app import app
from scheduler import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
pp = pprint.PrettyPrinter(indent=2)
logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sched = BackgroundScheduler()

global header
global VMANAGE
global J_USERNAME
global J_PASSWORD


# vManage Authentication Class
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


# Login screen
@app.route('/', methods=['GET', 'POST'])
def index():
    global VMANAGE
    global J_USERNAME
    global J_PASSWORD
    print(VMANAGE)
    if request.method == 'GET':
        try:
            Auth = Authentication()
            jsessionid = Auth.get_jsessionid(VMANAGE, J_USERNAME, J_PASSWORD)
            token = Auth.get_token(VMANAGE, jsessionid)
            print('credentials found on file or already logged in')

            sched.add_job(check_policy, trigger='cron', minute='*', id='1', replace_existing=True,
                          args=[VMANAGE, J_USERNAME, J_PASSWORD])
            print("Scheduler Started")
            try:
                sched.start()
            except:
                pass
            return redirect(url_for('schedule'))
        except:
            print('credentials not found, redirecting to log in')
            return render_template('login.html', title='Log In')
    elif request.method == 'POST':
        details = request.form
        print(details)
        VMANAGE = details['url']
        J_USERNAME = details['username']
        J_PASSWORD = details['password']

        sched.add_job(check_policy, trigger='cron', minute='*', id='1', replace_existing=True,
                      args=[VMANAGE, J_USERNAME, J_PASSWORD])
        print("Scheduler Started")
        try:
            sched.start()
        except:
            pass
        return redirect(url_for('schedule'))


# Welcome screen
@app.route('/start', methods=['GET', 'POST'])
def schedule():
    try:
        Auth = Authentication()
        jsessionid = Auth.get_jsessionid(VMANAGE, J_USERNAME, J_PASSWORD)
        token = Auth.get_token(VMANAGE, jsessionid)

        if token is not None:
            header = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
        else:
            header = {'Content-Type': "application/json", 'Cookie': jsessionid}

        policy_url = "dataservice/template/policy/vsmart"
        policy_response = requests.get(
            url=f"https://{VMANAGE}/{policy_url}", headers=header, verify=False
        )
        policylist = policy_response.json()['data']

        if request.method == 'GET':
            return render_template('schedule.html', title='vSmart Policy Scheduler', policylist=policylist)
        elif request.method == 'POST':
            return redirect('schedule.html', code=302)
    except:
        print('credentials not found, redirecting to log in')
        return render_template('login.html', title='Log In')


# Policy selected
@app.route('/policy/<policyId>', methods=['GET', 'POST'])
def scheduling(policyId):
    try:
        Auth = Authentication()
        jsessionid = Auth.get_jsessionid(VMANAGE, J_USERNAME, J_PASSWORD)
        token = Auth.get_token(VMANAGE, jsessionid)

        if token is not None:
            header = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
        else:
            header = {'Content-Type': "application/json", 'Cookie': jsessionid}
        # pp.pprint(header)
        policy_url = "dataservice/template/policy/vsmart"
        policy_response = requests.get(
            url=f"https://{VMANAGE}/{policy_url}", headers=header, verify=False
        )
        policylist = policy_response.json()['data']

        selected_policy = next(item for item in policylist if item['policyId'] == policyId)

        if request.method == 'GET':
            return render_template('scheduling.html', title='vSmart Policy Scheduler', policylist=policylist,
                                   selected=selected_policy['policyName'], policyId=selected_policy['policyId'])
        elif request.method == 'POST':
            status = commit(request.form.to_dict(), policyId, selected_policy['policyName'])
            if status:
                return render_template('scheduling.html', title='vSmart Policy Scheduler', policylist=policylist,
                                       selected=selected_policy['policyName'], policyId=selected_policy['policyId'])
    except:
        print('credentials not found, redirecting to log in')
        return render_template('login.html', title='Log In')


# Populate the list of schedules
@app.route('/parser', methods=['POST'])
def parser():
    if request.method == 'POST':
        policyList = {}
        print(request.json)
        policyId = request.json["policyId"]
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            entries = Policy.query.filter_by(policyId=policyId).filter_by(day=day).all()
            list = []
            for item in entries:
                list.append(item.serialize)
            policyList[day] = list
        return json.dumps(policyList)


# Validate the data
@app.route('/validator', methods=['POST'])
def validator():
    if request.method == 'POST':
        payload = {}
        data = request.json
        print(data)
        day = data['day']
        endTime = datetime.datetime.strptime(data['endTime'], '%H:%M')
        startTime = datetime.datetime.strptime(data['startTime'], '%H:%M')
        entries = Policy.query.filter_by(day=day).all()
        list = []
        for item in entries:
            list.append(item.serialize)
        pp.pprint(list)
        for item in list:
            if item['id'] == data['policyId']:
                continue
            cEndTime = datetime.datetime.strptime(item['end'], '%H:%M')
            cStartTime = datetime.datetime.strptime(item['start'], '%H:%M')
            DateRangesOverlap = max(startTime, cStartTime) < min(endTime, cEndTime)
            if DateRangesOverlap:
                print("conflict")
                payload['value'] = False
                payload['name'] = item['name']
                return json.dumps(payload)
            else:
                continue
        print("good")
        payload['value'] = True
        payload['name'] = 'good'
        return json.dumps(payload)
