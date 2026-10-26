# -*- coding: UTF-8 -*-
import csv as csvmod
import json
import re
from ast import literal_eval
from functools import wraps
from io import BytesIO, StringIO
from os import makedirs, remove
from os.path import basename, exists, expanduser, isfile, isdir, join, splitext
try:  # pragma: no cover
    import pyarrow
    import pyarrow.feather as feather
    import pyarrow.orc as orc
    import pyarrow.parquet as parquet
    PYARROW = True
except ImportError:  # pragma: no cover
    PYARROW = False


__all__ = ["basename", "csvmod", "ensure_str", "exists", "expanduser", "isfile", "isdir", "join", "json",
           "literal_eval", "makedirs", "re", "remove", "splitext", "text_or_path", "BytesIO", "StringIO",
           "CSV_DELIMITER", "DEFAULT_EXCL", "INMEMORY", "META_EXCL", "MISSING_TOKEN", "PYARROW", "TARGET_NAME"]
if PYARROW:
    __all__ += ["feather", "orc", "parquet", "pyarrow"]


CSV_DELIMITER = ";"
DEFAULT_EXCL  = ("hash", "realpath", "format", "size", "ctime", "mtime")  # origin: executables used in the Packing Box
INMEMORY      = "<memory>"
META_EXCL     = ["created", "modified", "revision"]
MISSING_TOKEN = "?"
TARGET_NAME   = "label"


def ensure_str(string):
    try:
        return string.decode()
    except AttributeError:
        return str(string)


def text_or_path(f=None, folders=False):
    """ Decorate a function taking a text, bytes or a path, reading the file in the latter case. A folder is passed as
         a path if folders is True, otherwise the function returns False (as no file content can be checked). """
    if f is None:
        return lambda f: text_or_path(f, folders)
    @wraps(f)
    def _wrapper(txt_path, *args, **kwargs):
        if not isinstance(txt_path, bytes):
            if isinstance(txt_path, str):
                # a string is a path if it points to an existing file or folder (a multiline string is a text)
                if "\n" not in txt_path and exists(p := expanduser(txt_path)):
                    if isdir(p):
                        if not folders:
                            return False
                        txt_path = p
                    else:
                        with open(p, "rb") as fh:
                            txt_path = fh.read()
                else:
                    txt_path = txt_path.encode()
            else:
                raise ValueError(f"Bad input text or path ({type(txt_path)})")
        return f(txt_path, *args, **kwargs)
    return _wrapper

