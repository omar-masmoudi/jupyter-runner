Welcome to Jupyter-Runner's documentation
=========================================

Jupyter runners allows to run **multiple notebooks** over **multiple sets of parameters**.

Notebook execution can happen in parallel with a fixed number of workers.

Usage
=====

::

    jupyter-run [options] <notebook>...

        --parameter-file=<PARAMETER_FILE>**    Optional parameters files containing one parameter instance by line, setting the environment.
        Example with 2 sets of 3 parameters:
            VAR1=VAL1 VAR2=VAL2 VAR3=VAL3
            VAR1=VAL5 VAR2=VAL18 VAR3=VAL42
        --workers=<workers>                    Maximum number of parallel execution [Default: 1]
        --output-directory=<OUTPUT_DIRECTORY>  Output directory [Default: .]
        --overwrite                            Overwrite output files if they already exist.
        --format=<FORMAT>                      Output format: html, notebook... [Default: html]
        --debug                                Enable debug logs
        --help                                 Display this help
        --version                              Display version



Tutorial
========

Run a simple notebook
---------------------

.. code-block:: console

    jupyter-run notebook.ipynb

By default, the process creates output file `notebook.html` in current directory.

Run multiple notebooks
----------------------

.. code-block:: console

    jupyter-run notebookA.ipynb notebookB.ipynb

By default, the process creates output files `notebookA.html` and `notebookB.html` in current directory.


Run notebook with parameters
----------------------------
Use environment variables on command-line.

.. code-block:: console

    ENV_VAR=xxx jupyter-run notebook.ipynb

In python notebook, variables can be retrieved using ``os.environ``:

.. code-block:: python

    import os
    env_var = os.environ.get('ENV_VAR', 'a_default_value')
    # usage of env_var in your code

By default, the process creates output file `notebook.html` in current directory.
The notebook variables passed by the user can impact the rendering of the output.

Run notebook with multiple sets of parameters
---------------------------------------------
Create a file with multiple set of parameters, one set of parameters per line.

Example file containing 2 sets of 3 parameters:
::

    VAR1=VAL1 VAR2=VAL2 VAR3=VAL3
    VAR1=VAL5 VAR2=VAL18 VAR3='VAL42 with space'

Then run jupyter-run specifying the path to ``my_parameter_file`` just created:

.. code-block:: console

    jupyter-run --parameter-file=my_parameter_file notebook.ipynb

By default, the process creates output files `notebook_1.html` and `notebook_2.html` in current directory.

Run multiple notebooks with multiple sets of parameters
-------------------------------------------------------
jupyter-run can combine multiple set of parameters on multiple notebooks.
When there are ``N`` sets of parameters running on ``M`` notebooks, there will be ``NxM`` distinct output files.

.. code-block:: console

    jupyter-run --parameter-file=my_parameter_file notebookA.ipynb notebookB.ipynb

By default, the process creates output files `notebookA_1.html`, `notebookA_2.html`, `notebookB_1.html`, `notebookB_2.html` in current directory.

Change output directory
-----------------------

.. code-block:: console

    jupyter-run --output-directory results notebook.ipynb

The process create output file ``results/notebook.html`.
``results`` directory is created if it does not pre-exist.

Overwrite existing outputs
--------------------------
By default, jupyter-run skip the run when output file(s) already exists.
To overwrite the files, use the ``--overwrite`` option:

.. code-block:: console

    jupyter-run --overwrite notebook.ipynb

Use multiple workers
--------------------
By default, only 1 notebook will be executed at the same time.
Use ``--workers`` option to specify the number of notebooks to run in parallel.

.. code-block:: console

    jupyter-run --workers 3 --parameter-file=my_parameter_file notebookA.ipynb notebookB.ipynb

The above command will start to run 3 notebook output over the 4 requested. When the first execution finishes, the 4th notebook is launched and so on.

Change output type
------------------
List of possible output types are available here:
https://nbconvert.readthedocs.io/en/latest/usage.html#default-output-format-html

.. code-block:: console

    jupyter-run --format notebook --output-directory results notebook.ipynb
