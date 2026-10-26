# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_db", "is_db", "load_db", "to_db"]


def from_db(dsff, path=None, **kw):
    """ Populate the DSFF file from a SQLDB file. """
    dsff.write(**load_db(path))


@text_or_path
def is_db(data, **kw):
    """ Check if the input data or path is a valid SQL database. """
    from sqlite3 import connect, Error
    from sys import version_info
    if not data.startswith(b"SQLite format 3\x00"):
        return False
    if version_info.minor > 10:
        try:
            with connect(":memory:") as c:
                c.deserialize(data)
                c.execute("PRAGMA schema_version;")
            return True
        except Error:
            return False
    else:  # pragma: no cover
        from os import close, write
        from tempfile import mkstemp
        fd, path = mkstemp(suffix=".db")
        try:
            write(fd, data)
            close(fd)
            fd = None
            with connect(f"file:{path}?mode=ro&immutable=1", uri=True) as c:
                c.execute("PRAGMA schema_version;").fetchone()
            return True
        except (Error, OSError):
            return False


def load_db(path, **kw):
    """ Load a SQLDB file as a dictionary with data, features and metadata. """
    from contextlib import closing
    from sqlite3 import connect
    with closing(connect(path)) as conn:
        cursor, data = conn.cursor(), {}
        # list tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        if not all(t in tables for t in ["data", "features", "metadata"]):
            raise BadInputData("The target SQLDB does not have the right format")
        # import data
        cursor.execute("PRAGMA table_info('data')")
        headers = [[col[1] for col in cursor.fetchall()]]
        cursor.execute("SELECT * FROM data;")
        data['data'] = headers + [r for r in cursor.fetchall()]
        # import feature definitions
        cursor.execute("SELECT name,description FROM features;")
        data['features'] = {r[0]: r[1] for r in cursor.fetchall()}
        # import metadata
        cursor.execute("SELECT key,value FROM metadata;")
        data['metadata'] = {r[0]: json.loads(r[1]) if isinstance(r[1], str) else r[1] for r in cursor.fetchall()}
    return data


def to_db(dsff, path=None, text=False, primary_index=0, missing=MISSING_TOKEN, **kw):
    """ Create a SQLDB from the data worksheet, saved as a file or output as a string. """
    from sqlite3 import connect
    _q = lambda n: "\"{}\"".format(str(n).replace("\"", "\"\""))
    data = dsff.data
    headers, rows = data[0], [[None if v is None or v == missing else v for v in r] for r in data[1:]]
    fields = []
    for i, header in enumerate(headers):
        values = [r[i] for r in rows if r[i] is not None]
        if len(values) > 0 and all(isinstance(v, (bool, int)) for v in values):
            dtype = "INTEGER"
        elif len(values) > 0 and all(isinstance(v, (bool, int, float)) for v in values):
            dtype = "REAL"
        else:
            dtype = "TEXT"
        # only use the column as the primary key if its values are unique and not missing
        pk = i == primary_index and len(values) == len(rows) and len(set(values)) == len(values)
        fields.append(f"{_q(header)} {dtype}{['', ' PRIMARY KEY'][pk]}")
    # create the database (overwrite an existing one, as for the other formats)
    if not text and isfile(path):
        remove(path)
    conn = connect(":memory:" if text else path)
    try:
        cursor = conn.cursor()
        # create and populate the data table
        cursor.execute("CREATE TABLE data ({});".format(", ".join(fields)))
        cursor.executemany("INSERT INTO data ({}) VALUES ({});".format(",".join(map(_q, headers)),
                           ",".join(["?"] * len(headers))), rows)
        # create and populate the features table
        cursor.execute("CREATE TABLE features (name TEXT PRIMARY KEY, description TEXT);")
        cursor.executemany("INSERT INTO features (name, description) VALUES (?, ?);", dsff.features.items())
        # create and populate the metadata table
        cursor.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value JSON);")
        cursor.executemany("INSERT INTO metadata (key, value) VALUES (?, ?);",
                           [(k, json.dumps(v, default=str)) for k, v in dsff.metadata.items()])
        conn.commit()
        if text:
            return "\n".join(conn.iterdump())
    finally:
        conn.close()
