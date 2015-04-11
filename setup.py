#!/usr/bin/env python
# encoding: utf-8
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

entry_points = """
[console_scripts]
ucsc_snapshots = ucsc_snapshots.ucsc_snapshots:main
"""
setup(name='ucsc_snapshots',
      version='0.1.8',
      description='fetch images from the UCSC genome browser using BED regions',
      author='Jay Hesselberth',
      author_email='jay.hesselberth@gmail.com',
      license='CC0',
      url='https://github.com/jayhesselberth/ucsc_snapshots',
      install_requires=['pybedtools', 'path.py', 'ucscsession',
                        'requests','beautifulsoup4','mechanize'],
      entry_points=entry_points,
      long_description=open('README').read(),
      classifiers=['License :: OSI Approved :: MIT License'],
)
