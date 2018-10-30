import reframe as rfm
import reframe.utility.sanity as sn


@rfm.parameterized_test([True], [False])
class OpenaccCudaCpp(rfm.RegressionTest):
    def __init__(self, withmpi):
        super().__init__()
        name_suffix = 'WithMPI' if withmpi else 'WithoutMPI'
        self.name = 'OpenaccCudaCPP' + name_suffix
        self.descr = 'test for OpenACC, CUDA, MPI, and C++'
        self.valid_systems = ['daint:gpu', 'dom:gpu', 'kesch:cn']
        self.valid_prog_environs = ['PrgEnv-cray', 'PrgEnv-pgi',
                                    'PrgEnv-cray-c2sm',
                                    'PrgEnv-cray-c2sm-gpu'
                                    'PrgEnv-pgi-c2sm',
                                    'PrgEnv-pgi-c2sm-gpu',
                                    'PrgEnv-gnu-c2sm']
        self.build_system = 'Make'
        self.build_system.fflags = ['-O2']
        if self.current_system.name in ['daint', 'dom']:
            self.modules = ['craype-accel-nvidia60']
            self.variables = {
                'MPICH_RDMA_ENABLED_CUDA': '1',
                'CRAY_CUDA_MPS': '1'
            }
            self.num_tasks = 12
            self.num_tasks_per_node = 12
            self.num_gpus_per_node = 1
            self.build_system.options = ['NVCC_FLAGS="-arch=compute_60"']
        elif self.current_system.name in ['kesch']:
            self.modules = ['craype-accel-nvidia35']
            self.variables = {
                'MV2_USE_CUDA': '1',
                'G2G': '1'
            }
            self.num_tasks = 8
            self.num_tasks_per_node = 8
            self.num_gpus_per_node = 8
            self.build_system.options = ['NVCC_FLAGS="-arch=compute_37"']

        if withmpi:
            self.build_system.cppflags = ['-DUSE_MPI']
        else:
            if self.current_system.name == 'kesch':
                self.valid_prog_environs = ['PrgEnv-cray-nompi',
                                            'PrgEnv-pgi-nompi']

            self.num_tasks = 1
            self.num_tasks_per_node = 1
            self.num_gpus_per_node = 1

        self.executable = 'openacc_cuda_mpi_cppstd'
        self.sanity_patterns = sn.assert_found(r'Result:\s+OK', self.stdout)
        self.maintainers = ['AJ', 'VK']
        self.tags = {'production'}

    def setup(self, partition, environ, **job_opts):
        if environ.name.startswith('PrgEnv-cray'):
            self.build_system.fflags += ['-hacc', '-hnoomp']
        elif environ.name.startswith('PrgEnv-pgi'):
            self.build_system.fflags += ['-acc']
            if self.current_system.name in ['daint', 'dom']:
                self.build_system.fflags += ['-ta:tesla:cc60']
                self.build_system.ldflags = ['-acc', '-ta:tesla:cc60',
                                             '-Mnorpath', '-lstdc++']
            elif self.current_system.name == 'kesch':
                self.build_system.fflags += ['-ta=tesla,cc35,cuda8.0']
                self.build_system.ldflags = [
                    '-acc', '-ta:tesla:cc35,cuda8.0', '-lstdc++',
                    '-L/global/opt/nvidia/cudatoolkit/8.0.61/lib64',
                    '-lcublas', '-lcudart']

        super().setup(partition, environ, **job_opts)
