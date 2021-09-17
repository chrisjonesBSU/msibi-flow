#!/usr/bin/env python
"""Initialize the project's data space.

Iterates over all defined state points and initializes
the associated job workspace directories.
The result of running this file is the creation of a signac workspace:
    - signac.rc file containing the project name
    - signac_statepoints.json summary for the entire workspace
    - workspace/ directory that contains a sub-directory of every individual statepoint
    - signac_statepoints.json within each individual statepoint sub-directory.
"""

import signac
import logging
from collections import OrderedDict
from itertools import product

def get_parameters():
    '''Use the listed parameters below to set up
    your MSIBI instructions.
    '''
    parameters = OrderedDict()
    parameters["potential_cutoff"] = [5.0] # Used for pot and rdf cut
    parameters["num_rdf_points"] = [101] # Num of RDF bins
    parameters["num_rdf_frames"] = [5] # Num of frames to sample in RDF
    parameters["smooth_rdf"] = [True]
    parameters["rdf_exclude_bonded"] = [False] # Exclude pairs on same molecule
    parameters["r_switch"] = [None]
    parameters["integrator"] = [] # Str of hoomd integrator
    parameters["integrator_kwargs"] = [] # Dictionary of integrator kwargs
    parameters["dt"] = [0.001]
    parameters["gsd_period"] = [1000] # Num of steps between gsd snapshots
    parameters["initial_potential"] = ["mie"] # mie, morse
    parameters["iterations"] = [20] 
    parameters["n_steps"] = [1e6] # Num simulation steps during each iteration

    # Information used to create MSIBI objects:
        # states: name, kT, target trajectory, alpha
        # pair: type1, type1, potential (optional)
        # bonds: type1, type2, k, r0
        # angles: type1, type2, type3, k, theta0

    # If your system does not contain bonds or angles, change both
    # parameters to None

    parameters["states"] = [
                [{}, {}, {}],
            ]
    parameters["pairs"] = [
                [{}, {}, {}],
            ]
    parameters["bonds"] = [
                [{}, {}, {}],
            ]
    parameters["angles"] = [
                [{}, {}, {}],
            ]
    return list(parameters.keys()), list(product(*parameters.values()))

def main():
    project = signac.init_project("project")
    param_names, param_combinations = get_parameters()
    # Create the generate jobs
    for params in param_combinations:
        parent_statepoint = dict(zip(param_names, params))
        parent_job = project.open_job(parent_statepoint)
        parent_job.init()

    project.write_statepoints()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
