"""Define the project's workflow logic and operation functions.

Execute this script directly from the command line, to view your project's
status, execute operations and submit them to a cluster. See also:

    $ python src/project.py --help
"""
import signac
from flow import FlowProject, directives
from flow.environment import DefaultSlurmEnvironment
from flow.environments.xsede import Bridges2Environment
import os

class MyProject(FlowProject):
    pass

class Borah(DefaultSlurmEnvironment):
    hostname_pattern = "borah"
    template = "borah.sh"

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(
            "--partition", default="gpu", help="Specify the partition to submit to."
        )

class R2(DefaultSlurmEnvironment):
    hostname_pattern = "r2"
    template = "r2.sh"

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(
            "--partition", default="gpuq", help="Specify the partition to submit to."
        )

class Fry(DefaultSlurmEnvironment):
    hostname_pattern = "fry"
    template = "fry.sh"

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(
            "--partition", default="batch", help="Specify the partition to submit to."
        )

# Definition of project-related labels (classification)
@MyProject.label
def completed(job):
    return job.doc.get("done")


@directives(executable="python -u")
@directives(ngpu=1)
@MyProject.operation
@MyProject.post(completed)
def optimize(job):
    from msibi import MSIBI, State, Pair, Bond, Angle, mie, morse
    import logging

    with job:
        job.doc["done"] = False
        logging.info("Setting up MSIBI optimizer...")
        opt = MSIBI(
            integrator=job.sp.integrator,
            integrator_kwargs=job.doc.integrator_kwargs,
            dt=job.sp.dt,
            gsd_period=job.sp.gsd_period,
            n_iterations=job.sp.iterations,
            n_steps=job.sp.n_steps,
        )

        logging.info("Creating State objects...")
        for state in job.sp.states:
            traj_file_path = os.path.abspath(
                    os.path.join(
                        job.ws, "..", "..", state["target_trajectory"]
                    )
            )
            opt.add_state(
                    State(
                        name=state["name"],
                        kT=state["kT"],
                        traj_file=traj_file_path,
                        alpha=state["alpha"],
					    _dir=job.ws
                    )
            )

        logging.info("Creating Pair objects...")
        for pair in job.sp.pairs:
            if "potential" in pair.keys():
                potential=pair["potential"]
            else:
                if job.sp.initial_potential == "morse":
                    potential = morse(opt.pot_r, 1.0, 1.0)
                elif job.sp.initial_potential == "mie":
                    potential = mie(job.sp.potential_cutoff, 1.0, 1.0)

            opt.add_pair(
                    Pair(
                        type1=pair["type1"],
                        type2=pair["type2"],
                        potential=potential,
                        head_correction_form = job.sp.head_correction
                    )
                )

        if job.sp.bonds is not None:
            logging.info("Creating Bond objects...")
            for bond in job.sp.bonds:
                new_bond = Bond(type1=bond["type1"], type2=bond["type2"])
                if bond["form"] == "harmonic":
                    new_bond.set_harmonic(k=bond["k"], r0=bond["r0"])

                opt.add_bond(new_bond)

        if job.sp.angles is not None:
            logging.info("Creating Angle objects...")
            for angle in job.sp.angles:
                new_angle = Angle(
                        type1=angle["type1"],
                        type2=angle["type2"],
                        type3=angle["type3"],
                )
                if angle["form"] == "harmonic":
                    new_angle.set_harmonic(k=angle["k"], theta0=angle["theta0"])

        opt.optimize_pairs(
                max_frames=job.sp.num_rdf_frames,
                rdf_cutoff=job.sp.potential_cutoff,
                r_min=job.sp.r_min,
                r_switch=job.sp.r_switch,
                n_rdf_points=job.sp.num_rdf_points,
                smooth_rdfs=job.sp.smooth_rdf,
                rdf_exclude_bonded=job.sp.rdf_exclude_bonded,

        )

        job.doc["dr"] = opt.dr
        job.doc["pot_r"] = opt.pot_r
        job.doc["done"] = True


if __name__ == "__main__":
    MyProject().main()
