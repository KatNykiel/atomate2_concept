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
from jobflow import JobStore, SETTINGS

import os
import monty
from pathlib import Path

import tqdm
from itertools import chain

from typing import Any, Union
from collections.abc import Iterable

task_document_kwargs = {
    'additional_fields':{# add fields for submission to database
        
    },
    #'vasp_calculation_kwargs':{
    # control which parts of a calculation are assimilated
    'parse_dos': True,
    'parse_bandstructure': True,
    'average_locpot': True,
    # control minutia of which files are parsed and how
    'vasprun_kwargs': {
        'parse_potcar_file':False,
        'parse_dos':True,
        'parse_eigen':True,
        'parse_projected_eigen':False,
    }
}

drone = VaspDrone(**task_document_kwargs)

store = SETTINGS.JOB_STORE
#look into defining save/load mapping to direct document items to
#additional stores

experiment_dir = '.' #invoke script from experiment directory
data_dir = '/depot/amannodi/data/perovskite_structures_training_set'

def get_vasp_paths(parent:Union[str,Path]) -> Iterable[str]:
    """
    Use drone to find viable VASP experiment directories
    
    valid paths include those that lead to:
    - unique vasprun.xml (nesting directories ok)
    - relax<###> directory (multi-optimization runs)
    - vasprun.relax<###> (multi-opt)
    """
    vaspaths = chain.from_iterable(
        [drone.get_valid_paths(x) for x in os.walk(parent) if
         drone.get_valid_paths(x)]
    )
    return vaspaths

def filter_vaspaths(vaspaths:Iterable[str],
                    filterlist)->Iterable[str]:
    """
    utility to manually narrow vaspaths to those which don't contain
    strings member to filterlist
    """
    vaspaths = [s for s in vaspaths if not
                any(filterentry in s for filterentry in filterlist)]
    return vaspaths

def assimilate_paths(vaspaths:Iterable[Union[str,Path]],
                     filterlist=[]) -> list:
    """
    Use drone to create list of taskdocuments corresponding to list of
    experiment directories.
    """
    docs = []
    for vaspath in tqdm(filter_vaspaths(vaspaths, filterlist),
                        desc=f"Processing {vaspath}"):
        try:
            with monty.os.cd(vaspath):
                docs.append(drone.assimilate())
        except Exception as e:
            print(e)
    return docs

def update_store(store:JobStore, docs:list) -> None:
    with store as s:
        s.update(docs, key="output")

### Additional functions to create Graph Network Training Directories

def make_record_name(doc, calc, step)->str:
    """
    make a string to serve as structure file and id_prop entry ID

    unique id made of:
    chemistry + LoT + intermediacy
    """
    formula=doc.dict()['formula_pretty']
    LoT=calc.dict()['run_type']
    istep=step
    record_name = f"{formula}_{LoT}_{istep}"
    return record_name

def structure_to_training_set_entry(struct:Structure,
                                    data_dir:Union[str,Path],
                                    record_name:str,
                                    props_list:list) -> None:
    filename=os.path.join(data_dir, record_name)
    id_prop_master=os.path.join(data_dir, 'id_prop_master.csv')
    props=','.join(map(str,props_list))
    struct.to(fmt='POSCAR', filename=filename)
    with open(id_prop_master, 'a') as f:
        f.write(f"{record_name},{props}\n")

def main():
    """silly temporary main function while waiting for Geddes resource"""
    id_prop_master=os.path.join(data_dir, 'id_prop_master.csv')
    with open(id_prop_master, 'a') as f:
        f.write(f"id,decoE,bg\n")
    docs = assimilate_paths(get_vasp_paths(experiment_dir),
                            filterlist=['LEPSILON','LOPTICS','Phonon_band_structure'])
    # LEPSILON doesn't have bands?  # get_element_spd_dos(el)[band] keyerror
    # LOPTICS doesn't have VASPrun pdos attribute
    # PH disp doesn't have electronic bands # get_element_spd_dos(el)[band] keyerror
    for doc in docs:
        # doc.dict().keys()
        # ['nsites', 'elements', 'nelements', 'composition', 'composition_reduced', 'formula_pretty','formula_anonymous'
        # , 'chemsys', 'volume', 'density', 'density_atomic', 'symmetry', 'dir_name', 'last_updated',
        # 'completed_at', 'input', 'output', 'structure', 'state', 'included_objects', 'vasp_objects', 'entry',
        # 'analysis', 'run_stats', 'orig_inputs', 'task_label', 'tags', 'author', 'icsd_id', 'calcs_reversed',
        # 'transformations', 'custodian', 'additional_json'])
        for calc in doc.calcs_reversed:
            # calc.dict().keys()
            # ['dir_name', 'vasp_version', 'has_vasp_completed', 'input', 'output', 'completed_at', 'task_name',
            # 'output_file_paths', 'bader', 'run_type', 'task_type', 'calc_type']
            # calc.dict()['output'].keys()
            # ['energy', 'energy_per_atom', 'structure', 'efermi', 'is_metal', 'bandgap', 'cbm', 'vbm', 'is_gap_direct',
            # 'direct_gap', 'transition', 'mag_density', 'epsilon_static', 'epsilon_static_wolfe', 'epsilon_ionic',
            # 'frequency_dependent_dielectric', 'ionic_steps', 'locpot', 'outcar', 'force_constants',
            # 'normalmode_frequencies', 'normalmode_eigenvals', 'normalmode_eigenvecs', 'elph_displaced_structures',
            # 'dos_properties', 'run_stats']
            # calc.dict()['input'].keys()
            # ['incar', 'kpoints', 'nkpoints', 'potcar', 'potcar_spec', 'potcar_type', 'parameters', 'lattice_rec',
            # 'structure', 'is_hubbard', 'hubbards']
            struct = calc.dict()['input']['structure'] #POSCAR
            props_list = [None, None] #no computed properties yet
            record_name = make_record_name(doc, calc, 0)
            structure_to_training_set_entry(struct,
                                            data_dir,
                                            record_name,
                                            props_list)
            for count, step in enumerate(calc.dict()['output']['ionic_steps']):
                # print(step.keys())
                # ['e_fr_energy', 'e_wo_entrp', 'e_0_energy', 'forces', 'stress', 'electronic_steps', 'structure']
                struct = step['structure'] #XDATCAR iteration
                # compute stability and band gap at each interval
                # decoE = step['e_fr_energy'] - energy of stuff
                decoE = -1
                HOMO = 1 # look for ionic step eigenvalues in outcar? 
                LUMO = 0
                bg = HOMO-LUMO
                props_list = [decoE, bg]
                record_name = make_record_name(doc, calc, count+1)
                structure_to_training_set_entry(struct,
                                                data_dir,
                                                record_name,
                                                props_list)

            struct = calc.dict()['output']['structure']
            decoE = calc.dict()['output']['energy'] # minus other stuff
            props_list = [decoE,
                          calc.dict()['output']['bandgap']]
            record_name = make_record_name(doc, calc, count+2)
            structure_to_training_set_entry(struct,
                                            data_dir,
                                            record_name,
                                            props_list)

if __name__ == "__main__":
    main()
    # docs = assimilate_paths(get_vasp_paths(experiment_dir),
    #                         filterlist=['LEPSILON','LOPTICS','Phonon_band_structure'])
    # update_store(store, docs)
