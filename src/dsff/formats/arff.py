# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_arff", "is_arff", "load_arff", "to_arff"]

_NAME = r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|[^\s'\"%{},]+)"
_TYPE = r"(?:numeric|real|integer|string|relational|date(?:\s+.+)?|\{.*\})"


def _quote(value):
    """ Quote a string value, escaping backslashes and single quotes. """
    return "'{}'".format(str(value).replace("\\", "\\\\").replace("'", "\\'"))


def _split(line):
    """ Split a data line on commas, honoring quoted values (with backslash escapes). """
    values, current, quote, quoted, i = [], "", None, False, 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\" and i + 1 < len(line):
                current += line[i+1]
                i += 1
            elif c == quote:
                quote = None
            else:
                current += c
        elif c == ",":
            values.append(current if quoted else current.strip())
            current, quoted = "", False
        elif c in "'\"" and current.strip() == "" and not quoted:
            current, quote, quoted = "", c, True
        elif not quoted:
            current += c
        elif not c.isspace():
            raise BadInputData("unexpected character after a quoted value")
        i += 1
    if quote:
        raise BadInputData("unterminated quoted value")
    values.append(current if quoted else current.strip())
    return values


def _unquote(name):
    if len(name) >= 2 and name[0] == name[-1] and name[0] in "'\"":
        name = re.sub(r"\\(.)", r"\1", name[1:-1])
    return name


def _parse(text_or_fh, target=TARGET_NAME, missing=MISSING_TOKEN, **kw):
    d, comments, metadata, title, n_cols = [[]], {}, {}, "", None
    relation = False
    for n, l in enumerate(t.splitlines() if isinstance(t := text_or_fh, str) else t, 1):
        l, pf = l.strip(), f"Line {n}: "
        # ignore blank lines ; get metadata and feature descriptions from comments
        if l == "":
            continue
        if l.startswith("%"):
            if (m := re.match(r"^\%\s*metadata\s*\:\s*(\{.*\})$", l)):
                try:
                    metadata = json.loads(m.group(1))
                except ValueError:
                    try:
                        metadata = literal_eval(m.group(1))
                    except (SyntaxError, ValueError) as e:
                        raise BadInputData(f"{pf}failed on metadata ({e})")
            elif (m := re.match(r"^\%\s*(.*?)\s*\:\s*(.*?)$", l)):
                comments[m.group(1)] = m.group(2)
            continue
        # the file shall start with "@RELATION"
        if not relation:
            if (m := re.match(rf"@RELATION\s+{_NAME}$", l, re.I)) is None:
                raise BadInputData(f"{pf}did not find a valid @RELATION")
            relation, title = True, _unquote(m.group(1))
            continue
        if l.upper().startswith("@ATTRIBUTE"):
            if n_cols is not None:
                raise BadInputData(f"{pf}found @ATTRIBUTE out of the attributes block")
            if (m := re.match(rf"@ATTRIBUTE\s+{_NAME}\s+{_TYPE}$", l, re.I)) is None:
                raise BadInputData(f"{pf}failed on @ATTRIBUTE (bad name or type)")
            header = _unquote(m.group(1))
            d[0].append(target if header == "class" else header)
            continue
        if n_cols is None:
            if l.upper() != "@DATA" or len(d[0]) == 0:
                raise BadInputData(f"{pf}did not find @DATA where expected")
            n_cols = len(d[0])
            continue
        if len(row := _split(l)) != n_cols:
            raise BadInputData(f"{pf}this row does not match the number of columns")
        d.append(row)
    if n_cols is None:
        raise BadInputData("did not find @DATA")
    for i in range(n_cols):
        values = set()
        for row in d[1:]:
            values.add(row[i])
            if row[i] in ["-", missing]:
                row[i] = {'-': "", missing: None}[row[i]]
        if len(values) > 0 and values <= {"0", "1"}:
            for row in d[1:]:
                row[i] = {'0': "False", '1': "True"}[row[i]]
    # feature descriptions are the comments whose names are attributes
    features = {h: comments.get(h, "") for h in d[0] if h != target}
    return d, features, metadata, title


def from_arff(dsff, path=None, target=TARGET_NAME, missing=MISSING_TOKEN, **kw):
    """ Populate the DSFF file from an ARFF file. """
    with open(path) as f:
        d, ft, md, t = _parse(f, target, missing)
    dsff['title'] = t
    dsff.write(data=d, features=ft, metadata=md)


@text_or_path
def is_arff(text, target=TARGET_NAME, missing=MISSING_TOKEN, **kw):
    """ Check if the input text or path is a valid ARFF. """
    try:
        _parse(ensure_str(text), target, missing)
        return True
    except (BadInputData, UnicodeDecodeError):
        return False


def load_arff(path, target=TARGET_NAME, missing=MISSING_TOKEN, **kw):
    """ Load an ARFF file as a dictionary with data, features and metadata. """
    with open(path) as f:
        d, ft, md, _ = _parse(f, target, missing)
    return {'data': d, 'features': ft, 'metadata': md}


def to_arff(dsff, path=None, target=TARGET_NAME, exclude=DEFAULT_EXCL, missing=MISSING_TOKEN, text=False, **kw):
    """ Output the dataset in ARFF format, suitable for use with the Weka framework, saved as a file or output as a
         string. """
    name = splitext(basename(path))[0]
    _missing = lambda v: v is None or v == missing
    _numeric = lambda v: isinstance(v, (bool, int, float))
    def _name(h):
        h = str(h).replace("<", "[lt]").replace(">", "[gt]")
        return h if re.match(r"[^\s'\"%{},]+$", h) else _quote(h)
    data = dsff.data
    headers, rows = [str(h) for h in data[0]], data[1:]
    # select the relevant columns, the target (if any) being the last one
    cols = [i for i, h in enumerate(headers) if h not in exclude and h != target]
    i_target = headers.index(target) if target in headers else -1
    if i_target > -1:
        cols.append(i_target)
    # compute the data type of each column from all of its values
    attributes, types = [], []
    dsff.logger.debug("> computing features and types...")
    for i in cols:
        values = [r[i] for r in rows if not _missing(r[i])]
        if i == i_target and len(values) > 0:
            labels = sorted(set(str(int(v) if isinstance(v, bool) else v) for v in values))
            t = "{%s}" % ",".join(map(_quote, labels))
        else:
            t = "NUMERIC" if all(_numeric(v) for v in values) else "STRING"
        attributes.append(("class" if i == i_target else _name(headers[i]), t))
        types.append(t)
    # format the data according to the ARFF format
    dsff.logger.debug("> computing data...")
    d = []
    for r in rows:
        row = []
        for i, t in zip(cols, types):
            v = r[i]
            if _missing(v):
                v = missing
            elif isinstance(v, bool):
                v = str(int(v)) if t == "NUMERIC" else _quote(int(v))
            elif t == "NUMERIC":
                v = str(v)
            else:
                v = _quote("-" if v == "" else v)
            row.append(v)
        d.append(row)
    # align the columns for readability
    widths = [max([len(row[k]) for row in d] + [0]) + 1 for k in range(len(cols))]
    d = (nl := "\n").join(" ".join(f"{v},".ljust(widths[k] + 1) for k, v in enumerate(row)).rstrip(" ,") for row in d)
    mlen = max([len(a) for a, _ in attributes] + [0])
    a = nl.join(f"@ATTRIBUTE {a.ljust(mlen)} {t}" for a, t in attributes)
    descr = lambda v: "" if v is None else str(v).replace("\n", " ")
    arff = f"@RELATION {_quote(name)}\n\n{a}\n\n@DATA\n{d}\n\n" \
           f"{['', f'% metadata: {json.dumps(dsff.metadata, default=str)}'][len(dsff.metadata) > 0]}\n\n" \
           f"{nl.join(f'% {n}: {descr(v)}' for n, v in dsff.features.items())}"
    if text:
        return arff
    with open(path, 'w+') as f:
        f.write(arff)
