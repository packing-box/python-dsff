#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""DSFF behaviour tests.

"""
import logging
import sqlite3

from .utils import *


DATA = [["hash", "a", "b", "c", "label"], ["h1", 1, 2.5, True, "upx"], ["h2", 3, 0.5, False, "?"]]
FEATURES = {'a': "integer feature", 'b': "float feature", 'c': "boolean feature"}
METADATA = {'source': "test", 'counts': {'upx': 1}}
ARROW = ["feather", "orc", "parquet"] if PYARROW else []


def make(name="test", data=DATA, features=FEATURES, metadata=METADATA):
    with DSFF(name, 'w') as f:
        f.write(data, features, metadata)
    return f"{name}.dsff"


class TestModes(DsffTestCase):
    def test_default_mode(self):
        self.assertEqual(DSFF().mode, "w")
        self.assertEqual(DSFF(INMEMORY).mode, "w")
        self.assertEqual(DSFF(make()).mode, "r")

    def test_save_method(self):
        path = make()
        self.assertFalse(hasattr(DSFF(path, 'r'), "save"))
        for mode in ["r+", "w", "w+"]:
            self.assertTrue(hasattr(DSFF(path, mode), "save"))
            path = make()

    def test_read_write(self):
        # r+ keeps the content and saves the changes
        with DSFF(path := make(), 'r+') as f:
            self.assertEqual(f.data, DATA)
            f['note'] = "updated"
        self.assertEqual(DSFF(path)['note'], "updated")
        # w truncates an existing file when opened
        with DSFF(path, 'w') as f:
            self.assertEqual(f.data, [])
            self.assertFalse(os.path.exists(path))

    def test_save(self):
        f = DSFF(path := make(), 'r+')
        f['note'] = "saved"
        f.save()
        f.close()
        self.assertEqual(DSFF(path).metadata['note'], "saved")

    def test_in_memory(self):
        with DSFF(INMEMORY) as f:
            f.write(DATA, FEATURES, METADATA)
            self.assertEqual(f.data, DATA)
            self.assertEqual(f.path, INMEMORY)
        self.assertEqual(os.listdir(), [])


class TestProperties(DsffTestCase):
    def test_properties(self):
        logger = logging.getLogger("test")
        with DSFF(make(), 'r+', logger=logger) as f:
            self.assertEqual(f.name, "test")
            self.assertEqual(f.path, "test.dsff")
            self.assertEqual(f.headers, list(FEATURES.keys()))
            self.assertEqual(f.features, FEATURES)
            self.assertEqual(f.metadata, METADATA)
            self.assertEqual(len(f), len(DATA))
            self.assertIs(f.logger, logger)
            f.name = "renamed"
            self.assertEqual(f.name, "renamed")
            f._DSFF__change = True
        # the name is saved as the title
        self.assertEqual(DSFF("test.dsff")['title'], "renamed")
        self.assertEqual(DSFF("other", 'w').path, "other.dsff")

    def test_items(self):
        with DSFF(make(), 'r+') as f:
            self.assertIsInstance(f['data'], Worksheet)
            self.assertIsInstance(f['features'], Worksheet)
            # standard properties
            self.assertIsInstance(f['created'], datetime)
            f['creator'] = "someone"
            self.assertEqual(f['creator'], "someone")
            # 'description' holds the metadata, hence it is a metadata key
            f['description'] = "a dataset"
            self.assertEqual(f['description'], "a dataset")
            self.assertEqual(f.metadata['description'], "a dataset")
            self.assertEqual(f['source'], "test")
            self.assertRaises(KeyError, f.__getitem__, "missing_key")
            for name in ["data", "features"]:
                self.assertRaises(ValueError, f.__setitem__, name, None)
        self.assertEqual(DSFF("test.dsff")['creator'], "someone")

    def test_creator(self):
        from getpass import getuser
        self.assertEqual(DSFF(make())['creator'], getuser())

    def test_data_only(self):
        # a DSFF without features is valid
        with DSFF("test", 'w') as f:
            f.write(DATA)
        with DSFF("test.dsff") as f:
            self.assertEqual(f.data, DATA)
            self.assertEqual(f.features, {})
            self.assertEqual(f.metadata, {})

    def test_exceptions(self):
        self.assertTrue(issubclass(BadDsffFile, OSError))
        self.assertTrue(issubclass(BadInputData, ValueError))
        self.assertTrue(issubclass(EmptyDsffFile, ValueError))


class TestWrite(DsffTestCase):
    def test_from_files(self):
        os.makedirs("ds")
        with open("ds/data.csv", 'w') as f:
            f.write("hash;a;label\nh1;1;upx\n")
        with open("ds/features.json", 'w') as f:
            json.dump({'a': "A"}, f)
        with open("ds/metadata.json", 'w') as f:
            json.dump({'m': 1}, f)
        with DSFF("test", 'w') as f:
            f.write("ds/data.csv", "ds/features.json", "ds/metadata.json")
            self.assertEqual((f.data, f.features, f.metadata), ([["hash", "a", "label"], ["h1", 1, "upx"]], {'a': "A"},
                                                                {'m': 1}))
        # a dataset folder provides the three files and the name
        with DSFF() as f:
            f.write("ds")
            self.assertEqual(f.path, "ds.dsff")
        # files with other names are rejected
        os.rename("ds/features.json", "ds/other.json")
        with DSFF() as f:
            self.assertRaises(BadInputData, f.write, None, "ds/other.json")
            self.assertRaises(BadInputData, f.write, None, None, "ds/other.json")
            self.assertRaises(BadInputData, f.write, "ds/other.json")

    def test_missing_token(self):
        with DSFF("test", 'w') as f:
            f.write([["a", "label"], [None, "x"]], missing="NA")
            self.assertEqual(f.data, [["a", "label"], ["NA", "x"]])

    def test_empty(self):
        with DSFF(INMEMORY) as f:
            for fmt in ["arff", "csv", "db", "dataset"] + ARROW:
                self.assertRaises(EmptyDsffFile, getattr(f, f"to_{fmt}"))


class TestConversions(DsffTestCase):
    def assertRoundTrip(self, fmt, data=DATA, features=FEATURES, metadata=METADATA):
        with DSFF(make()) as f:
            getattr(f, f"to_{fmt}")()
        with DSFF("back", 'w') as f:
            getattr(f, f"from_{fmt}")("test")
            self.assertEqual(f.data, data)
            self.assertEqual(f.features, features)
            self.assertEqual(f.metadata, metadata)

    def test_arff(self):
        # the excluded columns (here 'hash') are dropped
        self.assertRoundTrip("arff", [r[1:] for r in DATA])
        self.assertEqual(DSFF("back.dsff")['title'], "test")

    def test_csv(self):
        # CSV only holds the data ; feature names come from the headers
        self.assertRoundTrip("csv", features={'a': "", 'b': "", 'c': ""}, metadata={})

    def test_dataset(self):
        self.assertRoundTrip("dataset")
        self.assertEqual(sorted(os.listdir("test")), ["data.csv", "features.json", "metadata.json"])

    def test_db(self):
        self.assertRoundTrip("db")

    def test_pyarrow(self):
        for fmt in ARROW:
            with self.subTest(fmt=fmt):
                # pyarrow's ORC writer does not keep the schema metadata
                self.assertRoundTrip(fmt, **({'features': {}, 'metadata': {}} if fmt == "orc" else {}))

    def test_text_output(self):
        with DSFF(make()) as f:
            for fmt in ["arff", "csv"]:
                getattr(f, f"to_{fmt}")()
                with open(f"test.{fmt}", newline='') as fh:
                    self.assertEqual(getattr(f, f"to_{fmt}")(text=True), fh.read())
            for fmt in ARROW:
                self.assertIsInstance(getattr(f, f"to_{fmt}")(text=True), bytes)
            sql = f.to_db(text=True)
        conn = sqlite3.connect(":memory:")
        conn.executescript(sql)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM data;").fetchone(), (len(DATA) - 1, ))
        conn.close()

    def test_paths(self):
        with DSFF(make()) as f:
            f.to_csv("out")
            f.to_csv("other.csv")
            f.to_dataset("folder.v1")
        for path in ["out.csv", "other.csv", "folder.v1/data.csv"]:
            self.assertTrue(os.path.isfile(path))

    def test_format(self):
        with DSFF(make()) as f:
            for fmt in ["arff", "csv", "db", "dataset"] + ARROW:
                getattr(f, f"to_{fmt}")()
        for fmt in ["arff", "csv", "db"] + ARROW:
            with self.subTest(fmt=fmt):
                self.assertEqual(DSFF.format(f"test.{fmt}"), fmt)
        self.assertEqual(DSFF.format("test"), "dataset")
        self.assertEqual(DSFF.format("test.dsff"), "dsff")
        with open("test.dsff", 'rb') as f:
            self.assertEqual(DSFF.format(f.read()), "dsff")
        self.assertFalse(DSFF.is_valid_format(b"\x00\x01\x02"))
        self.assertTrue(DSFF.is_valid_format("test.dsff"))

    def test_load(self):
        with DSFF(make()) as f:
            for fmt in ["arff", "csv", "db", "dataset"] + ARROW:
                getattr(f, f"to_{fmt}")()
        for fmt in ["arff", "csv", "db", "dataset"] + ARROW:
            with self.subTest(fmt=fmt):
                d = globals()[f'load_{fmt}']("test" if fmt == "dataset" else f"test.{fmt}")
                self.assertEqual(sorted(d.keys()), ["data", "features", "metadata"])


class TestArff(DsffTestCase):
    def test_parsing(self):
        with open("test.arff", 'w') as f:
            f.write("@RELATION \"my data\"\n@ATTRIBUTE bin NUMERIC\n@ATTRIBUTE txt STRING\n"
                    "@ATTRIBUTE target {a,b}\n@DATA\n1, -, a\n0, 'x', NA\n")
        d = load_arff("test.arff", target="target", missing="NA")
        # binary columns become booleans, '-' an empty string and the missing token None
        self.assertEqual(d['data'], [["bin", "txt", "target"], ["True", "", "a"], ["False", "x", None]])
        self.assertEqual(d['features'], {'bin': "", 'txt': ""})
        with DSFF("test2", 'w') as f:
            f.from_arff("test.arff")
            self.assertEqual(f['title'], "my data")

    def test_class_renamed(self):
        d = load_arff_text("@RELATION r\n@ATTRIBUTE a NUMERIC\n@ATTRIBUTE class {x}\n@DATA\n1,x\n", target="y")
        self.assertEqual(d['data'][0], ["a", "y"])

    def test_errors(self):
        base = "@RELATION r\n@ATTRIBUTE a NUMERIC\n@DATA\n1\n"
        for bad in ["@ATTRIBUTE a NUMERIC\n@DATA\n1\n",                    # no @RELATION
                    "@RELATION r\n@DATA\n1\n",                             # no @ATTRIBUTE
                    "@RELATION r\n@ATTRIBUTE a\n@DATA\n1\n",               # no type
                    "@RELATION r\n@ATTRIBUTE a NUMERIC\n1\n",              # no @DATA
                    base + "@ATTRIBUTE b NUMERIC\n",                       # @ATTRIBUTE after @DATA
                    base + "1, 2\n",                                       # wrong number of columns
                    "@RELATION r\n@ATTRIBUTE a NUMERIC\n@DATA\n'a' 'b'\n", # garbage after a quoted value
                    b"\xff\xfe"]:                                          # not text
            with self.subTest(bad=bad):
                self.assertFalse(is_arff(bad))
        self.assertTrue(is_arff(base))


class TestDb(DsffTestCase):
    def test_bad_database(self):
        conn = sqlite3.connect("bad.db")
        conn.execute("CREATE TABLE other (a TEXT);")
        conn.commit()
        conn.close()
        self.assertTrue(is_db("bad.db"))
        self.assertRaises(BadInputData, load_db, "bad.db")

    def test_types(self):
        with DSFF(make()) as f:
            f.to_db()
        conn = sqlite3.connect("test.db")
        schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='data';").fetchone()[0]
        conn.close()
        for field in ['"hash" TEXT PRIMARY KEY', '"a" INTEGER', '"b" REAL', '"c" INTEGER', '"label" TEXT']:
            self.assertIn(field, schema)

    def test_primary_index(self):
        with DSFF(make()) as f:
            self.assertIn('"a" INTEGER PRIMARY KEY', f.to_db(text=True, primary_index=1))
            self.assertIn('CREATE TABLE data ("hash" TEXT, "a" INTEGER,', f.to_db(text=True, primary_index=None))


class TestCsv(DsffTestCase):
    def test_detection(self):
        self.assertTrue(is_csv("a;b\n1;2\n"))
        self.assertTrue(is_csv(b"a,b\n1,2\n"))
        self.assertFalse(is_csv(b"\xff\xfe\x00"))
        # a folder is not a CSV, even if its name looks like one
        os.makedirs("folder")
        self.assertFalse(is_csv("folder"))
        self.assertRaises(ValueError, is_csv, 1)

    def test_exclude(self):
        with open("test.csv", 'w') as f:
            f.write("hash;size;a;label\nh;1;2;x\n")
        self.assertEqual(load_csv("test.csv")['features'], {'a': ""})
        self.assertEqual(load_csv("test.csv", exclude=("a", ))['features'], {'hash': "", 'size': ""})


def load_arff_text(text, **kw):
    with open("text.arff", 'w') as f:
        f.write(text)
    return load_arff("text.arff", **kw)


class TestCommon(DsffTestCase):
    def test_ensure_str(self):
        self.assertEqual(ensure_str(b"text"), "text")
        self.assertEqual(ensure_str("text"), "text")
        self.assertEqual(ensure_str(1), "1")
    
    def test_path_keyword(self):
        # the path can also be passed as a keyword argument
        with DSFF(make()) as f:
            f.to_csv(path="kw")
        with DSFF("back", 'w') as f:
            f.from_csv(path="kw")
            self.assertEqual(f.data, DATA)
