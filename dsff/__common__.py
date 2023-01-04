# -*- coding: UTF-8 -*-
import csv as csvmod
import json
import re
from io import StringIO
from os import makedirs, remove
from os.path import basename, expanduser, isfile, isdir, join, splitext


__all__ = ["basename", "csvmod", "expanduser", "isfile", "isdir", "join", "json", "makedirs", "remove", "splitext",
           "re", "StringIO", "CSV_DELIMITER", "DEFAULT_EXCL", "INMEMORY", "META_EXCL", "MISSING_TOKEN", "TARGET_NAME"]


CSV_DELIMITER = ";"
DEFAULT_EXCL  = ("hash", "realpath", "format", "size", "ctime", "mtime")  # origin: executables used in the Packing Box
INMEMORY      = "<memory>"
META_EXCL     = ["created", "modified", "revision"]
MISSING_TOKEN = "?"
TARGET_NAME   = "label"

