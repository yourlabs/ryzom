#!/usr/bin/env python

"""Install the ``ryzom.pth`` file to let python understand the ``ryzom`` encoding."""

from distutils.sysconfig import get_python_lib
import os.path


PTH_FILENAME = "ryzom.pth"
PTH_CONTENT = (
    "import ryzom_codec.register"
#    "import sys; exec('"
#    "try:\\n"
#    "    import ryzom.codec.register\\n"
#    "except ImportError:\\n"
#    "    pass\\n"
#    "')"
)

python_lib = get_python_lib()
with open(os.path.join(python_lib, PTH_FILENAME), "w") as pth_file:
    pth_file.write(PTH_CONTENT)
