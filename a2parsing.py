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
from pymatgen.core import Structure

import os
import monty
from pathlib import Path

import pprint
import json

import subprocess
from itertools import chain

from typing import Any, Union
from collections.abc import Iterable

task_document_kwargs = {
    'additional_fields':{# add fields to the document for submission to database
        
    },
    # #'vasp_calculation_kwargs':{# control which parts of a calculation are assimilated
    # 'parse_dos': False,
    # 'parse_bandstructure': False,
    # 'average_locpot': True,
    # 'vasprun_kwargs': {# control minutia of which files are parsed and how
    #     'parse_potcar_file':False,
    #     'parse_dos':True,
    #     'parse_eigen':False,
    #     'parse_projected_eigen':False,
    # }
}
drone = VaspDrone(**task_document_kwargs)

data_dir = '/depot/amannodi/data/perovskite_structures_training_set'

def get_vasp_paths(parent:Union[str,Path]) -> Iterable[str]:
    vaspaths = chain.from_iterable(
        [drone.get_valid_paths(x) for x in os.walk(parent) if drone.get_valid_paths(x)]
    )
    return vaspaths

def filter_vasp_path(vaspaths:Iterable[str])->Iterable[str]:
    """ narrow vaspaths to subdirectories matching a pattern """
    return vaspaths

def assimilate_paths(vaspaths:Iterable[Union[str,Path]]) -> list:
    docs = []
    for vaspath in vaspaths:
        #print(vaspath)
        with monty.os.cd(vaspath):
            docs.append(drone.assimilate())
    return docs

def make_record_name(doc, calc, step)->str:
    """
    make a string to serve as structure file and id_prop entry ID

    unique id made of:
    chemistry + LoT + intermediacy
    """
    formula=doc.dict()['formula_pretty']
    LoT=calc.dict()['run_type']
    istep=
    record_name = f"{formula}_{LoT}_{}"
    return record_name

def structure_to_training_set_entry(structure:Structure,
                                    data_dir:Union[str,Path],
                                    record_name:str,
                                    props_list:list) -> None:
    filename=os.path.join(data_dir, record_name)
    id_prop_master=os.path.join(data_dir, 'id_prop_master.csv')
    props=','.join(props_list)
    struct.to(fmt='POSCAR', filename=filename)
    with open(id_prop_master, 'a') as f:
        f.write(f"{record_name},{props}")

def main():
    """silly temporary main function while waiting for Geddes resource"""
    docs = assimilate_paths(get_vasp_paths('.'))
    for doc in docs:
        # print(doc.dict().keys())
        # ['nsites', 'elements', 'nelements', 'composition', 'composition_reduced', 'formula_pretty', 'formula_anonymous', 'chemsys', 'volume', 'density', 'density_atomic', 'symmetry', 'dir_name', 'last_updated', 'completed_at', 'input', 'output', 'structure', 'state', 'included_objects', 'vasp_objects', 'entry', 'analysis', 'run_stats', 'orig_inputs', 'task_label', 'tags', 'author', 'icsd_id', 'calcs_reversed', 'transformations', 'custodian', 'additional_json'])
        for calc in doc.calcs_reversed:
            # print(calc.dict().keys())
            # ['dir_name', 'vasp_version', 'has_vasp_completed', 'input', 'output', 'completed_at', 'task_name', 'output_file_paths', 'bader', 'run_type', 'task_type', 'calc_type']
            # print(calc.dict()['output'].keys())
            # dict_keys(['energy', 'energy_per_atom', 'structure', 'efermi', 'is_metal', 'bandgap', 'cbm', 'vbm', 'is_gap_direct', 'direct_gap', 'transition', 'mag_density', 'epsilon_static', 'epsilon_static_wolfe', 'epsilon_ionic', 'frequency_dependent_dielectric', 'ionic_steps', 'locpot', 'outcar', 'force_constants', 'normalmode_frequencies', 'normalmode_eigenvals', 'normalmode_eigenvecs', 'elph_displaced_structures', 'dos_properties', 'run_stats'])
            for step in calc.dict()['output']['ionic_steps']:
                #print(step.keys())
                #dict_keys(['e_fr_energy', 'e_wo_entrp', 'e_0_energy', 'forces', 'stress', 'electronic_steps', 'structure'])
                record_name = make_record_name(doc, calc, step)
                props_list = [step['e_0_energy']]
                struct = step['structure']
                structure_to_training_set_entry(struct,
                                                data_dir,
                                                record_name,
                                                props_list)


if __name__ == "__main__":
    main()
