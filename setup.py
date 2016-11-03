#!/usr/bin/env python
import os
from setuptools import setup, find_packages
__version__ = "0.3.5"
# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name = 'pynicom',
       author = 'Carlo Lobrano',
       author_email = 'c.lobrano@gmail.com',
       description = 'A Minicom like shell in Python',
       entry_points = {'console_scripts' : 'pynicom = pynicom:main'},
       include_package_data = True,
       install_requires = ['docopt', 'pyserial', 'raffaello'],
       keywords = ['serial', 'minicom'],
       license = 'MIT',
       long_description = read('README.rst'),
       package_dir={'': 'src'},
       packages = find_packages('src'),
       py_modules = ['pynicom'],
       url='https://github.com/clobrano/pynicom.git',
       version = __version__,
       classifiers = [
            "Development Status :: 4 - Beta",
       ]
       )


