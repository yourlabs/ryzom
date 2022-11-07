#!/usr/bin/env python

"""Install the ``ryzom.pth`` file to let python understand the ``ryzom`` encoding."""

from distutils.sysconfig import get_python_lib
import os
import os.path
import site

PTH_FILENAME = "ryzom.pth"
PTH_CONTENT = (
#    "import ryzom_codec.register"
    "import sys; exec('"
    "try:\\n"
    "    import ryzom_codec.register\\n"
    "except ImportError:\\n"
    "    pass\\n"
    "')"
)

try:
    python_lib = get_python_lib()
    with open(os.path.join(python_lib, PTH_FILENAME), "w") as pth_file:
        pth_file.write(PTH_CONTENT)
except Exception:
    pass

try:
    python_lib = get_python_lib(prefix=os.getenv("HOME") + "/.local")
    with open(os.path.join(python_lib, PTH_FILENAME), "w") as pth_file:
        pth_file.write(PTH_CONTENT)
except Exception:
    pass

try:
    python_lib = site.getsitepackages()[0]
    with open(os.path.join(python_lib, PTH_FILENAME), "w") as pth_file:
        pth_file.write(PTH_CONTENT)
except Exception:
    pass

