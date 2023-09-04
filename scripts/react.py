from rxn_ca.computing.schemas.ca_result_schema import RxnCAResultDoc
from rxn_ca.core.recipe import ReactionRecipe

from jobflow.managers.local import run_locally
from rxn_ca.computing.flows.parallel_rxn_flow import ParallelRxnMaker

import argparse
import os
import time

parser = argparse.ArgumentParser(
                    prog="Reaction Automaton",
                    description="Runs the rxn-ca automaton",
)

parser.add_argument('recipe_filename')
parser.add_argument('-d', '--input-dir')
parser.add_argument('-o', '--output-file')

args = parser.parse_args()

output_file = args.output_file
recipe_filename = args.recipe_filename

print(f"Reading recipe from {recipe_filename}...")

if output_file is None:
    output_dir = os.path.dirname(recipe_filename)
    output_fname = time.strftime("%Y-%m-%d-%H%M%S") + '.json'
    output_file = os.path.join(output_dir, output_fname)

print(f"Choosing {output_file} as output location")

recipe = ReactionRecipe.from_file(recipe_filename)

maker = ParallelRxnMaker()
flow = maker.make(
    recipe,
    output_fname=output_file
)

output: RxnCAResultDoc = run_locally(flow)