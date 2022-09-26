"""
VASP run parsing script

implemented using atomate and jobflow

Objectives:
1. prepare to backfill database with legacy experiments
   - collect relaxations + subsequent calculations
   - fill atomate schema
     - difference between workflow schema and output schema?
   - upload to database
2. write atomic steps to files and populate ml directory on depot
"""

from atomate2.vasp.drones import VaspDrone
import os
import monty
from pathlib import Path

import pprint
import json

import subprocess
from itertools import chain

drone = VaspDrone()

vaspaths = chain.from_iterable(
    [drone.get_valid_paths(x) for x in os.walk('.') if drone.get_valid_paths(x)]
)

docs = []
for vaspath in vaspaths:
    print(vaspath)
    with monty.os.cd(vaspath):
        docs.append(drone.assimilate())

for doc in docs:
    for calc in doc.calcs_reversed:
        for step in calc.dict()['output']['ionic_steps']:
            print('count')
            pprint.pprint(step['structure'])
