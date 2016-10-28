#!/usr/bin/env python
import os
from setuptools import setup, find_packages
__version__ = "0.3.4"
# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name = 'pynicom',
       version = __version__,
       description = 'A Minicom like shell in Python',
       long_description = read('README.rst'),
       url='https://github.com/clobrano/pynicom.git',
       author = 'Carlo Lobrano',
       author_email = 'c.lobrano@gmail.com',
       license = 'MIT',
       py_modules = ['pynicom'],
       install_requires = ['docopt', 'pyserial', 'raffaello'],
       packages = find_packages(),
       package_data={
             '': ['README.rst'],
         },
       include_package_data = True,
       entry_points = {'console_scripts' : 'pynicom = pynicom:main'},
       keywords = ['serial', 'minicom'],
       classifiers = [
            "Development Status :: 4 - Beta",
       ],
       )


