# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

"""
    Name:       MyLog
    Author:     Andy Liu
    Email :     andy.liu.ud@hotmail.com
    Created:    3/24/2015
    Copyright:  Copyright ©Intel Corporation. All rights reserved.
    Licence:    This program is free software: you can redistribute it 
    and/or modify it under the terms of the GNU General Public License 
    as published by the Free Software Foundation, either version 3 of 
    the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler


def init_logger(_debug=True):
    _log_path_file = os.path.basename(sys.argv[0]) + '.log'
    _log_mode = 'a'
    _log_max_size = 1 * 1024 * 1024  # 1M
    _log_max_files = 1  # 1 File
    _log_debug_format = "%(asctime)s %(levelname)-10s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s"
    _log_info_format = "%(asctime)s %(levelname)-10s%(message)s"

    _debug_formatter = logging.Formatter(_log_debug_format)
    _info_formatter = logging.Formatter(_log_info_format)

    _rfh = RotatingFileHandler(_log_path_file, _log_mode, _log_max_size, _log_max_files)
    _rfh.setLevel(logging.DEBUG)
    _rfh.setFormatter(_debug_formatter)

    _ch = logging.StreamHandler()
    if _debug:
        _ch.setLevel(logging.DEBUG)
        _ch.setFormatter(_debug_formatter)
    else:
        _ch.setLevel(logging.INFO)
        _ch.setFormatter(_info_formatter)

    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)
    _logger.addHandler(_rfh)
    _logger.addHandler(_ch)
    return _logger
