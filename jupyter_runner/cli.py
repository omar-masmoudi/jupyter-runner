"""
Usage: jupyter-runner [options] <notebook>...

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
import os
from os.path import exists, isfile
import multiprocessing
from inspect import signature

from docopt import docopt

from . import __version__
from .execute import (
    get_tasks,
    execute_notebook,
)
from .constant import MAP_OUTPUT_EXTENSION


LOG_FORMAT = '[%(asctime)s %(levelname)s] %(message)s'
LOGGER = logging.getLogger(__file__)


def log_input_options(args):
    LOGGER.debug('Running notebook(s) with following arguments:')
    for key in sorted(args.keys()):
        if key in ['--help', '--version']:
            continue
        LOGGER.debug('%s: %s', key, args[key])


def parse_args(args):
    """Return sanitize dict of arguments."""
    workers = int(args['--workers'])
    assert workers >= 1

    parameter_file = args['--parameter-file']
    assert parameter_file is None or isfile(parameter_file)

    notebooks = args['<notebook>']
    for notebook in notebooks:
        assert isfile(notebook)
        with open(notebook, mode='r'):
            # Open notebook file to ensure it exists
            pass

    output_dir = args['--output-directory']
    if not exists(output_dir):
        os.makedirs(output_dir)
    assert os.access(output_dir, os.W_OK), \
        'No write access to output directory: %s' % output_dir

    overwrite = args['--overwrite']

    output_format = args['--format']
    assert output_format in MAP_OUTPUT_EXTENSION.keys()

    timeout = args['--timeout']
    assert float(timeout), '--timeout should be a float.'

    allow_errors = args['--allow-errors']

    return dict(
        parameter_file=parameter_file,
        notebooks=notebooks,
        output_dir=output_dir,
        debug=args['--debug'],
        overwrite=overwrite,
        output_format=output_format,
        timeout=timeout,
        allow_errors=allow_errors,
    )


def main():
    """Main function of jupyter-run."""
    args = docopt(__doc__, version=__version__)

    # Determine log level
    debug = args['--debug']
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    # In debug mode, log input options
    log_input_options(args)

    # Read and return sanitized arguments
    args = parse_args(args)

    # Retrieve individual task to run (product of parameters and notebooks)
    kw_tasks = get_tasks(
        parameter_file=args['parameter_file'],
        notebooks=args['notebooks'],
        output_dir=args['output_dir'],
        debug=args['debug'],
        overwrite=args['overwrite'],
        output_format=args['output_format'],
        timeout=args['timeout'],
        allow_errors=args['allow_errors'],
    )

    # Flatten list of kwargs to list of args
    tasks = [
        [kw_task[arg] for arg in signature(execute_notebook).parameters]
        for kw_task in kw_tasks
    ]

    ret_codes = []
    if args['workers'] > 1:
        with multiprocessing.Pool(args['workers']) as pool:
            ret_codes = pool.starmap(execute_notebook, tasks, chunksize=1)
    else:
        # Execute without multiprocessing to ease debugging
        for task in tasks:
            ret_codes.append(execute_notebook(**task))

    return max(ret_codes) if ret_codes else 0
