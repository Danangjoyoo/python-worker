from setuptools import setup, find_packages
import codecs
import os

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = '1.10.2'
DESCRIPTION = 'Simplify and master control (run and stop) the python threads (workers)'

# Setting up
setup(
    name="python-worker",
    version=VERSION,
    author="danangjoyoo (Agus Danangjoyo)",
    author_email="<agus.danangjoyo.blog@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=["keyboard"],
    keywords=['python', 'threading', 'worker', 'async worker', 'async thread', 'abort thread', 'thread stopper', "thread manager", 'simple thread', "thread monitor"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    url="https://github.com/Danangjoyoo/python-worker"
)