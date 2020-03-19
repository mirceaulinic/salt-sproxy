# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('salt_sproxy').version
except pkg_resources.DistributionNotFound:
    __version__ = 'Not installed'

__version_info__ = tuple(__version__.split('.'))

all = ['__version__', '__version_info__']
