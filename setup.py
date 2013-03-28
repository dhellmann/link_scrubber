#!/usr/bin/env python

PROJECT = 'bmcleaner'
VERSION = '0.1'

# Bootstrap installation of Distribute
import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='pinboard.in or delicious.com bookmark cleaner',
    long_description=long_description,

    author='Doug Hellmann',
    author_email='doug.hellmann@gmail.com',

    classifiers=['Development Status :: 5 - Production/Stable',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    provides=['bmcleaner'],
    install_requires=['pydelicious'],

    packages=find_packages(),
    include_package_data=True,

    entry_points={
        #'console_scripts': [ 'venvw_hook = virtualenvwrapper.hook_loader:main' ],
        },

    zip_safe=False,
    )
