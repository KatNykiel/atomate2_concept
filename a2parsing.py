from atomate2.vasp.drones import VaspDrone
import os
import monty
from pathlib import Path
import subprocess
from itertools import chain

# drone = VaspDrone()
# with monty.os.cd('./VASP_runs/Si_test'):
#     doc = drone.assimilate()
# drone.get_valid_paths([(r,d,f) for r,d,f in os.walk('.')][2])
#     print(doc)

drone = VaspDrone()

vaspaths = list(chain.from_iterable(
  [drone.get_valid_paths(x) for x in os.walk('.') if drone.get_valid_paths(x)]
))

print(vaspaths)

docs = []
for vaspath in vaspaths:
    print(vaspath)
    with monty.os.cd(vaspath):
        docs.append(drone.assimilate())

