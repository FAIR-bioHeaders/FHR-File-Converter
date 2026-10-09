"""Deprecated name of :mod:`bioheaders`, kept so existing code keeps working.

The ``fhr`` package was renamed ``bioheaders`` (distribution ``fair-bioheaders``)
in 0.4.0. Importing ``fhr`` warns once and then makes ``fhr`` and ``fhr.cli`` the
very same module objects as ``bioheaders`` and ``bioheaders.cli``, so attributes,
private helpers, and monkeypatching behave exactly as before. The ``fhr-*``
commands do not import this module and never print the warning.

This is a single module rather than an ``fhr/`` package on purpose: ``pip``
upgrades ``fhr`` 0.3 to the ``fhr`` 0.4 compatibility distribution after
installing ``fair-bioheaders``, and removing 0.3 deletes the files it installed,
which include ``fhr/__init__.py`` but not ``fhr.py``.
"""

import sys
import warnings

import bioheaders
import bioheaders.cli

warnings.warn(
    "The 'fhr' package is now 'bioheaders' (install 'fair-bioheaders'); "
    "replace 'import fhr' with 'import bioheaders'. "
    "The 'fhr' name will keep working for now.",
    DeprecationWarning,
    stacklevel=2,
)

sys.modules[__name__ + ".cli"] = bioheaders.cli
sys.modules[__name__] = bioheaders
