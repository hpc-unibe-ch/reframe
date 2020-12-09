#
# ReFrame generic settings
#
ReframePrefix = '/storage/homefs'

class ReframeSettings:
    job_poll_intervals = [1, 2, 3]
    job_submit_timeout = 60
    checks_path = ['checks/']
    checks_path_recurse = True
    site_configuration = {
        'systems': {
            'generic': {
                'descr': 'Generic example system',
                'hostnames': ['localhost'],
                'partitions': {
                    'login': {
                        'scheduler': 'local',
                        'modules': [],
                        'access':  [],
                        'environs': ['builtin-gcc'],
                        'descr': 'Login nodes'
                    }
                }
            },
            'ubelix': {
                'descr': 'UniBE HPC system UBELiX',
                'hostnames': ['submit'],
                'modules_system': 'lmod',
                'stagedir':   '{}/ms20e149/ReFrame/stage/'.format(ReframePrefix),
                'outputdir':  '{}/ms20e149/ReFrame/output/'.format(ReframePrefix),
                'perflogdir': '{}/ms20e149/ReFrame/logs/'.format(ReframePrefix),
                'resourcesdir': '{}/ms20e149/ReFrame/resources'.format(ReframePrefix),
                'partitions': {
                    'login': {
                        'scheduler': 'local',
                        'modules': [],
                        'access':  [],
                        'environs': ['builtin-gcc'],
                        'descr': 'Login nodes'
                    },
                    'mc': {
                        'scheduler': 'nativeslurm',
                        'modules': [],
                        'access':  [],
                        'environs': ['foss', 'intel', 'pgi'],
                        'descr': 'compute nodes'
                    },
                     'gpu': {
                        'scheduler': 'nativeslurm',
                        'modules': [],
                        'access':  ['--partition=gpu', '--gres=gpu:teslaP100:1'],
                        'environs': ['foss', 'intel', 'pgi'],
                        'descr': 'gpu compute nodes'
                    }
                }
            }
        },
        'environments': {
            '*': {
                'builtin': {
                    'type': 'ProgEnvironment',
                    'cc':  'cc',
                    'cxx': '',
                    'ftn': '',
                },
                'builtin-gcc': {
                    'type': 'ProgEnvironment',
                    'cc':  'gcc',
                    'cxx': 'g++',
                    'ftn': 'gfortran',
                },
                'foss': {
                    'type': 'ProgEnvironment',
                    'modules': ['foss'],
                    'cc':  'mpicc',
                    'cxx': 'mpic++',
                    'ftn': 'mpifort',
                },
                'intel': {
                    'type': 'ProgEnvironment',
                    'modules': ['intel'],
                    'cc':  'mpiicc',
                    'cxx': 'mpiicpc',
                    'ftn': 'mpiifort',
                },
                'pgi': {
                    'type': 'ProgEnvironment',
                    'modules': ['PGI'],
                    'cc':  'pgcc',
                    'cxx': 'pgc++',
                    'ftn': 'pgf90',
                },
            }
        }
    }

    logging_config = {
        'level': 'DEBUG',
        'handlers': [
            {
                'type': 'file',
                'name': 'reframe.log',
                'level': 'DEBUG',
                'format': '[%(asctime)s] %(levelname)s: '
                          '%(check_info)s: %(message)s',
                'append': False,
            },

            # Output handling
            {
                'type': 'stream',
                'name': 'stdout',
                'level': 'INFO',
                'format': '%(message)s'
            },
            {
                'type': 'file',
                'name': 'reframe.out',
                'level': 'INFO',
                'format': '%(message)s',
                'append': False,
            }
        ]
    }

    perf_logging_config = {
        'level': 'DEBUG',
        'handlers': [
            {
                'type': 'filelog',
                'prefix': '%(check_system)s/%(check_partition)s',
                'level': 'INFO',
                'format': (
                    '%(asctime)s|reframe %(version)s|'
                    '%(check_info)s|jobid=%(check_jobid)s|'
                    '%(check_perf_var)s=%(check_perf_value)s|'
                    'ref=%(check_perf_ref)s '
                    '(l=%(check_perf_lower_thres)s, '
                    'u=%(check_perf_upper_thres)s)|'
                    '%(check_perf_unit)s'
                ),
                'append': True
            }
#            {
#                'type': 'file',
#                'name': 'perf_summary.dat',
#                'level': 'DEBUG',
#                'format': (
#                    '%(asctime)s|'
#                    '%(check_info)s|'
#                    '%(check_perf_var)s|'
#                    '%(check_perf_value)s|'
#                    '%(check_perf_ref)s|'
#                    '%(check_perf_lower_thres)s|'
#                    '%(check_perf_upper_thres)s|'
#                    '%(check_perf_unit)s'
#                ),
#                'append': True
#            }
        ]
    }


settings = ReframeSettings()
