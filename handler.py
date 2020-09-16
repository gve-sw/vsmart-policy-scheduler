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

import pprint

from app import db
from app.models import Policy

pp = pprint.PrettyPrinter(indent=4)


def commit(data, policyId, policyName):
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    # modes = ['start_', 'end_']
    policies = []
    pp.pprint(data)
    entries = Policy.query.filter_by(policyId=policyId).all()
    pp.pprint(entries)
    for entry in entries:
        db.session.delete(entry)
        pp.pprint(f"Deleted {entry}")
        db.session.commit()
    for day in days:
        count = 0
        while(1):
            if data.get(f"start_{day}{count}") and data.get(f"end_{day}{count}"):
                try:
                    # print(type(data.get(f"start_{day}{count}")))
                    # print(data.get(f"start_{day}{count}"))
                    new = Policy(day=day, policyId=policyId, policyName=policyName, start=data[f"start_{day}{count}"],
                                 end=data[f"end_{day}{count}"])
                    # policies.append(new)
                    pp.pprint(f"Added {new}")
                    db.session.add(new)
                    db.session.commit()
                    count = count + 1
                except:
                    count = 0
                    break
                # break
            else:
                count = 0
                break

    return True
