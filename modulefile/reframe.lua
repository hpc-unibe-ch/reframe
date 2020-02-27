require 'os'

help([[
Description
===========
Provide the regression test suite ReFrame
]])

whatis("Description: Provide the regression test suite ReFrame")

conflict("reframe")
load("Python")
-- assume that $HOME has not been clobbered or modified
base = pathJoin(os.getenv("HOME"), "reframe")
run = pathJoin(os.getenv("HOME"), "ReFrame")
-- Note: EASYBUILD_PREFIX implicitly sets EASYBUILD_BUILDPATH,
-- EASYBUILD_SOURCEPATH and EASYBUILD_INSTALLPATH unless these are overridden
setenv("RFM_NOBACKUP", pathJoin(run, "stage"))
setenv("RFM_ROOT", base)
prepend_path("PATH", pathJoin(base, "bin"))


