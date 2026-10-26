# -*- coding: UTF-8 -*-
import builtins
import logging
import types
from ast import literal_eval
from datetime import datetime
from functools import wraps
from getpass import getuser
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from .__common__ import *
from .arff import *
from .csv import *
from .dataset import *
from .db import *
if PYARROW:  # pragma: no cover
    from .pa import *


_FORMAT_TEXT_ALIAS = {'arff': "ARFF", 'csv': "CSV", 'db': "SQL", 'orc': "ORC"}
_NO_EXT_FORMAT     = ["dataset"]


def _open_workbook(path_or_fh):
    """ Load a workbook and check that it complies with DSFF. """
    # openpyxl only validates the extension of a path, hence open the file to allow '.dsff'
    try:
        if hasattr(path_or_fh, "read"):
            wb = load_workbook(path_or_fh)
        else:
            with open(path_or_fh, 'rb') as fh:
                wb = load_workbook(fh)
    except Exception:
        raise BadDsffFile("File is not a DSFF file")
    # check that the file has only 2 worksheets: 'data' and 'features'
    if wb.sheetnames != ["data", "features"]:
        raise BadDsffFile("File is not a DSFF file")
    # check that the 'features' worksheet has 2 columns: 'name' and 'description'
    for headers in wb['features'].rows:
        if len(headers) != 2 or headers[0].value != "name" or headers[1].value != "description":
            raise BadDsffFile("The features worksheet does not comply with DSFF")
        break
    return wb


@text_or_path
def is_dsff(data, **kw):
    """ Check if the input data or path is a valid DSFF. """
    try:
        _open_workbook(BytesIO(data))
        return True
    except BadDsffFile:
        return False


__all__ = ["DSFF"] + [k for k, v in list(globals().items()) if k.startswith(("is_", "load_")) and callable(v) and \
                      getattr(v, "__module__", "").startswith("dsff")]


for name, etype in [("BadDsffFile", "OSError"), ("BadInputData", "ValueError"), ("EmptyDsffFile", "ValueError")]:
    if not hasattr(builtins, name):
        exec(f"class {name}({etype}): __module__ = 'builtins'")
        setattr(builtins, name, locals()[name])


def _bind_from(dsff):
    def _adapt_name(f):
        def _wrapper(*a, **kw):
            path = None
            if len(a) > 0:
                path, a = a[0], a[1:]
            elif 'path' in kw:
                path = kw.pop('path')
            if dsff.mode == "r":
                raise ValueError("DSFF opened in read-only mode")
            path = _fix_path(path or (INMEMORY if dsff.name == INMEMORY else _default_name(dsff)),
                             f.__name__.split("_", 1)[1], True)
            if path == INMEMORY:
                raise ValueError("no path specified")
            dsff.logger.debug(f"creating DSFF from {path}...")
            return f(dsff, path, *a, **kw)
        setattr(dsff, f.__name__, _wrapper)
        return _wrapper
    return _adapt_name


def _bind_to(dsff):
    def _is_empty(f):
        def _wrapper(*a, **kw):
            if len(dsff) == 0:
                raise EmptyDsffFile("No data")
            path = None
            if len(a) > 0:
                path, a = a[0], a[1:]
            elif 'path' in kw:
                path = kw.pop('path')
            path = _fix_path(path or _default_name(dsff), fmt := f.__name__.split("_", 1)[1])
            dsff.logger.debug(f"converting DSFF to {path}..." if 'text' not in kw or kw['text'] else \
                              f"converting DSFF to {_FORMAT_TEXT_ALIAS.get(fmt, fmt.capitalize())}...")
            return f(dsff, path, *a, **kw)
        setattr(dsff, f.__name__, _wrapper)
        return _wrapper
    return _is_empty


def _default_name(dsff):
    name = dsff.name
    if name == INMEMORY:
        return "undefined"
    return name[:-5] if name.endswith(".dsff") else name


def _fix_path(path, ext, existing=False):
    """ Append the extension of the format to the path, unless it already has it (or, for an input file, unless the
         path already points to a file). """
    if path == INMEMORY:
        return path
    path = expanduser(path)
    if ext is None or ext in _NO_EXT_FORMAT or path.lower().endswith(f".{ext}") or existing and isfile(path):
        return path
    return f"{path}.{ext}"


def _to_cell(value, missing=MISSING_TOKEN):
    """ Convert a value to what is stored in a cell ; scalars (bool, int, float) are stored natively. """
    if value is None:
        return missing
    if isinstance(value, (bool, int, float)):
        return value
    return _eval(str(value))


def _eval(value):
    """ Evaluate a string holding a scalar (bool, int or float), otherwise keep it as is. """
    if not isinstance(value, str):
        return value
    try:
        v = literal_eval(value)
    except Exception:
        return value
    return v if isinstance(v, (bool, int, float)) else value


