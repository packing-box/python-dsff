# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_arff", "to_arff"]


def from_arff(dsff, path=None, target=TARGET_NAME, missing=MISSING_TOKEN):
    """ Populate the DSFF file from an ARFF file. """
    path = expanduser(path or dsff.name)
    if not path.endswith(".arff"):
        path += ".arff"
    dsff.logger.debug("creating DSFF from ARFF file...")
    d = []
    with open(path) as f:
        relation, attributes, data = False, [False, False], False
        for n, l in enumerate(f, 1):
            l = l.strip()
            # ignore comments before @RELATION
            if l.startswith("#"):
                continue
            if not relation:
                if l.startswith("@RELATION "):
                    relation = True
                    try:
                        dsff['title'] = re.match(r"@RELATION\s+('[^']*'|\"[^\"]*\")$", l).group(1).strip("'\"")
                        continue
                    except Exception as e:
                        raise BadInputData("Line %d: failed on @RELATION (%s)" % (n, e))
                else:
                    raise BadInputData("Line %d: did not find @RELATION" % n)
            # then ignore blank lines
            if l == "":
                if attributes[0] and not attributes[1]:
                    # close the atributes block
                    attributes[1] = True
                    n_cols = len(d[0])
                continue
            if l.startswith("@ATTRIBUTE "):
                if not attributes[0]:
                    attributes[0] = True
                if len(d) == 0:
                    # start the attributes block
                    d.append([])
                if attributes[1]:
                    raise BadInputData("Line %d: found @ATTRIBUTE out of the attributes block)" % n)
                try:
                    header = re.match(r"@ATTRIBUTE\s+([^\s]+)\s+[A-Z]+$", l).group(1)
                    if header == "class":
                        header = target
                    d[0].append(header)
                except AttributeError:
                    raise BadInputData("Line %d: failed on @ATTRIBUTE (bad type)" % n)
                finally:
                    continue
            if not data:
                if l == "@DATA":
                    data = True
                    continue
                else:
                    raise BadInputData("Line %d: did not find @DATA where expected" % n)
            row = list(map(lambda x: x.strip("'\""), re.split(r",\s+", l)))
            if len(row) != n_cols:
                raise BadInputData("Line %d: this row does not match the number of columns" % n)
            d.append(row)
    for i in range(n_cols):
        values = []
        for j, row in enumerate(d):
            if j == 0:
                continue
            if row[i] not in values:
                values.append(row[i])
            if row[i] in ["-", missing]:
                row[i] = {'-': "", missing: None}[row[i]]
        if "".join(sorted(set(values))) in ["0", "1", "01"]:
            for j, row in enumerate(d):
                if j > 0:
                    row[i] = {'0': "False", '1': "True"}[row[i]]
    dsff.write(d)
    features = {}
    for headers in dsff['data'].rows:
        for header in headers:
            features[header.value] = ""
        break
    dsff.write(features=features)


def to_arff(dsff, path=None, target=TARGET_NAME, exclude=DEFAULT_EXCL, missing=MISSING_TOKEN, text=False):
    """ Output the dataset in ARFF format, suitable for use with the Weka framework, saved as a file or output as a
         string. """
    path = splitext(expanduser(path or dsff.name))[0]
    if not path.endswith(".arff"):
        path += ".arff"
    name = splitext(basename(path))[0]
    dsff.logger.debug("extracting data from DSFF to ARFF file...")
    _d = lambda c: {None: missing, '': "-", 'False': "0", 'True': "1"}.get(c.value, c.value)
    _sanitize_n = lambda c: _d(c).replace("<", "[lt]").replace(">", "[gt]")
    _sanitize_v = lambda c: _d(c)[1:].strip("\"'") if _d(c).startswith("=") else _d(c)
    data = dsff['data']
    # compute the list of features and their data types
    dsff.logger.debug("> computing features and types...")
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
    dsff.logger.debug("> computing data...")
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
    d = "\n".join(" ".join(("{: <%s}" % (mlen_c[k]+1)).format((x if types[k] == "NUMERIC" or x == MISSING_TOKEN else \
                            "'%s'" % x) + ",") for k, x in enumerate(row)).rstrip(" ,") for row in d)
    arff = "@RELATION \"{}\"\n\n{}\n\n@DATA\n{}".format(name, "\n".join(a), d)
    if text:
        return arff
    with open(path, 'w+') as f:
        f.write(arff)

