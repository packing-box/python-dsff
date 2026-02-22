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
    from json import loads
    from os.path import basename, splitext
    from sqlite3 import connect
    conn = connect(path)
    cursor, data = conn.cursor(), {}
    # list tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    if not all(t in tables for t in ["data", "features", "metadata"]):  # pragma: no cover
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
    data['metadata'] = {r[0]: loads(r[1]) if isinstance(r[1], str) else r[1] for r in cursor.fetchall()}
    conn.close()
    return data


def to_db(dsff, path=None, text=False, primary_index=0, **kw):
    """ Create a SQLDB from the data worksheet, saved as a file or output as a string. """
    from json import dumps
    from sqlite3 import connect
    fields = []
    rows = (data := dsff['data']).rows
    headers, first = [c.value for c in next(rows)], next(rows)
    for i, pair in enumerate(zip(headers, first)):
        header, cell = pair
        try:
            dtype = {int: "INTEGER", float: "REAL", bool: "INTEGER"}[type(dsff._DSFF__eval(cell.value))]
        except (KeyError, ValueError):
            dtype = "TEXT"
        fields.append(f"{header} {dtype}{['',' PRIMARY KEY'][i==primary_index]}")
    # create the database
    conn = connect(":memory:" if text else path)
    cursor = conn.cursor()
    # create and populate the data table
    cursor.execute("CREATE TABLE IF NOT EXISTS data ({fields});" \
                   .format(fields="\n    ".join(f"{f}," for f in fields).rstrip(",")))
    cursor.executemany("INSERT INTO data ({fields}) VALUES ({tokens});"\
                       .format(fields=",".join(headers), tokens=",".join(["?"]*len(headers))),
                       [[v.value for v in row] for i, row in enumerate(data.rows) if i > 0])
    # create and populate the features table
    cursor.execute("CREATE TABLE IF NOT EXISTS features (name TEXT PRIMARY KEY, description TEXT);")
    cursor.executemany("INSERT INTO features (name, description) VALUES (?, ?);",
                       [(r[0].value, r[1].value) for i, r in enumerate(dsff['features'].rows) if i > 0])
    # create and populate the metadata table
    cursor.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value JSON);")
    cursor.executemany("INSERT INTO metadata (key, value) VALUES (?, ?);",
                       [(k, dumps(v)) for k, v in dsff.metadata.items()])
    conn.commit()
    if text:
        sql = {}
        # extract SQL code
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table';")
        sql['table'] = "\n".join(row[0] for row in cursor.fetchall())
        for t in ["data", "features", "metadata"]:
            cursor.execute(f"SELECT * FROM {t};")
            sql[t] = "\n".join(f"INSERT INTO {t} VALUES ('{row[0]}', '{row[1]}');" for row in cursor.fetchall())
        # combine all SQL
        return "\n".join(sql.values())
    conn.close()

