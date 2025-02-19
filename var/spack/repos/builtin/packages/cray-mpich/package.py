# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack.package import *
from spack.pkg.builtin.mpich import MpichEnvironmentModifications
from spack.util.module_cmd import get_path_args_from_module_line, module


class CrayMpich(MpichEnvironmentModifications, Package):
    """Cray's MPICH is a high performance and widely portable implementation of
    the Message Passing Interface (MPI) standard."""

    homepage = "https://docs.nersc.gov/development/compilers/wrappers/"
    has_code = False  # Skip attempts to fetch source that is not available

    maintainers("haampie")

    version("8.1.25")
    version("8.1.24")
    version("8.1.21")
    version("8.1.14")
    version("8.1.7")
    version("8.1.0")
    version("8.0.16")
    version("8.0.14")
    version("8.0.11")
    version("8.0.9")
    version("7.7.16")
    version("7.7.15")
    version("7.7.14")
    version("7.7.13")

    depends_on("cray-pmi")
    depends_on("libfabric")

    requires("platform=linux", msg="Cray MPICH is only available on Cray")

    # cray-mpich 8.1.7: features MPI compiler wrappers
    variant("wrappers", default=True, when="@8.1.7:", description="enable MPI wrappers")

    provides("mpi@3")

    canonical_names = {
        "gcc": "GNU",
        "cce": "CRAY",
        "intel": "INTEL",
        "clang": "ALLINEA",
        "aocc": "AOCC",
    }

    @property
    def modname(self):
        return "cray-mpich/{0}".format(self.version)

    @property
    def external_prefix(self):
        mpich_module = module("show", self.modname).splitlines()

        for line in mpich_module:
            if "CRAY_MPICH_DIR" in line:
                return get_path_args_from_module_line(line)[0]

        # Fixes an issue on Archer2 cray-mpich/8.0.16 where there is
        # no CRAY_MPICH_DIR variable in the module file.
        for line in mpich_module:
            if "CRAY_LD_LIBRARY_PATH" in line:
                libdir = get_path_args_from_module_line(line)[0]
                return os.path.dirname(os.path.normpath(libdir))

    def setup_run_environment(self, env):
        if self.spec.satisfies("+wrappers"):
            self.setup_mpi_wrapper_variables(env)
            return

        env.set("MPICC", self.compiler.cc)
        env.set("MPICXX", self.compiler.cxx)
        env.set("MPIFC", self.compiler.fc)
        env.set("MPIF77", self.compiler.f77)

    def setup_dependent_package(self, module, dependent_spec):
        spec = self.spec
        if spec.satisfies("+wrappers"):
            MpichEnvironmentModifications.setup_dependent_package(self, module, dependent_spec)
        elif spack_cc is not None:
            spec.mpicc = spack_cc
            spec.mpicxx = spack_cxx
            spec.mpifc = spack_fc
            spec.mpif77 = spack_f77

    def install(self, spec, prefix):
        raise InstallError(
            self.spec.format(
                "{name} is not installable, you need to specify "
                "it as an external package in packages.yaml"
            )
        )

    @property
    def headers(self):
        hdrs = find_headers("mpi", self.prefix.include, recursive=True)
        hdrs.directories = os.path.dirname(hdrs[0])
        return hdrs

    @property
    def libs(self):
        query_parameters = self.spec.last_query.extra_parameters

        libraries = ["libmpich"]

        if "cxx" in query_parameters:
            libraries.extend(["libmpicxx", "libmpichcxx"])

        if "f77" in query_parameters:
            libraries.extend(["libmpifort", "libmpichfort", "libfmpi", "libfmpich"])

        if "f90" in query_parameters:
            libraries.extend(["libmpif90", "libmpichf90"])

        libs = find_libraries(libraries, root=self.prefix.lib, recursive=True)
        libs += find_libraries(libraries, root=self.prefix.lib64, recursive=True)

        return libs
