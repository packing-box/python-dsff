#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""DSFF regression tests.

"""
import sqlite3
import tempfile

from .utils import *


DATA = [["hash", "a", "b", "label"], ["x", 1, 2.5, "upx"], ["y", 3, None, "?"]]
FEATURES = {'a': "feature A", 'b': "feature B"}


class TestRegressions(TestCase):
    def setUp(self):
        self._cwd, self._tmp = os.getcwd(), tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_metadata_values(self):
        # booleans, None and apostrophes in metadata shall not make the file unreadable
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES, {'flag': True, 'none': None, 'note': "it's"})
        with DSFF("test.dsff", 'r+') as f:
            f['other'] = "isn't"
        self.assertEqual(DSFF("test.dsff").metadata, {'flag': True, 'none': None, 'note': "it's", 'other': "isn't"})

    def test_paths(self):
        # absolute paths shall be recognized by the is_* functions and DSFF.format
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES)
            f.to_arff()
            f.to_db()
        for fmt in ["arff", "db", "dsff"]:
            path = os.path.abspath(f"test.{fmt}")
            self.assertTrue(globals()[f'is_{fmt}'](path))
            self.assertEqual(DSFF.format(path), fmt)
        self.assertIsNone(DSFF.format(b"PK\x03\x04\x14\x00\x00\x00\x08\x00P\xb3T\\F\xc7MH"))
        # a dot in the name shall not be taken for an extension
        with DSFF("test-v1.2", 'w') as f:
            f.write(DATA, FEATURES)
            f.to_csv()
        self.assertTrue(os.path.isfile("test-v1.2.csv"))
        # an input file with another extension shall be used as is
        with open("test.txt", 'w') as f:
            f.write("a;b\n1;2\n")
        with DSFF("test2", 'w') as f:
            f.from_csv("test.txt")
            self.assertEqual(f.data, [["a", "b"], [1, 2]])

    def test_rewrite(self):
        # rewriting smaller data or features shall not leave cells of the previous ones
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES)
        with DSFF("test.dsff", 'r+') as f:
            f.write([["a"], [9]], {'a': "feature A"})
        f = DSFF("test.dsff")
        self.assertEqual(f.data, [["a"], [9]])
        self.assertEqual(f.features, {'a': "feature A"})

    def test_read_only(self):
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES)
        with DSFF("test.dsff") as f:
            self.assertRaises(ValueError, f.write, [["z"], [0]])
            self.assertRaises(ValueError, f.__setitem__, "key", "value")
            self.assertRaises(ValueError, f.from_csv, "test.csv")

    def test_types(self):
        # only scalar literals are evaluated
        with DSFF("test", 'w') as f:
            f.write([["name", "label"], ["[1]", "1.5"], ["(1, 2)", "x"]])
            self.assertEqual(f.data, [["name", "label"], ["[1]", 1.5], ["(1, 2)", "x"]])

    def test_exception_in_context(self):
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES)
        try:
            with DSFF("test.dsff", 'r+') as f:
                f['key'] = "value"
                raise RuntimeError
        except RuntimeError:
            pass
        self.assertNotIn("key", DSFF("test.dsff").metadata)

    def test_undefined_not_removed(self):
        with open("undefined.dsff", 'w') as f:
            f.write("keep")
        DSFF()
        self.assertTrue(os.path.isfile("undefined.dsff"))

    def test_all(self):
        import dsff
        self.assertNotIn("load_workbook", dsff.__all__)
        self.assertIn("is_dsff", dsff.__all__)

    def test_arff(self):
        # no label column
        with DSFF("test", 'w') as f:
            f.write([["a", "b"], [1, 2]], {'a': "A", 'b': "B"})
            self.assertNotIn("class", f.to_arff(text=True))
        # quotes and commas in values, missing value in the first row, nominal class
        with DSFF("test", 'w') as f:
            f.write([["name", "x", "label"], ["it's, ok", None, "upx"], ["a\\b", 2.5, "?"]], {'name': "N", 'x': "X"})
            arff = f.to_arff(text=True)
            f.to_arff()
        self.assertIn("@ATTRIBUTE x     NUMERIC", arff)
        self.assertIn("@ATTRIBUTE class {'upx'}", arff)
        self.assertEqual(load_arff("test.arff")['data'][1:], [["it's, ok", None, "upx"], ["a\\b", "2.5", None]])
        # standard ARFF files from Weka
        self.assertTrue(is_arff("% comment\n\n@RELATION iris\n@ATTRIBUTE 'petal width' REAL\n"
                                "@ATTRIBUTE class {Iris-setosa,Iris-virginica}\n\n@DATA\n0.2,Iris-setosa\n"))
        self.assertFalse(is_arff("@RELATION 'x'\n\n@ATTRIBUTE a NUMERIC\n"))
        # comments that are not feature descriptions
        with open("weka.arff", 'w') as f:
            f.write("% 1. Title: Iris\n@RELATION iris\n@ATTRIBUTE a REAL\n@ATTRIBUTE class {x}\n@DATA\n1,x\n% a: A\n")
        self.assertEqual(load_arff("weka.arff")['features'], {'a': "A"})

    def test_db(self):
        data = [["order", "file name", "label"], ["1", "x", "upx"], ["1", "y", "?"]]
        with DSFF("test", 'w') as f:
            f.write(data, {'order': "O"})
            f.to_db()
            f.to_db()  # overwrite
            sql = f.to_db(text=True)
        self.assertIn("INSERT INTO \"data\" VALUES(1,'y',NULL);", sql)
        conn = sqlite3.connect("test.db")
        self.assertEqual(conn.execute("SELECT * FROM data;").fetchall(), [(1, "x", "upx"), (1, "y", None)])
        conn.close()
        with DSFF("test", 'w') as f:
            f.write([["a", "label"]], {'a': "A"})
            self.assertIsNone(f.to_db())

    def test_pyarrow(self):
        if PYARROW:
            with DSFF("test", 'w') as f:
                f.write(DATA, FEATURES, {'m': 1})
                f.to_parquet()
            d = load_parquet("test.parquet")
            self.assertEqual(d['features'], FEATURES)
            self.assertEqual(d['metadata'], {'m': 1})
            self.assertEqual(d['data'][2], ["y", 3, None, None])

    def test_csv(self):
        with open("test.csv", 'w') as f:
            f.write("hash;a;label\nx;1;upx\n")
        self.assertEqual(load_csv("test.csv")['features'], {'a': ""})
        with DSFF("test", 'w') as f:
            f.from_csv("test.csv", exclude=())
            self.assertEqual(f.features, {'hash': "", 'a': ""})
    
    def test_edge_cases(self):
        # binary-like text is not a CSV
        self.assertFalse(is_csv("a;b\x00\n1;2\n"))
        # quoting errors and metadata comments in ARFF
        base = "@RELATION x\n@ATTRIBUTE a STRING\n@DATA\n"
        self.assertFalse(is_arff(base + "'unterminated\n"))
        self.assertFalse(is_arff(base + "'a' b\n"))
        self.assertEqual(load_arff_text(base + "% metadata: {'k': True}\n'a'\n")['metadata'], {'k': True})
        self.assertFalse(is_arff(base + "% metadata: {bad}\n'a'\n"))
        # metadata saved by older versions (Python representation) and unparsable metadata
        with DSFF("test", 'w') as f:
            f.write(DATA, FEATURES)
            f._DSFF__wb.properties.description = "{'k': True, 'note': \"it's\"}"
            self.assertEqual(f.metadata, {'k': True, 'note': "it's"})
            f._DSFF__wb.properties.description = "{bad"
            self.assertRaises(BadDsffFile, getattr, f, "metadata")
            f._DSFF__wb.properties.description = None
        # columns with mixed types are exported to Arrow formats as strings
        if PYARROW:
            with DSFF("test", 'w') as f:
                f.write([["a", "label"], [1, "x"], ["y", "x"]])
                self.assertEqual(f._to_table().column("a").to_pylist(), ["1", "y"])


def load_arff_text(text):
    with open("text.arff", 'w') as f:
        f.write(text)
    return load_arff("text.arff")
