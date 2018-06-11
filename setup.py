from os.path import join, dirname

from setuptools import setup, find_packages


def read(filename):
    with open(join(dirname(__file__), filename)) as fileobj:
        return fileobj.read()


def get_version(package):
    return [
        line for line in read('{}/__init__.py'.format(PACKAGE)).splitlines()
        if line.startswith('__version__ = ')][0].split("'")[1]


PACKAGE = 'jupyter_runner'
VERSION = get_version(PACKAGE)


setup(
    name=PACKAGE,
    version=VERSION,
    description='Jupyter notebook runner.',
    long_description=read('README.rst'),
    author='Omar Masmoudi',
    packages=find_packages(),
    entry_points="""
        [console_scripts]
        jupyter-runner = jupyter_runner.run:main
    """,
    install_requires=['docopt', 'jupyter'],
    classifiers=[
        'Programming Language :: Python :: 3.5',
    ],
)
