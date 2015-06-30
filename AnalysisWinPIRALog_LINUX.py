# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

"""
    Name:       AnalysisWinPIRALog_LINUX
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
        self.start = re.compile(r'^[0-9a-f]{2}:[0-9a-f]{2}\.\d')
        self._key_word = 'DEV_NAME'
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

    # def warning_duplicate_dev_add(self):
    # logging.debug('Into warning_duplicate_dev_add')
    # _verify_list = list()
    # for _dev_type, _expect_values in self.config_dict.get('xml').iteritems():
    # if isinstance(_expect_values, list):
    # for _expect_value in _expect_values:
    # if _expect_value.get(self._key_word) in _verify_list:
    #                     logging.error('Duplicate device address : %s' % _expect_value.get(self._key_word))
    #                     sys.exit(1)
    #                 else:
    #                     _verify_list.append(_expect_value.get(self._key_word))
    #         elif isinstance(_expect_values, dict):
    #             if _expect_values.get(self._key_word) in _verify_list:
    #                 logging.error('Duplicate device address : %s' % _expect_values.get(self._key_word))
    #                 sys.exit(1)
    #             else:
    #                 _verify_list.append(_expect_values.get(self._key_word))
    #     if len(_verify_list) == 0:
    #         logging.error("Can't find key word <%s>" % self._key_word)
    #         sys.exit(1)
    #     logging.info('Verify duplicate device address done')
    #     return True

    def parse_log_file(self):
        logging.debug('Into parse_log_file')
        _record = dict()
        _dev_name = ''
        with open(self._log_file, 'r') as f:
            # remove header and footer in log file
            for _line in f.readlines():
                _line = _line.strip()
                if _line and ':' in _line:
                    if re.findall(self.start, _line):
                        if _record:
                            self.log_dict.update({_dev_name.strip(): deepcopy(_record)})
                            _record.clear()
                        _bus_no, _dev_name = _line.split(' ', 1)
                        _record.update({'BUS_NO': _bus_no.strip(), 'DEV_NAME': _dev_name.strip()})
                    else:
                        _key, _value = _line.split(':', 1)
                        _record.update({_key.strip(): _value.strip()})
            else:
                self.log_dict.update({_dev_name.strip(): deepcopy(_record)})
                pass
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
        {'DEV_NAME': 'PCI bridge: Intel Corporation Haswell-E PCI Express Root Port 1 (rev 02) (prog-if 00 [Normal decode])'}

        _record:
        {'ACSCap': 'SrcValid+ TransBlk+ ReqRedir+ CmpltRedir+ UpstreamFwd+ EgressCtrl- DirectTrans-',
        'ACSCtl': 'SrcValid- TransBlk- ReqRedir- CmpltRedir- UpstreamFwd- EgressCtrl- DirectTrans-',
        'AERCap': 'First Error Pointer: 00, GenCap- CGenEn- ChkCap- ChkEn-',
        'Address': 'fee00438  Data: 0000',
        'BUS_NO': '00:01.0',
        'BridgeCtl': 'Parity+ SERR+ NoISA- VGA- MAbort- >Reset- FastB2B-',
        'Bus': 'primary=00, secondary=01, subordinate=01, sec-latency=0',
        'CEMsk': 'RxErr- BadTLP- BadDLLP- Rollover- Timeout- NonFatalErr-',
        'CESta': 'RxErr- BadTLP- BadDLLP- Rollover- Timeout- NonFatalErr-',
        'Capabilities': '[300 v1] Vendor Specific Information: ID=0008 Rev=0 Len=038 <?>',
        'Changed': 'MRL- PresDet- LinkState+',
        'Compliance De-emphasis': '-6dB',
        'Control': 'AttnInd Off, PwrInd Off, Power- Interlock-',
        'DEV_NAME': 'PCI bridge: Intel Corporation Haswell-E PCI Express Root Port 1 (rev 02) (prog-if 00 [Normal decode])',
        'DevCap': 'MaxPayload 256 bytes, PhantFunc 0, Latency L0s <64ns, L1 <1us',
        'DevCap2': 'Completion Timeout: Range BCD, TimeoutDis+, LTR-, OBFF Not Supported ARIFwd+',
        'DevCtl': 'Report errors: Correctable- Non-Fatal+ Fatal+ Unsupported-',
        'DevCtl2': 'Completion Timeout: 260ms to 900ms, TimeoutDis-, LTR-, OBFF Disabled ARIFwd+',
        'DevSta': 'CorrErr- UncorrErr- FatalErr- UnsuppReq- AuxPwr- TransPend-',
        'Flags': 'PMEClk- DSI- D1- D2- AuxCurrent=0mA PME(D0+,D1-,D2-,D3hot+,D3cold+)',
        'I/O behind bridge': '0000f000-00000fff',
        'Kernel driver in use': 'pcieport',
        'Kernel modules': 'shpchp',
        'Latency': '0',
        'LnkCap': 'Port #1, Speed 8GT/s, Width x8, ASPM L1, Latency L0 <512ns, L1 <16us',
        'LnkCtl': 'ASPM Disabled; RCB 64 bytes Disabled- Retrain- CommClk+',
        'LnkCtl2': 'Target Link Speed: 8GT/s, EnterCompliance- SpeedDis-',
        'LnkSta': 'Speed 8GT/s, Width x8, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-',
        'LnkSta2': 'Current De-emphasis Level: -6dB, EqualizationComplete+, EqualizationPhase1+',
        'Masking': '00000003  Pending: 00000000',
        'Memory behind bridge': '91c00000-91cfffff',
        'Prefetchable memory behind bridge': '0000383ffc000000-0000383ffdffffff',
        'RootCap': 'CRSVisible-',
        'RootCtl': 'ErrCorrectable- ErrNon-Fatal+ ErrFatal+ PMEIntEna- CRSVisible-',
        'RootSta': 'PME ReqID 0000, PMEStatus- PMEPending-',
        'Secondary status': '66MHz- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort+ <SERR- <PERR-',
        'SltCap': 'AttnBtn- PwrCtrl- MRL- AttnInd- PwrInd- HotPlug- Surprise-',
        'SltCtl': 'Enable: AttnBtn- PwrFlt- MRL- PresDet- CmdCplt- HPIrq- LinkChg-',
        'SltSta': 'Status: AttnBtn- PowerFlt- MRL- CmdCplt- PresDet+ Interlock-',
        'Status': 'D0 NoSoftRst+ PME-Enable- DSel=0 DScale=0 PME-',
        'Transmit Margin': 'Normal Operating Range, EnterModifiedCompliance- ComplianceSOS-',
        'UEMsk': 'DLP- SDES- TLP- FCP- CmpltTO- CmpltAbrt+ UnxCmplt- RxOF- MalfTLP- ECRC- UnsupReq+ ACSViol-',
        'UESta': 'DLP- SDES- TLP- FCP- CmpltTO- CmpltAbrt- UnxCmplt- RxOF- MalfTLP- ECRC- UnsupReq- ACSViol-',
        'UESvrt': 'DLP+ SDES+ TLP+ FCP+ CmpltTO+ CmpltAbrt+ UnxCmplt+ RxOF+ MalfTLP+ ECRC- UnsupReq- ACSViol+'}
        """
        _return_value = True
        _reason = list()
        _pattern = re.compile(r'Speed\s*(.*),\s*Width\s*(\w*),')
        if 'LnkCap' in _record:
            if 'LnkSta' in _record:
                logging.debug('the key word LnkCap in log : %s' % (pformat(_record.get('LnkCap'))))
                logging.debug('the key word LnkSta in log : %s' % (pformat(_record.get('LnkSta'))))
                l_LnkCap = _pattern.findall(_record.get('LnkCap'))[0]
                logging.debug('l_LnkCap : %s' % pformat(l_LnkCap))
                l_LnkSta = _pattern.findall(_record.get('LnkSta'))[0]
                logging.debug('l_LnkSta : %s' % pformat(l_LnkSta))
                if l_LnkCap == l_LnkSta:
                    logging.debug('Speed and Width compare PASSED')
                else:
                    _reason.append('Speed and Width compare FAILED')
                    logging.debug('Speed and Width compare FAILED')
                    _return_value = False
            else:
                _reason.append('the key word <LnkSta> is not include in log %s' % (pformat(_record)))
                logging.debug('the key word LnkSta is not include in log %s' % (pformat(_record)))
                _return_value = False
        else:
            _reason.append('the key word <LnkCap> is not include in log %s' % (pformat(_record)))
            logging.debug('the key word LnkCap is not include in log %s' % (pformat(_record)))
            _return_value = False
        _record.update({'Reason': _reason})
        return _return_value

    def output_detail_result(self, output_file):
        _show_list = ['Result', 'Reason', 'BUS_NO', 'DEV_NAME']
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
    # if al.warning_duplicate_dev_add():
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
