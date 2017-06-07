# coding=utf8

from __future__ import unicode_literals

__all__ = ['DefineException', 'BuildException', 'ParseException']


class DefineException(Exception):
    pass


class ParseException(Exception):
    pass


class BuildException(Exception):
    pass
