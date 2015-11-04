#!/usr/bin/env python

from setuptools import setup, find_packages
#from pycom import __version__

setup (name = 'pycom',
        version = "0.1.0",
        description = 'A Minicom lik shell in Python',
        author = 'Carlo Lobrano',
        author_email = 'c.lobrano@gmail.com',
        license = 'MIT',
        py_modules = ['pycom'],
        install_requires = ['readline', 'docopt', 'raffaello'],
        packages = find_packages(),
        entry_points = {'console_scripts' : 'pycom = pycom:main'},
        include_package_data = True,
        use_2to3 = True,
        keywords = ['serial', 'minicom'],
        )


