# coding=utf8

from __future__ import unicode_literals

from .constructors import CSequence


class CIPv4(CSequence):
    def __init__(self, **kwargs):
        super(CIPv4, self).__init__(format='>4B', **kwargs)

    def pre_build(self, value):
        return list(map(int, value.split('.')))

    def post_parse(self, value):
        return '{0}.{1}.{2}.{3}'.format(*value)


class CIPv4Port(CSequence):
    def __init__(self, **kwargs):
        super(CIPv4Port, self).__init__(format='>4BH', **kwargs)

    def pre_build(self, value):
        ip, port = value.split(':')
        return list(map(int, ip.split('.'))) + [int(port)]

    def post_parse(self, value):
        return '{0}.{1}.{2}.{3}:{4}'.format(*value)
