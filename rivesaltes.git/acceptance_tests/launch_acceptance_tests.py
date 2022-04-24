import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError

# mandatory utf-8 because nbformat writes notebook with utf-8 content
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
basedir = os.path.dirname(os.path.abspath(__file__))

run_path = '{}/'.format(basedir)
output_dir = '{}/out'.format(basedir)
notebook_filename_out = '{}/out/TestOutput_{}.ipynb'
notebook_base_url = '{}/notebooks/{}.ipynb'


import os
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

paths = [
    'example_acceptance_test',
    'pvlib_acceptance_test',
    'pvmodeling_acceptance_test',
    'simulation_acceptance_test'
]

for notebook_name in paths :
    with open(notebook_base_url.format(basedir, notebook_name)) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=1000, kernel_name='datadriver')

        print('Run path=' + run_path)
        try:
            out = ep.preprocess(nb, {'metadata': {'path': run_path}})
        except CellExecutionError:
            out = None
            msg = 'Error executing the notebook "%s".\n\n' % notebook_name
            msg += 'See notebook "%s" for the traceback.' % notebook_filename_out
            print(msg)
            raise
        finally:
            with open(notebook_filename_out.format(basedir, notebook_name), mode='wt') as f:
                nbformat.write(nb, f)