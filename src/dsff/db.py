# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_db", "to_db"]


def from_db(dsff, path=None, exclude=DEFAULT_EXCL):
    """ Populate the DSFF file from a SQLDB file. """
    from json import loads
    from sqlite3 import connect
    path = fix_path(dsff, path, ".db")
    dsff.logger.debug(f"creating DSFF from {path}...")
    conn = connect(path)
    cursor = conn.cursor()
    # list tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    if not all(t in tables for t in ["data", "features", "metadata"]):
        raise BadInputData("The target SQLDB does not have the right format")
    # import data
    cursor.execute("PRAGMA table_info('data')")
    headers = [[col[1] for col in cursor.fetchall()]]
    cursor.execute("SELECT * FROM data;")
    dsff.write(headers + [r for r in cursor.fetchall()])
    # import feature definitions
    cursor.execute("SELECT name,description FROM features;")
    dsff.write(features={r[0]: r[1] for r in cursor.fetchall()})
    # import metadata
    cursor.execute("SELECT key,value FROM metadata;")
    dsff.write(metadata={r[0]: loads(r[1]) if isinstance(r[1], str) else r[1] for r in cursor.fetchall()})
    conn.close()


def to_db(dsff, path=None, text=False, primary_index=0):
    """ Create a SQLDB from the data worksheet, saved as a file or output as a string. """
    from json import dumps
    from sqlite3 import connect
    path = fix_path(dsff, path, ".db", True)
    dsff.logger.debug(f"extracting data from DSFF to {[path,'SQL'][text]}...")
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

