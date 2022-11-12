# -*- coding: UTF-8 -*-
import builtins
import csv
import json
import logging
import openpyxl.reader.excel as excelr
from ast import literal_eval
from datetime import datetime
from getpass import getuser
from io import StringIO
from openpyxl import load_workbook, Workbook
from openpyxl.packaging.custom import CustomDocumentProperty
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from os import makedirs
from os.path import basename, expanduser, isfile, isdir, join, splitext
from zipfile import ZipFile


__all__ = ["DSFF"]

CSV_DELIMITER = ";"
DEF_ARFF_EXCL = ("hash", "realpath", "format", "size", "ctime", "mtime")  # origin: executables used in the Packing Box
META_EXCL     = ["created", "modified", "revision"]


for name, etype in [("BadDsffFile", "OSError"), ("BadInputData", "ValueError")]:
    if not hasattr(builtins, name):
        exec("class %s(%s): __module__ = 'builtins'" % (name, etype))
        setattr(builtins, name, locals()[name])


class DSFF:
    """ DataSet File Format. """
    def __init__(self, path=None, logger=None):
        self.__change = False
        self.__logger = logger or logging.getLogger("DSFF")
        self.__path = path
        if self.__path is not None and not self.__path.endswith(".dsff"):
            self.__path += ".dsff"
        # if the target path exists and is a file, open it
        if path is not None and isfile(path):
            # disable archive validation as it does not recognize '.dsff'
            tmp = excelr._validate_archive
            excelr._validate_archive = lambda f: ZipFile(f, 'r')
            self.__wb = load_workbook(path)
            excelr._validate_archive = tmp
            self.__check()
        # otherwise, create a new workbook with the default worksheets
        else:
            self.__wb = Workbook()
            del self.__wb['Sheet']  # remove the default sheet
            for ws in ["data", "features"]:
                self.__wb.create_sheet(ws)
    
    def __enter__(self):
        return self
    
    def __exit__(self):
        self.save()
        self.close()
    
    def __getitem__(self, name):
        if name in ["data", "features"]:
            return self.__wb[name]
        try:
            return getattr(self.__wb.properties, name)
        except AttributeError:
            pass
        return self.metadata[name]
    
    def __setitem__(self, name, value):
        if name in ["data", "features"]:
            raise ValueError("'%s' is a name reserved for a worksheet" % name)
        if hasattr(self.__wb.properties, name):
            setattr(self.__wb.properties, name, value)
        d = self.metadata
        d[name] = value
        self.__wb.properties.description = json.dumps(d)
        self.__change = True
    
    def __check(self):
        # check that the file has only 2 worksheets: 'data' and 'features'
        if [ws._WorkbookChild__title for ws in self.__wb.worksheets] != ["data", "features"]:
            raise BadDsffFile("The input file is not a DSFF file")
        # check that the 'features' worksheet has 2 columns: 'name' and 'description'
        for headers in self.__wb['features'].rows:
            if len(headers) != 2 or headers[0].value != "name" or headers[1].value != "description":
                raise BadDsffFile("The features worksheet does not comply with DSFF")
            break
    
    def __eval(self, v):
        try:
            return literal_eval(v)
        except (SyntaxError, ValueError):
            return v
    
    def close(self):
        self.__wb.close()
    
    def save(self):
        if self.__change:
            if self.__path is None:
                raise ValueError("No destination path defined")
            props = self.__wb.properties
            if props.creator is None or props.creator == "openpyxl":
                props.creator = getuser()
            props.title = self.name
            props.description = self.metadata
            self.__wb.save(self.__path)
            self.__change = False
    
    def to_arff(self, path=None, target="label", exclude=DEF_ARFF_EXCL, missing="?", text=False):
        """ Output the dataset in ARFF format, suitable for use with the Weka framework. """
        path = path or self.name
        if not path.endswith(".arff"):
            path += ".arff"
        name = splitext(basename(path))[0]
        self.__logger.debug("converting DSFF to ARFF...")
        _d = lambda c: {None: missing, '': "-", 'False': "0", 'True': "1"}.get(c.value, c.value)
        _sanitize_n = lambda c: _d(c).replace("<", "[lt]").replace(">", "[gt]")
        _sanitize_v = lambda c: _d(c)[1:].strip("\"'") if _d(c).startswith("=") else _d(c)
        data = self.__wb['data']
        # compute the list of features and their data types
        self.__logger.debug("> computing features and types...")
        d, mlen_h, i_target, h_excl = [], 0, -1, []
        # collect headers and compute the indices list for non-data columns
        for headers in data.rows:
            for i, header in enumerate(headers):
                header = _sanitize_n(header)
                if header in exclude:
                    h_excl.append(i)
                    continue
                if header == target:
                    i_target = i
                    continue
                mlen_h = max(mlen_h, len(header))
            break
        # filter headers on the relevant data
        headers = [h for k, h in enumerate(headers) if k != i_target and k not in h_excl] + \
                  [headers[i_target] if i_target > -1 else []]
        # format the data according to the ARFF format
        self.__logger.debug("> computing data...")
        types = []
        # parse labels, data types and relevant data
        for i, row in enumerate(data.rows):
            if i > 0:
                if len(types) == 0:
                    labels = ["0", "1"] if i_target == -1 else \
                             list(set(_sanitize_v(row[i_target]) for k, row in enumerate(data) if k > 0))
                    labels = [x for x in labels if x != missing]
                    # compute types
                    for j, cell in enumerate(row):
                        v = _sanitize_v(cell)
                        try:
                            float(v)
                            t = "NUMERIC"
                        except ValueError:
                            t = "STRING"
                        types.append(t)
                    # filter data types based on the relevant columns
                    types = [t for k, t in enumerate(types) if k != i_target and k not in h_excl] + \
                            [types[i_target] if i_target > -1 else []]
                    # compute the list of ARFF attribute lines based on the column names and data types
                    a = [("@ATTRIBUTE {: <%s} {}" % mlen_h).format("class" if j == len(types)-1 else \
                          _sanitize_n(headers[j]), t) for j, t in enumerate(types)]
                    mlen_c = [0] * len(types)
                # filter data based on the relevant columns
                row = [_sanitize_v(x) for k, x in enumerate(row) if k != i_target and k not in h_excl] + \
                      ([_sanitize_v(row[i_target])] if i_target > -1 else [])
                # compute the maximum length for each column
                mlen_c = [max(x, len(row[k]) if types[k] == "NUMERIC" else len(row[k])+2) for k, x in enumerate(mlen_c)]
                d.append(row)
        # format the resulting data and output the ARFF
        d = "\n".join(" ".join(("{: <%s}" % (mlen_c[k]+1)).format((x if types[k] == "NUMERIC" else "'%s'" % x) + ",") \
                               for k, x in enumerate(row)).rstrip(" ,") for row in d)
        arff = "@RELATION \"{}\"\n\n{}\n\n@DATA\n{}".format(name, "\n".join(a), d)
        if text:
            return arff
        with open(path, 'w+') as f:
            f.write(arff)
    
    def to_csv(self, path=None, text=False):
        """ Create a CSV from the data worksheet. """
        path = path or self.name
        if not path.endswith(".csv"):
            path += ".csv"
        with (StringIO() if text else open(expanduser(path), 'w+')) as f:
            writer = csv.writer(f, delimiter=CSV_DELIMITER)
            for cells in self.__wb['data'].rows:
                writer.writerow([self.__eval(c.value) for c in cells])
            if text:
                return f.getvalue()
    
    def to_dataset(self, path=None):
        """ Create a dataset folder according to the Dataset structure ;
        name
         +-- data.csv
         +-- features.json
         +-- metadata.json
        """
        path = path or self.name
        makedirs(path, exist_ok=True)
        self.__logger.debug("converting DSFF to Dataset folder...")
        # handle data first
        self.__logger.debug("> making data.csv...")
        with open(join(path, "data.csv"), 'w+') as f:
            writer = csv.writer(f, delimiter=CSV_DELIMITER)
            for cells in self.__wb['data'].rows:
                writer.writerow([self.__eval(c.value) for c in cells])
        # then handle features dictionary
        self.__logger.debug("> making features.json...")
        with open(join(path, "features.json"), 'w+') as f:
            json.dump(self.features, f, indent=2)
        # finally handle metadata dictionary
        self.__logger.debug("> making metadata.json...")
        with open(join(path, "metadata.json"), 'w+') as f:
            json.dump(self.metadata, f, indent=2)
    
    def write(self, data=None, features=None, metadata=None):
        """ Write data and/or features and/or metadata to the workbook.
        
        :param data:     matrix of data (including headers) OR path to data.csv OR path to Dataset folder
        :param features: dictionary of features' names and descriptions OR path to features.json
        :param metadata: dictionary of dataset's metadata OR path to metadata.json
        """
        # get the cell coordinate from (X,Y) coordinates (e.g. (1,2) => "B1")
        coord = lambda x, y: ws.cell(x+1, y+1).coordinate
        # private function to auto-adjust column widths
        def autoadjust(ws):
            col_widths = []
            for row in ws.rows:
                if len(col_widths) == 0:
                    col_widths = len(row) * [0]
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell.value))
            for i, w in enumerate(col_widths):
                ws.column_dimensions[get_column_letter(i+1)].width = w
        # if the first argument is a folder, assume it is a Dataset structure compliant with:
        #   name
        #    +-- data.csv
        #    +-- features.json
        #    +-- metadata.json
        if data is not None and not isinstance(data, (list, dict)) and isdir(expanduser(data)):
            self.__path, d = self.__path or "%s.dsff" % basename(data), expanduser(data)
            data, features, metadata = join(d, "data.csv"), join(d, "features.json"), join(d, "metadata.json")
        # handle data first
        if data is not None:
            self.__logger.debug("writing data to DSFF...")
            ws, d = self.__wb['data'], data
            if not isinstance(d, list) and isfile(expanduser(d)) and basename(d) == "data.csv":
                with open(expanduser(d)) as f:
                    d = []
                    for row in csv.reader(f, delimiter=CSV_DELIMITER):
                        d.append(row)
            try:
                for r, row in enumerate(d):
                    for c, value in enumerate(row):
                        c = coord(r, c)
                        ws[c] = value
                        if r == 0:
                            ws[c].alignment = Alignment(horizontal="center")
                            ws[c].font = Font(bold=True)
                autoadjust(ws)
                self.__change = True
            except Exception as e:
                raise BadInputData(str(e))
        # then handle features dictionary
        if features is not None:
            self.__logger.debug("writing features to DSFF...")
            ws, headers, d = self.__wb['features'], ["name", "description"], features
            if not isinstance(d, dict) and isfile(expanduser(d)) and basename(d) == "features.json":
                with open(expanduser(d)) as f:
                    d = json.load(f)
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
        # finally handle metadata dictionary
        if metadata is not None:
            self.__logger.debug("writing metadata to DSFF...")
            d = metadata
            if not isinstance(d, dict) and isfile(expanduser(d)) and basename(d) == "metadata.json":
                with open(expanduser(d)) as f:
                    d = json.load(f)
            self.__wb.properties.description = json.dumps(d)
        self.save()
    
    @property
    def data(self):
        return [[self.__eval(c.value) for c in cells] for cells in self.__wb['data'].rows]
    
    @property
    def features(self):
        return {cells[0].value: cells[1].value for i, cells in enumerate(self.__wb['features'].rows) if i > 0}
    
    @property
    def metadata(self):
        return json.loads(self.__wb.properties.description or "{}")
    
    @property
    def name(self):
        return self.__wb.properties.title or \
               (splitext(basename(self.__path))[0] if self.__path is not None else "undefined")

