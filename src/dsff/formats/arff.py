# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_arff", "is_arff", "to_arff"]


def _parse(text_or_fh, target=TARGET_NAME, missing=MISSING_TOKEN):
    d, features, metadata, title = [], {}, {}, ""
    relation, attributes, data = False, [False, False], False
    for n, l in enumerate(t.splitlines() if isinstance(t := text_or_fh, str) else t):
        l, pf = l.strip(), f"Line {n}: "
        # the file shall start with "@RELATION"
        if not relation:
            if l.startswith("@RELATION "):
                relation = True
                try:
                    title = re.match(r"@RELATION\s+('[^']*'|\"[^\"]*\")$", l).group(1).strip("'\"")
                    continue
                except Exception as e:
                    raise BadInputData(f"{pf}failed on @RELATION ({e})")
            else:
                raise BadInputData(f"{pf}did not find @RELATION")
        # get metadata and feature descriptions from comments
        if l.startswith("%"):
            if re.match(r"^\%\s+metadata\s*\:\s*\{.*\}$", l):
                metadata = literal_eval(l.split(":", 1)[1])
            elif (m := re.match(r"^\%\s+(.*?)\s*\:\s*(.*?)$", l)):
                name, descr = m.groups()
                features[name] = descr
            continue
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
                raise BadInputData(f"{pf}found @ATTRIBUTE out of the attributes block)")
            try:
                header = re.match(r"@ATTRIBUTE\s+([^\s]+)\s+[A-Z]+$", l).group(1)
                if header == "class":
                    header = target
                d[0].append(header)
                continue
            except AttributeError:
                raise BadInputData(f"{pf}failed on @ATTRIBUTE (bad type)")
        if not data:
            if l == "@DATA":
                data = True
                continue
            else:
                raise BadInputData(f"{pf}did not find @DATA where expected")
        row = list(map(lambda x: x.strip("'\""), re.split(r",\s+", l)))
        if len(row) != n_cols:
            raise BadInputData(f"{pf}this row does not match the number of columns")
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
    return d, features, metadata, title


def from_arff(dsff, path=None, target=TARGET_NAME, missing=MISSING_TOKEN):
    """ Populate the DSFF file from an ARFF file. """
    with open(path) as f:
        d, ft, md, t = _parse(f, target, missing)
    dsff['title'] = t
    dsff.write(data=d, features=ft, metadata=md)


@text_or_path
def is_arff(text):
    """ Check if the input text or path is a valid ARFF. """
    try:
        _parse(ensure_str(text))
        return True
    except (BadInputData, UnicodeDecodeError):
        return False


def to_arff(dsff, path=None, target=TARGET_NAME, exclude=DEFAULT_EXCL, missing=MISSING_TOKEN, text=False):
    """ Output the dataset in ARFF format, suitable for use with the Weka framework, saved as a file or output as a
         string. """
    name = splitext(basename(path))[0]
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
        if i == 0:
            continue  # do not process headers
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
    d = (nl := "\n").join(" ".join(("{: <%s}" % (mlen_c[k]+1)).format((x if types[k] == "NUMERIC" or \
                       x == MISSING_TOKEN else "'%s'" % x) + ",") for k, x in enumerate(row)).rstrip(" ,") for row in d)
    arff = f"@RELATION \"{name}\"\n\n{nl.join(a)}\n\n@DATA\n{d}\n\n" \
           f"{['', f'% metadata: {json.dumps(dsff.metadata)}'][len(dsff.metadata) > 0]}\n\n" \
           f"{nl.join(f'% {name}: {descr}' for name, descr in dsff.features.items())}"
    if text:
        return arff
    with open(path, 'w+') as f:
        f.write(arff)

