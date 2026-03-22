"""
Runtime hook for --onefile portable build.
Patches fbs_runtime._frozen.get_resource_dirs to include sys._MEIPASS
so that resources bundled via --add-data are found correctly.
"""
import sys
import os

_orig_get_resource_dirs = None

def _patched_get_resource_dirs():
    dirs = _orig_get_resource_dirs()
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and meipass not in dirs:
        dirs = [meipass] + dirs
    return dirs

import fbs_runtime._frozen as _frozen
_orig_get_resource_dirs = _frozen.get_resource_dirs
_frozen.get_resource_dirs = _patched_get_resource_dirs
