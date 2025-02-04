# -*- coding: UTF-8 -*-
"""DSFF package information.

"""
import os
from datetime import datetime

__y = str(datetime.now().year)
__s = "2023"

__author__    = "Alexandre D'Hondt"
__copyright__ = f"© {[__y,__s+'-'+__y][__y != __s]} A. D'Hondt"
__license__   = "GPLv3+ (https://www.gnu.org/licenses/gpl-3.0.html)"

with open(os.path.join(os.path.dirname(__file__), "VERSION.txt")) as f:
    __version__ = f.read().strip()

