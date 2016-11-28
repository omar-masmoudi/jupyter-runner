"""
Usage: run_notebook.py [options] <notebook>...

    --parameter-file=<PARAMETER_FILE>  Optional parameters files containing
    one parameter instance by line, setting the environment.
    Example with 2 sets of 3 parameters:
        VAR1=VAL1 VAR2=VAL2 VAR3=VAL3
        VAR1=VAL5 VAR2=VAL18 VAR3=VAL42
    --workers=<workers>  Maximum number of parallel execution  [Default: 1]
    --output-directory=<OUTPUT_DIRECTORY>  Output directory  [Default: .]
    --overwrite  Overwrite output files if they already exist.
    --format=<FORMAT>  Output format: html, notebook...  [Default: html]
    --timeout=<TIMEOUT>  Cell execution timeout in seconds.  [Default: -1]
    --allow-errors  Allow errors during notebook execution.
    --debug  Enable debug logs
    --help  Display this help
    --version  Display version
"""
import logging
import shlex
import os
from os.path import basename, splitext, exists, join, abspath, samefile
import subprocess
import multiprocessing

from docopt import docopt

import jupyter_runner

LOG_FORMAT = '[%(asctime)s %(levelname)s] %(message)s'
LOGGER = logging.getLogger(__file__)


def parse_parameters(text):
    """
    Return environment dictionary from text.

    VAR1=VAL1 VAR2=VAL2 VAR3=VAL3
    returns
    {'VAR1': 'VAL1 with spaces', 'VAR2': 'VAL2', 'VAR3': 'VAL3'}
    :param text: Environment text string in bash format.
    :return: parameters dictionary to pass to subprocess as environment
    """
    tokens = shlex.shlex(text, posix=True)
    is_key = True
    current_key = None
    environ = {}
    for token in tokens:
        if token == '=':
            is_key = not is_key
            continue
        if is_key:
            current_key = token
        else:
            environ[current_key] = token
            is_key = True
    return environ


def parse_parameter_file(filename):
    """
    Open filename and return the parameters as list of dictionaries.

    :param filename: Filename containing one set of parameters per line.
    :return: dict of parameters
    """
    if filename is None:
        # Return list of one parameter
        return [{}]
    with open(filename) as fh:
        lines = fh.readlines()
    parameters = []
    for line in lines:
        parameters.append(parse_parameters(line))
    return parameters


def execute_notebook(notebook_file, parameters, output_file, debug, overwrite,
                     format, timeout, allow_errors):
    """
    Execute notebook and export output result file.

    :param notebook_file: Notebook file to execute.
    :param parameters: Dictionary of environment variables.
    :param output_file: Output HTML file path.
    :param debug: Boolean enabling debug notebook execution.
    :param overwrite: Boolean overwriting
    :param format: String 'html' or 'ipynb'
    :param timeout: Timeout in seconds
    :param allow_errors: Boolean authorizing errors in notebook execution
    """
    in_place = False
    if exists(output_file):
        if not overwrite:
            LOGGER.info("Skip existing output file %s" % output_file)
            return 0
        elif samefile(notebook_file, output_file):
            LOGGER.debug("Executing notebook %s in place" % output_file)
            in_place = True
        else:
            LOGGER.info("Remove existing output file %s" % output_file)
            os.remove(output_file)

    cmd = ['jupyter', 'nbconvert', '--execute',
           '--ExecutePreprocessor.timeout=%s' % timeout,
           '--output', output_file,
           '--to', format]
    if debug:
        cmd.append('--debug')
    if in_place:
        cmd.append('--inplace')
    if allow_errors:
        cmd.append('--allow-errors')
    cmd.append(notebook_file)
    env = os.environ.update(parameters)

    LOGGER.info("Executing command: %s with parameters: %s" %
                (' '.join(cmd), str(parameters)))
    ret = subprocess.call(cmd, env=env)

    return ret


def get_tasks(parameter_file, notebooks, output_dir, debug, overwrite, format,
              timeout, allow_errors):
    """Return list of tasks to run based on parameters and notebooks.

    The number of tasks returned is:
        # of parameters x # of notebooks.
    """
    parameters = parse_parameter_file(parameter_file)

    tasks = []
    for param_id, params in enumerate(parameters):
        for notebook in notebooks:
            if parameter_file is None:
                file_suffix = ''
            elif 'JUPYTER_OUTPUT_SUFFIX' in params:
                file_suffix = '_%s' % params['JUPYTER_OUTPUT_SUFFIX']
            else:
                file_suffix = '_%d' % (param_id + 1)
            extension = '.%s' % format if format != 'notebook' else '.ipynb'
            output_name = '%s%s%s' % (splitext(basename(notebook))[0],
                                      file_suffix,
                                      extension)
            output_file = abspath(join(output_dir, output_name))
            tasks.append((notebook, params, output_file, debug, overwrite,
                          format, timeout, allow_errors))

    for task_id, task in enumerate(tasks):
        LOGGER.debug('Task %d: %s' % (task_id + 1, str(task)))

    return tasks


def main():
    """Main function of jupyter-run."""
    args = docopt(__doc__, version=jupyter_runner.__version__)

    debug = args['--debug']
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    LOGGER.debug('Running notebook(s) with following arguments:')
    for key in sorted(args.keys()):
        if key in ['--help', '--version']:
            continue
        LOGGER.debug('%s: %s' % (key, args[key]))

    workers = int(args['--workers'])
    parameter_file = args['--parameter-file']
    notebooks = args['<notebook>']
    output_dir = args['--output-directory']
    overwrite = args['--overwrite']
    format = args['--format']
    timeout = args['--timeout']
    allow_errors = args['--allow-errors']
    if not exists(output_dir):
        os.makedirs(output_dir)

    tasks = get_tasks(parameter_file, notebooks, output_dir, debug, overwrite,
                      format, timeout, allow_errors)
    ret_codes = []
    if workers > 1:
        with multiprocessing.Pool(workers) as pool:
            ret_codes = pool.starmap(execute_notebook, tasks, chunksize=1)
    else:
        # Execute without multiprocessing to ease debugging
        for task in tasks:
            ret_codes.append(execute_notebook(*task))

    return max(ret_codes) if ret_codes else 0
