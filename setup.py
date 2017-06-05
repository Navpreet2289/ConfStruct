# coding=utf8

from __future__ import unicode_literals

from setuptools import setup

lib_classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
]

setup(name="ConfStruct",
      version='0.7.0',
      author="kinegratii",
      author_email="kinegratii@gmail.com",
      url="https://github.com/kinegratii/ConfStruct",
      keywords="struct binary pack unpack",
      py_modules=["conf_struct"],
      install_requires=['six'],
      description='A parser and builder between python dictionary and "length-body" binary data.',
      license="MIT",
      classifiers=lib_classifiers
      )
