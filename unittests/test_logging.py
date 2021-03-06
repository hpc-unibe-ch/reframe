# Copyright 2016-2020 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import logging
import logging.handlers
import os
import pytest
import sys
import re
import tempfile
import time
import unittest
from datetime import datetime

import reframe as rfm
import reframe.core.logging as rlog
from reframe.core.exceptions import ConfigError, ReframeError
from reframe.core.launchers.registry import getlauncher
from reframe.core.schedulers import Job
from reframe.core.schedulers.registry import getscheduler


class _FakeCheck(rfm.RegressionTest):
    pass


def _setup_fake_check():
    # A bit hacky, but we don't want to run a full test every time
    test = _FakeCheck()
    test._job = Job.create(getscheduler('local')(),
                           getlauncher('local')(),
                           'fakejob')
    test.job._completion_time = time.time()
    return test


class TestLogger(unittest.TestCase):
    def setUp(self):
        tmpfd, self.logfile = tempfile.mkstemp()
        os.close(tmpfd)

        self.logger  = rlog.Logger('reframe')
        self.handler = logging.handlers.RotatingFileHandler(self.logfile)
        self.formatter = rlog.RFC3339Formatter(
            fmt='[%(asctime)s] %(levelname)s: %(check_name)s: %(message)s',
            datefmt='%FT%T')

        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

        # Use the logger adapter that defines check_name
        self.logger_without_check = rlog.LoggerAdapter(self.logger)

        # Logger adapter with an associated check
        self.logger_with_check = rlog.LoggerAdapter(self.logger,
                                                    _setup_fake_check())

    def tearDown(self):
        os.remove(self.logfile)

    def found_in_logfile(self, pattern):
        found = False
        with open(self.logfile, 'rt') as fp:
            found = re.search(pattern, fp.read()) is not None

        return found

    def test_invalid_loglevel(self):
        with pytest.raises(ValueError):
            self.logger.setLevel('level')

        with pytest.raises(ValueError):
            rlog.Logger('logger', 'level')

    def test_custom_loglevels(self):
        self.logger_without_check.info('foo')
        self.logger_without_check.verbose('bar')

        assert os.path.exists(self.logfile)
        assert self.found_in_logfile('info')
        assert self.found_in_logfile('verbose')
        assert self.found_in_logfile('reframe')

    def test_check_logger(self):
        self.logger_with_check.info('foo')
        self.logger_with_check.verbose('bar')

        assert os.path.exists(self.logfile)
        assert self.found_in_logfile('info')
        assert self.found_in_logfile('verbose')
        assert self.found_in_logfile('_FakeCheck')

    def test_handler_types(self):
        assert issubclass(logging.Handler, rlog.Handler)
        assert issubclass(logging.StreamHandler, rlog.Handler)
        assert issubclass(logging.FileHandler, rlog.Handler)
        assert issubclass(logging.handlers.RotatingFileHandler, rlog.Handler)

        # Try to instantiate rlog.Handler
        with pytest.raises(TypeError):
            rlog.Handler()

    def test_custom_handler_levels(self):
        self.handler.setLevel('verbose')
        self.handler.setLevel(rlog.VERBOSE)

        self.logger_with_check.debug('foo')
        self.logger_with_check.verbose('bar')

        assert not self.found_in_logfile('foo')
        assert self.found_in_logfile('bar')

    def test_logger_levels(self):
        self.logger_with_check.setLevel('verbose')
        self.logger_with_check.setLevel(rlog.VERBOSE)

        self.logger_with_check.debug('bar')
        self.logger_with_check.verbose('foo')

        assert not self.found_in_logfile('bar')
        assert self.found_in_logfile('foo')

    def test_rfc3339_timezone_extension(self):
        self.formatter = rlog.RFC3339Formatter(
            fmt=('[%(asctime)s] %(levelname)s: %(check_name)s: '
                 'ct:%(check_job_completion_time)s: %(message)s'),
            datefmt='%FT%T%:z')
        self.handler.setFormatter(self.formatter)
        self.logger_with_check.info('foo')
        self.logger_without_check.info('foo')
        assert not self.found_in_logfile(r'%%:z')
        assert self.found_in_logfile(r'\[.+(\+|-)\d\d:\d\d\]')
        assert self.found_in_logfile(r'ct:.+(\+|-)\d\d:\d\d')

    def test_rfc3339_timezone_wrong_directive(self):
        self.formatter = rlog.RFC3339Formatter(
            fmt='[%(asctime)s] %(levelname)s: %(check_name)s: %(message)s',
            datefmt='%FT%T:z')
        self.handler.setFormatter(self.formatter)
        self.logger_without_check.info('foo')
        assert self.found_in_logfile(':z')


