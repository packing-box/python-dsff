# -*- coding: UTF-8 -*-
import csv as csvmod
import json
import re
from ast import literal_eval
from io import BytesIO, StringIO
from os import makedirs, remove
from os.path import basename, expanduser, isfile, isdir, join, splitext
try:  # pragma: no cover
    import pyarrow
    import pyarrow.feather as feather
    import pyarrow.orc as orc
    import pyarrow.parquet as parquet
    import pandas
    PYARROW = True
except ImportError:  # pragma: no cover
    PYARROW = False


__all__ = ["basename", "csvmod", "expanduser", "isfile", "isdir", "join", "json", "literal_eval", "makedirs",
           "remove", "splitext", "re", "BytesIO", "StringIO",
           "CSV_DELIMITER", "DEFAULT_EXCL", "INMEMORY", "META_EXCL", "MISSING_TOKEN", "PYARROW", "TARGET_NAME"]
if PYARROW:
    __all__ += ["feather", "orc", "pandas", "pyarrow", "parquet"]


CSV_DELIMITER = ";"
DEFAULT_EXCL  = ("hash", "realpath", "format", "size", "ctime", "mtime")  # origin: executables used in the Packing Box
INMEMORY      = "<memory>"
META_EXCL     = ["created", "modified", "revision"]
MISSING_TOKEN = "?"
TARGET_NAME   = "label"

