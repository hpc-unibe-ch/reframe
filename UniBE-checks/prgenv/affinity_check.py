import reframe as rfm
import reframe.utility.sanity as sn


class AffinityTestBase(rfm.RegressionTest):
    def __init__(self, variant):
        super().__init__()
        self.valid_systems = ['ubelix:mc']
        self.valid_prog_environs = ['foss']
        self.build_system = 'Make'
        self.build_system.options = ['-C affinity', 'MPI=1']
        # The github URL can not be specifid as `self.sourcedir` as that
        # would prevent the src folder from being copied to stage which is
        # necessary since these tests need files from it.
        self.prebuild_cmd = ['git clone https://github.com/vkarak/affinity']
        self.executable = './affinity/affinity'
        self.variant = variant
        self.maintainers = ['RS', 'SK']
        self.tags = {'production', 'maintenance'}

    def setup(self, partition, environ, **job_opts):

        def parse_cpus(x):
            return sorted([int(xi) for xi in x.split()])

        re_aff_cores = r'CPU affinity: \[\s+(?P<cpus>[\d+\s+]+)\]'
        self.aff_cores = sn.extractall(
            re_aff_cores, self.stdout, 'cpus', parse_cpus)
        ref_key = 'ref_' + partition.fullname
        self.ref_cores = sn.extractall(
            re_aff_cores, self.cases[self.variant][ref_key],
            'cpus', parse_cpus)
        re_aff_thrds = r'^Tag:[^\n\r]*Thread:\s+(?P<thread>\d+)'
        self.aff_thrds = sn.extractall(re_aff_thrds, self.stdout, 'thread',
                                       int)
        self.ref_thrds = sn.extractall(
            re_aff_thrds, self.cases[self.variant][ref_key],
            'thread', int)
        re_aff_ranks = r'^Tag:[^\n\r]*Rank:\s+(?P<rank>\d+)[\s+\S+]'
        self.aff_ranks = sn.extractall(re_aff_ranks, self.stdout, 'rank', int)
        self.ref_ranks = sn.extractall(
            re_aff_ranks, self.cases[self.variant][ref_key],
            'rank', int)

        # Ranks and threads can be extracted into lists in order to compare
        # them since the affinity programm prints them in ascending order.
        self.sanity_patterns = sn.all([
            sn.assert_eq(self.aff_thrds, self.ref_thrds),
            sn.assert_eq(self.aff_ranks, self.ref_ranks),
            sn.assert_eq(sn.sorted(self.aff_cores), sn.sorted(self.ref_cores))
        ])

        super().setup(partition, environ, **job_opts)


@rfm.parameterized_test(
                        ['omp_bind_threads'],
                        ['omp_bind_cores'])
class AffinityOpenMPTest(AffinityTestBase):
    def __init__(self, variant):
        super().__init__(variant)
        self.descr = 'Checking the cpu affinity for OMP threads.'
        self.cases = {
            'omp_bind_threads': {
                'ref_ubelix:gpu': 'gpu_omp_bind_threads.txt',
                'ref_ubelix:mc': 'mc_omp_bind_threads.txt',
                'num_cpus_per_task:gpu': 3,
                'num_cpus_per_task:mc': 20,
                'ntasks_per_core': None,
                'OMP_PLACES': 'threads',
            },
            'omp_bind_cores': {
                'ref_ubelix:gpu': 'gpu_omp_bind_cores.txt',
                'ref_ubelix:mc': 'mc_omp_bind_cores.txt',
                'num_cpus_per_task:gpu': 3,
                'num_cpus_per_task:mc': 20,
                'ntasks_per_core': 1,
                'OMP_PLACES': 'cores',
            },
        }
        self.variant = variant

    def setup(self, partition, environ, **job_opts):
        self.num_cpus_per_task = (
            self.cases[self.variant]['num_cpus_per_task:%s' % partition.name])
        if self.cases[self.variant]['ntasks_per_core']:
            self.num_tasks_per_core = (
                self.cases[self.variant]['ntasks_per_core'])

        self.num_tasks = 1
        self.variables  = {
            'OMP_NUM_THREADS': str(self.num_cpus_per_task),
            'OMP_PLACES': self.cases[self.variant]['OMP_PLACES']
            # OMP_PROC_BIND is set to TRUE if OMP_PLACES is defined.
            # Both OMP_PROC_BIND values CLOSE and SPREAD give the same
            # result as OMP_PROC_BIND=TRUE when all cores are requested.
        }
        super().setup(partition, environ, **job_opts)


@rfm.parameterized_test(['alternate_socket_filling'],
                        ['consecutive_socket_filling'],
                        ['single_task_per_socket_omp'])
class SocketDistributionTest(AffinityTestBase):
    def __init__(self, variant):
        super().__init__(variant)
        self.descr = 'Checking distribution of ranks and threads over sockets.'
        self.valid_systems = ['ubelix:mc']
        self.cases = {
            'alternate_socket_filling': {
                'ref_ubelix:mc': 'alternate_socket_filling.txt',
                'num_tasks': 20,
                'num_cpus_per_task': 1,
                'num_tasks_per_socket': 10,
                'cpu-bind': None,
            },
            'consecutive_socket_filling': {
                'ref_ubelix:mc': 'consecutive_socket_filling.txt',
                'num_tasks': 20,
                'num_cpus_per_task': 1,
                'num_tasks_per_socket': None,
                'cpu-bind': 'rank',
            },
            'single_task_per_socket_omp': {
                'ref_ubelix:mc': 'single_task_per_socket_omp.txt',
                'num_tasks': 2,
                'num_cpus_per_task': 10,
                'num_tasks_per_socket': 1,
                'cpu-bind': None,
            },
        }
        self.num_tasks = self.cases[variant]['num_tasks']
        self.num_cpus_per_task = self.cases[variant]['num_cpus_per_task']
        self.num_tasks_per_socket = self.cases[variant]['num_tasks_per_socket']

    def setup(self, partition, environ, **job_opts):
        super().setup(partition, environ, **job_opts)
        if self.cases[self.variant]['cpu-bind']:
            self.job.launcher.options = ['--cpu-bind=%s' %
                                         self.cases[self.variant]['cpu-bind']]