class DSFF:
    """ DataSet File Format.
    
    Modes:          r   r+  w   w+
        --------------------------
        read        *   *       *
        write           *   *   *
        create              *   *
        truncate            *   *
    
    Important note: XSLX format has a limitation of 1,048,576 rows per sheet.
    """
    def __init__(self, path=None, mode=None, logger=None):
        if mode is None:
            mode = "rw"[path in [None, INMEMORY]]
        if re.match(r"[rw]\+?$", mode) is None:
            raise ValueError("Mode should be one of: r, r+, w, w+")
        self.__change = False
        self.__logger = logger or logging.getLogger("DSFF")
        self.__name = None
        self.__path = path
        self.__mode = mode
        # depending on the mode, bind the necessary methods
        if mode in ["r+", "w", "w+"]:
            self.save = types.MethodType(lambda dsff: dsff._DSFF__save(), self)
        self.logger.debug("binding write methods")
        for name, obj in globals().items():
            if name.startswith("from_"):
                _bind_from(self)(obj)
        self.logger.debug("binding read methods")
        for name, obj in globals().items():
            if name.startswith("to_"):
                _bind_to(self)(obj)
        # perform checks
        if mode in ["r", "r+"]:
            if path is None:
                raise ValueError("No input path to a .dsff file provided")
            if path != INMEMORY and not isfile(path):
                raise FileNotFoundError("Input .dsff does not exist")            
        # if the target path exists and is a file, open it
        if mode in ["r", "r+"] and path != INMEMORY:
            self.__wb = _open_workbook(path)
            return
        # otherwise, create a new workbook with the default worksheets
        if path is not None and isfile(self.path):
            remove(self.path)  # re-create
        self.__wb = Workbook()
        del self.__wb['Sheet']  # remove the default sheet
        for ws in ["data", "features"]:
            self.__wb.create_sheet(ws)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, *args):
        # do not save a dataset that may be incomplete
        if exc_type is None:
            self.__save()
        self.close()
    
    def __getitem__(self, name):
        if name in ["data", "features"]:
            return self.__wb[name]
        # the common property 'description' is used to store the metadata of the dataset, hence 'description' can be
        #  used as a key in the metadata but not from the common properties
        try:
            if name != "description":
                return getattr(self.__wb.properties, name)
        except AttributeError:
            pass
        return self.metadata[name]
    
    def __len__(self):
        return len(self.data)
    
    def __setitem__(self, name, value):
        if name in ["data", "features"]:
            raise ValueError(f"'{name}' is a name reserved for a worksheet")
        self.__check_writable()
        # see the note from __getitem__ related to 'description'
        if hasattr(self.__wb.properties, name) and name != "description":
            setattr(self.__wb.properties, name, value)
        d = self.metadata
        d[name] = value
        self.__wb.properties.description = json.dumps(d)
        self.__change = True
    
    def __check_writable(self):
        if self.mode == "r":
            raise ValueError("DSFF opened in read-only mode")
    
    def __eval(self, v):
        return _eval(v)
    
    def __save(self):
        if self.mode == "r" or self.path == INMEMORY:
            return
        if self.__change:
            props = self.__wb.properties
            if props.creator is None or props.creator == "openpyxl":
                props.creator = getuser()
            props.title = self.name
            props.description = json.dumps(self.metadata)
            if isfile(self.path) and self.mode.startswith("w"):
                remove(self.path)
            self.__wb.save(self.path)
            self.__change = False
    
    def _to_table(self):
        if not PYARROW:
            raise NotImplementedError("This method is available only wheh Pyarrow is installed")
        data = self.data
        headers, cols = [str(h) for h in data[0]], []
        for col in (zip(*data[1:]) if len(data) > 1 else [[] for _ in headers]):
            col = [None if c is None or c == MISSING_TOKEN else c for c in col]
            try:
                cols.append(pyarrow.array(col))
            except (pyarrow.ArrowInvalid, pyarrow.ArrowTypeError):
                # mixed types, e.g. strings and numbers ; fall back to strings
                cols.append(pyarrow.array([None if c is None else str(c) for c in col]))
        meta = {str(k): "" if v is None else str(v) for k, v in self.features.items()}
        meta['__metadata__'] = str(self.metadata).encode()
        schema_with_meta = pyarrow.schema(pyarrow.Table.from_arrays(cols, names=headers).schema, metadata=meta)
        return pyarrow.Table.from_arrays(cols, schema=schema_with_meta)
    
    def close(self):
        self.__wb.close()
    
    def write(self, data=None, features=None, metadata=None, missing="?"):
        """ Write data and/or features and/or metadata to the workbook.
        
        :param data:     matrix of data (including headers) OR path to data.csv OR path to Dataset folder
        :param features: dictionary of features' names and descriptions OR path to features.json
        :param metadata: dictionary of dataset's metadata OR path to metadata.json
        """
        self.__check_writable()
        # get the cell coordinate from (X,Y) coordinates (e.g. (1,2) => "B1")
        coord = lambda x, y: ws.cell(x+1, y+1).coordinate
        # private function to auto-adjust column widths
        def autoadjust(ws):
            col_widths = []
            for row in ws.rows:
                if len(col_widths) == 0:
                    col_widths = len(row) * [0]
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell.value)))
            for i, w in enumerate(col_widths):
                ws.column_dimensions[get_column_letter(i+1)].width = w
        # if the first argument is a folder, assume it is a specific folder structure as follows:
        #   [name]
        #     +-- data.csv            # metadata and labels of the executable
        #     +-- features.json       # dictionary of selected features and their descriptions
        #     +-- metadata.json       # simple statistics about the dataset
        if data is not None and not isinstance(data, (list, dict)) and isdir(expanduser(data)):
            self.__path, d = self.__path or basename(data), expanduser(data)
            data, features, metadata = join(d, "data.csv"), join(d, "features.json"), join(d, "metadata.json")
        # handle data first
        if data is not None:
            self.__logger.debug("writing data to DSFF...")
            ws, d = self.__wb['data'], data
            if not isinstance(d, (list, tuple)):
                if isfile(expanduser(d)) and splitext(d)[1] == ".csv":
                    with open(expanduser(d), newline='') as f:
                        d = [r for r in csvmod.reader(f, delimiter=CSV_DELIMITER)]
                else:
                    raise BadInputData("'data' is not a list")
            # clear the worksheet so that no cell of previous data remains
            ws.delete_rows(1, ws.max_row)
            for r, row in enumerate(d):
                for c, value in enumerate(row):
                    c = coord(r, c)
                    ws[c] = _to_cell(value, missing)
                    if r == 0:
                        ws[c].alignment = Alignment(horizontal="center")
                        ws[c].font = Font(bold=True)
            autoadjust(ws)
            self.__change = True
        # then handle features dictionary
        if len(features or {}) > 0:
            self.__logger.debug("writing features to DSFF...")
            ws, headers, d = self.__wb['features'], ["name", "description"], features
            if not isinstance(d, dict):
                if isfile(expanduser(d)) and basename(d) == "features.json":
                    with open(expanduser(d)) as f:
                        d = json.load(f)
                else:
                    raise BadInputData("'features' is not a dictionary")
            ws.delete_rows(1, ws.max_row)
            try:
                for c, header in enumerate(headers):
                    c = coord(0, c)
                    ws[c] = header
                    ws[c].alignment = Alignment(horizontal="center")
                    ws[c].font = Font(bold=True)
                for r, pair in enumerate(d.items()):
                    ws[coord(r+1, 0)] = pair[0]
                    ws[coord(r+1, 1)] = pair[1]
                autoadjust(ws)
                self.__change = True
            except Exception as e:
                raise BadInputData(f"Unexpected error while parsing 'features' ({e})")
        # finally handle metadata dictionary
        if len(metadata or {}) > 0:
            self.__logger.debug("writing metadata to DSFF...")
            d = metadata
            if not isinstance(d, dict):
                if isfile(expanduser(d)) and basename(d) == "metadata.json":
                    with open(expanduser(d)) as f:
                        d = json.load(f)
                else:
                    raise BadInputData("'metadata' is not a dictionary")
            try:
                self.__wb.properties.description = json.dumps(d)
                self.__change = True
            except Exception as e:
                raise BadInputData(f"Unexpected error while parsing 'metadata' ({e})")
        self.__save()
    
    @property
    def data(self):
        return [[self.__eval(c.value) for c in cells] for cells in self.__wb['data'].rows]
    
    @property
    def features(self):
        return {cells[0].value: cells[1].value for i, cells in enumerate(self.__wb['features'].rows) if i > 0}
    
    @property
    def headers(self):
        return list(self.features.keys())
    
    @property
    def logger(self):
        return self.__logger
    
    @property
    def metadata(self):
        d = self.__wb.properties.description
        if not d:
            return {}
        try:
            return json.loads(d)
        except ValueError:
            pass
        # older versions saved the representation of a Python dictionary
        try:
            return literal_eval(d)
        except (SyntaxError, ValueError):
            raise BadDsffFile("Metadata could not be parsed")
    
    @property
    def mode(self):
        return self.__mode
    
    @property
    def name(self):
        return self.__name or self.__wb.properties.title or splitext(basename(self.path))[0]
    
    @name.setter
    def name(self, name):
        self.__name = name
    
    @property
    def path(self):
        p = self.__path or "undefined"
        if p != INMEMORY and not p.endswith(".dsff"):
            p += ".dsff"
        return p
    
    @staticmethod
    @text_or_path(folders=True)
    def format(text):
        for k, func in globals().items():
            if k.startswith("is_") and func(text):
                return k.split("_", 1)[1]
    
    @staticmethod
    @text_or_path(folders=True)
    def is_valid_format(text):
        return DSFF.format(text) is not None

