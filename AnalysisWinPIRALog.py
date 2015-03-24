# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

"""
    Name:       AnalysisWinPIRALog
    Author:     Andy Liu
    Email :     anx.liu@intal.com
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
import argparse
import logging
import os
import re
import sys
import xlwt
from copy import deepcopy
from pprint import pformat
from AnalysisWinPIRALog.MyLog import init_logger

from encoder import XML2Dict


class AnalysisLog:
    def __init__(self, _config_file, _log_file):
        self._config_file = _config_file
        self._log_file = _log_file
        self.config_dict = dict()
        self.log_dict = dict()
        self.result_list = list()
        self._key_word = 'DEV_ADD'
        self.return_value = True

    def parse_config_file(self):
        logging.debug('Into function parse_config_file')
        with open(self._config_file, 'r') as f:
            _xml_str = f.read()

        try:
            _obj = XML2Dict(coding='utf-8')
            self.config_dict = _obj.parse(_xml_str)
            logging.debug('config_dict : %s' % pformat(self.config_dict))
            logging.info('Parse config file done')
            return self.config_dict
        except Exception, e:
            logging.error("Can't parse as XML!")
            logging.exception(e)
            sys.exit(1)

    def warning_duplicate_dev_add(self):
        logging.debug('Into warning_duplicate_dev_add')
        _verify_list = list()
        for _dev_type, _expect_values in self.config_dict.get('xml').iteritems():
            if isinstance(_expect_values, list):
                for _expect_value in _expect_values:
                    if _expect_value.get(self._key_word) in _verify_list:
                        logging.error('Duplicate device address : %s' % _expect_value.get(self._key_word))
                        sys.exit(1)
                    else:
                        _verify_list.append(_expect_value.get(self._key_word))
            elif isinstance(_expect_values, dict):
                if _expect_values.get(self._key_word) in _verify_list:
                    logging.error('Duplicate device address : %s' % _expect_values.get(self._key_word))
                    sys.exit(1)
                else:
                    _verify_list.append(_expect_values.get(self._key_word))
        if len(_verify_list) == 0:
            logging.error("Can't find key word <%s>" % self._key_word)
            sys.exit(1)
        logging.info('Verify duplicate device address done')
        return True

    def parse_log_file(self):
        logging.debug('Into parse_log_file')
        _record = dict()
        _dev_add = ''
        with open(self._log_file, 'r') as f:
            # remove header and footer in log file
            for _line in f.readlines()[12:-3]:
                _line = _line.strip()
                if _line and ':' in _line:
                    if _line.startswith(self._key_word):
                        if _record:
                            self.log_dict.update({_dev_add.strip(): deepcopy(_record)})
                            _record.clear()
                        _key, _dev_add = _line.split(':', 1)
                        _record.update({_key.strip(): _dev_add.strip()})
                    else:
                        _key, _value = _line.split(':', 1)
                        _record.update({_key.strip(): _value.strip()})
            else:
                self.log_dict.update({_dev_add: deepcopy(_record)})
        logging.debug('log_dict : %s' % pformat(self.log_dict))
        logging.info('Parse log file done')
        return self.log_dict

    def verify_result(self):
        for _dev_type, _expect_values in self.config_dict.get('xml').iteritems():
            if isinstance(_expect_values, list):
                logging.debug('_expect_values is list')
                for _expect_value in _expect_values:
                    _key_word = _expect_value.get(self._key_word)
                    if _key_word in self.log_dict:
                        _record = self.log_dict.get(_key_word)
                        if self.compare_result(_expect_value, _record):
                            _record.update({'Result': 'PASSED'})
                        else:
                            _record.update({'Result': 'FAILED'})
                            self.return_value = False
                        self.result_list.append(_record)
                    else:
                        self.result_list.append({self._key_word: _key_word, 'Result': 'Not Found'})
                        self.return_value = False
            elif isinstance(_expect_values, dict):
                logging.debug('_expect_values is dict')
                _key_word = _expect_values.get(self._key_word)
                if _key_word in self.log_dict:
                    _record = self.log_dict.get(_key_word)
                    if self.compare_result(_expect_values, _record):
                        _record.update({'Result': 'PASSED'})
                    else:
                        _record.update({'Result': 'FAILED'})
                        self.return_value = False
                    self.result_list.append(_record)
                else:
                    self.result_list.append({self._key_word: _key_word, 'Result': 'Not Found'})
                    self.return_value = False
        logging.debug('result_list : %s' % pformat(self.result_list))
        logging.info('Verify result done')

    @staticmethod
    def compare_result(_expect_value, _record):
        """
        expect_value:
        {'CLASS': 'BRIDGE_DEV, Host',
         'DEV_ADD': 'S0:B0:D0:F0 0x80000000',
         'LINK': {'capable': {'x4': '2.5Gb'},
                  'negotiated': {'x0': '0.0Gb'}},
         'VID_DID': 'Haswell-E DMI2'}

        _record:
        {'CLASS': 'NETWORK_CTLR, Ethernet controller',
         'DEV_ADD': 'S0:B1:D0:F0 0x80100000',
         'LINK': 'x4 at 5.0Gb capable, x4 at 5.0Gb negotiated',
         'PCIE': 'PCI Express Endpoint',
         'SVID_DID': '8086  Intel Corporation, 35c8',
         'VID_DID': '80861521, Intel Corporation, I350 Gigabit Network Connection'}
        """
        _return_value = True
        _reason = list()
        for _item in _expect_value.iterkeys():
            if _item in _record:
                logging.debug('the key word %s in expect : %s' % (_item, pformat(_expect_value.get(_item))))
                logging.debug('the key word %s in log : %s' % (_item, pformat(_record.get(_item))))
                if 'LINK' == _item:
                    _expect_capable_channel, _expect_capable_speed = _expect_value.get(_item).get('capable').items()[0]
                    _expect_negotiated_channel, _expect_negotiated_speed = \
                        _expect_value.get(_item).get('negotiated').items()[0]
                    pattern = re.compile(r'(\w*) at (.*) capable, (\w*) at (.*) negotiated')
                    m = re.match(pattern, _record.get(_item))
                    _capable_channel, _capable_speed, _negotiated_channel, _negotiated_speed = m.groups()
                    if _expect_capable_channel.strip() == _capable_channel \
                            and _expect_capable_speed.strip() == _capable_speed \
                            and _expect_negotiated_channel.strip() == _negotiated_channel \
                            and _expect_negotiated_speed.strip() == _negotiated_speed:
                        logging.debug('the key word %s compare PASSED' % _item)
                    else:
                        _reason.append('the key word <%s> compare FAILED' % _item)
                        logging.debug('the key word %s compare FAILED' % _item)
                        _return_value = False
                else:
                    if _expect_value.get(_item).strip() in _record.get(_item):
                        logging.debug('the key word %s compare PASSED' % _item)
                    else:
                        _reason.append('the key word <%s> compare FAILED' % _item)
                        logging.debug('the key word %s compare FAILED' % _item)
                        _return_value = False
            else:
                _reason.append('the key word <%s> is not include in log %s' % (_item, pformat(_record)))
                logging.debug('the key word %s is not include in log %s' % (_item, pformat(_record)))
                _return_value = False
        _record.update({'Reason': _reason})
        return _return_value

    def output_detail_result(self, output_file):
        _show_list = ['Result', 'Reason', 'DEV_ADD']
        fp = xlwt.Workbook()
        table = fp.add_sheet('Detail Result')
        for _idx, _title in enumerate(_show_list):
            table.write(0, _idx, _title)

        for _row, _record in enumerate(self.result_list):
            for _column, _title in enumerate(_show_list):
                if _title in _record:
                    if isinstance(_record.get(_title), list):
                        _text = '\n'.join(_record.get(_title))
                    else:
                        _text = _record.get(_title)
                else:
                    _text = ''
                table.write(_row + 1, _column, _text)
        fp.save(output_file)


def parse_command_line():
    """
    parse command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', '-l', action="store", dest="log_file", help="log file path")
    parser.add_argument('--configfile', '-c', action="store", dest="config_file", help="config file path")
    parser.add_argument('--outputfile', '-o', action="store", dest="output_file", help="output file path")
    parser.add_argument('--resultfile', '-r', action="store", dest="result_file", help="result file path")
    parser.add_argument("--debug", '-d', action="store_true", dest="debug", default=False, help="Show debug info")

    args = parser.parse_args()
    config_file = args.config_file
    log_file = args.log_file
    output_file = args.output_file
    result_file = args.result_file

    if config_file is None:
        config_file = 'config.xml'
    if not os.path.exists(config_file):
        logging.error("Can't find config file!")
        logging.error("Please input config file path!")
        parser.print_help()
        sys.exit(1)
    args.config_file = config_file

    if log_file is None:
        log_file = 'log.txt'
    if not os.path.exists(log_file):
        logging.error("Can't find log file!")
        logging.error("Please input log file path!")
        parser.print_help()
        sys.exit(1)
    args.log_file = log_file

    if output_file is None:
        args.output_file = 'output.xls'

    if result_file is None:
        args.result_file = 'result.txt'

    return args


def main():
    args = parse_command_line()

    logger = init_logger(args.debug)
    logger.info('================== Start ==================')
    al = AnalysisLog(_config_file=args.config_file, _log_file=args.log_file)
    al.parse_config_file()
    if al.warning_duplicate_dev_add():
        al.parse_log_file()
        al.verify_result()
        if al.return_value:
            with open(args.result_file, 'w') as f:
                f.write(b'PASSED')
            logger.info('PASSED')
        else:
            with open(args.result_file, 'w') as f:
                f.write(b'FAILED')
            logger.info('FAILED')
        al.output_detail_result(args.output_file)
        logger.info('Detail log please check the %s' % args.output_file)
    logger.info('=================== End ===================')


if __name__ == '__main__':
    main()