class TestLoggingConfiguration(unittest.TestCase):
    def setUp(self):
        tmpfd, self.logfile = tempfile.mkstemp(dir='.')
        os.close(tmpfd)
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {
                    'type': 'file',
                    'name': self.logfile,
                    'level': 'WARNING',
                    'format': '[%(asctime)s] %(levelname)s: '
                              '%(check_name)s: %(message)s',
                    'datefmt': '%F',
                    'append': True,
                }
            ]
        }
        self.check = _FakeCheck()

    def tearDown(self):
        if os.path.exists(self.logfile):
            os.remove(self.logfile)

    def found_in_logfile(self, string):
        for handler in rlog.getlogger().logger.handlers:
            handler.flush()
            handler.close()

        found = False
        with open(self.logfile, 'rt') as f:
            found = string in f.read()

        return found

    def close_handlers(self):
        for h in rlog.getlogger().logger.handlers:
            h.close()

    def flush_handlers(self):
        for h in rlog.getlogger().logger.handlers:
            h.flush()

    def test_valid_level(self):
        rlog.configure_logging(self.logging_config)
        assert rlog.INFO == rlog.getlogger().getEffectiveLevel()

    def test_no_handlers(self):
        del self.logging_config['handlers']
        with pytest.raises(ValueError):
            rlog.configure_logging(self.logging_config)

    def test_empty_handlers(self):
        self.logging_config['handlers'] = []
        with pytest.raises(ValueError):
            rlog.configure_logging(self.logging_config)

    def test_handler_level(self):
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().info('foo')
        rlog.getlogger().warning('bar')

        assert not self.found_in_logfile('foo')
        assert self.found_in_logfile('bar')

    def test_handler_append(self):
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('foo')
        self.close_handlers()

        # Reload logger
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('bar')

        assert self.found_in_logfile('foo')
        assert self.found_in_logfile('bar')

    def test_handler_noappend(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {
                    'type': 'file',
                    'name': self.logfile,
                    'level': 'WARNING',
                    'format': '[%(asctime)s] %(levelname)s: %(message)s',
                    'datefmt': '%F',
                    'append': False,
                }
            ]
        }

        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('foo')
        self.close_handlers()

        # Reload logger
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('bar')

        assert not self.found_in_logfile('foo')
        assert self.found_in_logfile('bar')

    def test_date_format(self):
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('foo')
        assert self.found_in_logfile(datetime.now().strftime('%F'))

    def test_unknown_handler(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {'type': 'stream', 'name': 'stderr'},
                {'type': 'foo'}
            ],
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_handler_syntax_no_type(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'name': 'stderr'}]
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_handler_convert_syntax(self):
        old_syntax = {
            self.logfile: {
                'level': 'INFO',
                'format': '%(message)s',
                'append': False,
            },
            '&1': {
                'level': 'INFO',
                'format': '%(message)s'
            },
            '&2': {
                'level': 'ERROR',
                'format': '%(message)s'
            }
        }

        new_syntax = [
            {
                'type': 'file',
                'name': self.logfile,
                'level': 'INFO',
                'format': '%(message)s',
                'append': False
            },
            {
                'type': 'stream',
                'name': 'stdout',
                'level': 'INFO',
                'format': '%(message)s'
            },
            {
                'type': 'stream',
                'name': 'stderr',
                'level': 'ERROR',
                'format': '%(message)s'
            }
        ]

        self.assertCountEqual(new_syntax,
                              rlog._convert_handler_syntax(old_syntax))

    def test_stream_handler_stdout(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'stream', 'name': 'stdout'}],
        }
        rlog.configure_logging(self.logging_config)
        raw_logger = rlog.getlogger().logger
        assert len(raw_logger.handlers) == 1
        handler = raw_logger.handlers[0]

        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout

    def test_stream_handler_stderr(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'stream', 'name': 'stderr'}],
        }

        rlog.configure_logging(self.logging_config)
        raw_logger = rlog.getlogger().logger
        assert len(raw_logger.handlers) == 1
        handler = raw_logger.handlers[0]

        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stderr

    def test_multiple_handlers(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {'type': 'stream', 'name': 'stderr'},
                {'type': 'file', 'name': self.logfile},
                {'type': 'syslog', 'address': '/dev/log'}
            ],
        }
        rlog.configure_logging(self.logging_config)
        assert len(rlog.getlogger().logger.handlers) == 3

    def test_file_handler_timestamp(self):
        self.logging_config['handlers'][0]['timestamp'] = '%F'
        rlog.configure_logging(self.logging_config)
        rlog.getlogger().warning('foo')
        logfile = '%s_%s' % (self.logfile, datetime.now().strftime('%F'))
        assert os.path.exists(logfile)
        os.remove(logfile)

    def test_file_handler_syntax_no_name(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {'type': 'file'}
            ],
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_stream_handler_unknown_stream(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [
                {'type': 'stream', 'name': 'foo'},
            ],
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_syslog_handler(self):
        import platform

        if platform.system() == 'Linux':
            addr = '/dev/log'
        elif platform.system() == 'Darwin':
            addr = '/dev/run/syslog'
        else:
            pytest.skip()

        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'syslog', 'address': addr}]
        }
        rlog.getlogger().info('foo')

    def test_syslog_handler_no_address(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'syslog'}]
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_syslog_handler_unknown_facility(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'syslog', 'facility': 'foo'}]
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_syslog_handler_unknown_socktype(self):
        self.logging_config = {
            'level': 'INFO',
            'handlers': [{'type': 'syslog', 'socktype': 'foo'}]
        }
        with pytest.raises(ConfigError):
            rlog.configure_logging(self.logging_config)

    def test_global_noconfig(self):
        # This is to test the case when no configuration is set, but since the
        # order the unit tests are invoked is arbitrary, we emulate the
        # 'no-config' state by passing `None` to `configure_logging()`

        rlog.configure_logging(None)
        assert rlog.getlogger() is rlog.null_logger

    def test_global_config(self):
        rlog.configure_logging(self.logging_config)
        assert rlog.getlogger() is not rlog.null_logger

    def test_logging_context(self):
        rlog.configure_logging(self.logging_config)
        with rlog.logging_context() as logger:
            assert logger is rlog.getlogger()
            assert logger is not rlog.null_logger
            rlog.getlogger().error('error from context')

        assert self.found_in_logfile('reframe')
        assert self.found_in_logfile('error from context')

    def test_logging_context_check(self):
        rlog.configure_logging(self.logging_config)
        with rlog.logging_context(check=self.check):
            rlog.getlogger().error('error from context')

        rlog.getlogger().error('error outside context')
        assert self.found_in_logfile(
            '_FakeCheck: %s: error from context' % sys.argv[0])
        assert self.found_in_logfile(
            'reframe: %s: error outside context' % sys.argv[0])

    def test_logging_context_error(self):
        rlog.configure_logging(self.logging_config)
        try:
            with rlog.logging_context(level=rlog.ERROR):
                raise ReframeError('error from context')

            pytest.fail('logging_context did not propagate the exception')
        except ReframeError:
            pass

        assert self.found_in_logfile('reframe')
        assert self.found_in_logfile('error from context')
