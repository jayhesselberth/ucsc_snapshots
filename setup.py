#!/usr/bin/env python
# encoding: utf-8
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(name='ucsctools',
      version='0.1.3',
      description='useful tools for the UCSC genome browser',
      author='Jay Hesselberth',
      author_email='jay.hesselberth@gmail.com',
      license='MIT',
      url='https://github.com/jayhesselberth/ucsctools',
      install_requires=['ucscsession', 'pybedtools', 'path'],
      scripts=['ucsc_snapshots'],
      long_description=open('README.md').read(),
      classifiers=['License :: OSI Approved :: MIT License'],
)
