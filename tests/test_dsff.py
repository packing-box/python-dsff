#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""DSFF tests.

"""
from .utils import *


class TestDsff(TestCase):
    @classmethod
    def tearDownClass(cls):
        rmdir(TEST_BASENAME)
        rmfile(TEST)
        rmfile("undefined.dsff")
        for ext in [".arff", ".csv", ".db"]:
            rmfile(TEST_BASENAME + ext)
    
    def tearDown(self):
        rmfile(TEST)
    
    def test_dsff_modes(self):
        # path not set, shall not work with 'r+?' or a bad mode
        self.assertRaises(ValueError, DSFF, None, "BAD_MODE")
        self.assertRaises(ValueError, DSFF, None, "r")
        self.assertRaises(ValueError, DSFF, None, "r+")
        self.assertRaises(FileNotFoundError, DSFF, BAD)
    
    def test_dsff_format(self):
        # not a DSFF file
        with open(TEST, 'w') as f:
            f.write("BAD")
        self.assertRaises(BadDsffFile, DSFF, TEST)
        # missing 'features' worksheet
        create_bad_test_dsff()
        self.assertRaises(BadDsffFile, DSFF, TEST)
        # bad 'features' worksheet
        create_test_dsff()
        with DSFF(TEST, 'r+') as f:
            f['features']['C1'] = "BAD"
            f._DSFF__change = True
        self.assertRaises(BadDsffFile, DSFF, TEST)
        # read and write properties and metadata
        create_test_dsff()
        with DSFF(TEST, 'r+') as f:
            for worksheet in ["data", "features"]:
                # getting 'data' and 'features' returns the related worksheet
                self.assertTrue(isinstance(f[worksheet], Worksheet))
                # cannot overwrite 'data' and 'features' worksheets
                self.assertRaises(ValueError, f.__setitem__, worksheet, None)
            # write/read common properties
            f['title'] = "test"
            self.assertEqual(f['title'], "test")
            f['title'] = "example-dataset"
            self.assertTrue(isinstance(f['created'], datetime))
            self.assertRaises(KeyError, f.__getitem__, "THIS_PROPERTY_OR_METADATA_KEY_DOES_NOT_EXIST")
        # attempt to write improper data, features or metadata
        with DSFF() as f:
            # input bad data list or features dictionary or metadata dictionary
            self.assertRaises(BadInputData, f.write, "BAD")
            self.assertRaises(BadInputData, f.write, TEST_DATA, "BAD")
            self.assertRaises(BadInputData, f.write, TEST_DATA, TEST_FEATURES, "BAD")
            # now input correct data
            self.assertIsNone(f.write(TEST_DATA, TEST_FEATURES, TEST_METADATA))
            self.assertTrue(len(f.data) > 0)
            # try to input an object within features
            k = list(TEST_FEATURES.keys())[0]
            v = TEST_FEATURES[k]
            TEST_FEATURES[k] = TEST_OBJECT
            self.assertRaises(BadInputData, f.write, None, TEST_FEATURES)
            TEST_FEATURES[k] = v
            # try to input an object within features
            k = list(TEST_METADATA.keys())[0]
            v = TEST_METADATA[k]
            TEST_METADATA[k] = TEST_OBJECT
            self.assertRaises(BadInputData, f.write, None, None, TEST_METADATA)
            TEST_METADATA[k] = v
    
    def test_conversion_arff(self):
        self.assertTrue(is_arff(TEST_ARFF))
        # DSFF to ARFF
        create_test_dsff()
        with DSFF(TEST) as f:
            self.assertIsNotNone(f.to_arff(text=True))
            self.assertIsNone(f.to_arff())
        with DSFF(mode='w+') as f:
            self.assertRaises(ValueError, f.to_arff, ())
        # ARFF to DSFF
        #  use a test ARFF with a comment line
        with open(arff := f"{TEST_BASENAME}.arff", 'w') as f:
            f.write(TEST_ARFF)
        self.assertTrue(is_arff(arff))
        self.assertIsInstance(load_arff(arff), dict)
        with DSFF() as f:
            f.from_arff(TEST_BASENAME)
        # test for multiple error scenarios
        with open(arff) as f:
            d = f.read().splitlines(True)
        @contextmanager
        def _test():
            yield d
            with open(arff, 'w') as f:
                f.writelines(d)
            with DSFF() as f:
                self.assertRaises(BadInputData, f.from_arff, TEST_BASENAME)
        #  use a bad ARFF without the @RELATION line
        with _test():
            d[0] = "@RELATION BAD:NO_QUOTE\n"
            d.remove(d[1])
        #  use a bad ARFF without the @RELATION line
        with _test():
            l1, d = d[0], d[1:]
        d.insert(0, "@RELATION 'example-dataset'\n")
        #  use a bad @ATTRIBUTE line
        with _test():
            tmp_attr, d[3] = d[3], "@ATTRIBUTE test NOT_A_CORRECT_TYPE\n"
        #  use an @ATTRIBUTE at a bad position
        with _test():
            d[3] = tmp_attr
            d.insert(10, "@ATTRIBUTE test BAD\n")
        # inject data line with a wrong number of columns
        with _test():
            d.insert(10, "0.123456789, 0")
        #  put @DATA at a bad position
        with _test():
            d.insert(10, d.pop(6))
    
    def test_conversion_csv(self):
        self.assertFalse(is_csv(b"PK\x03\x04\x14\x00\x00\x00\x08\x00P\xb3T\\F\xc7MH"))
        # DSFF to CSV
        create_test_dsff()
        with DSFF(TEST) as f:
            self.assertIsNotNone(f.to_csv(text=True))
            self.assertIsNone(f.to_csv())
        self.assertTrue(is_csv(csv := f"{TEST_BASENAME}.csv"))
        self.assertIsInstance(load_csv(csv), dict)
        # CSV to DSFF
        with DSFF() as f:
            f.from_csv(TEST_BASENAME)
    
    def test_conversion_dataset(self):
        # DSFF to FilelessDataset
        create_test_dsff()
        with DSFF(TEST) as f:
            self.assertIsNone(f.to_dataset())
        # FilelessDataset to DSFF
        with DSFF() as f:
            f.from_dataset(TEST_BASENAME)
        self.assertTrue(is_dataset(TEST_BASENAME))
        self.assertRaises(BadInputData, load_dataset, 0)
        self.assertIsInstance(load_dataset(TEST_BASENAME), dict)
        # FilelessDataset to DSFF (bad input dataset)
        os.remove(os.path.join(TEST_BASENAME, "metadata.json"))
        with DSFF() as f:
            self.assertRaises(BadInputData, f.from_dataset, TEST_BASENAME)
        rmdir(TEST_BASENAME)
        # FilelessDataset to DSFF (not a folder)
        with open(TEST_BASENAME, 'w') as f:
            pass
        with DSFF() as f:
            self.assertRaises(BadInputData, f.from_dataset, TEST_BASENAME)
        os.remove(TEST_BASENAME)
        os.makedirs(TEST_BASENAME)
        self.assertFalse(is_dataset(TEST_BASENAME))
        rmdir(TEST_BASENAME)
    
    def test_conversion_db(self):
        self.assertFalse(is_db(b"PK\x03\x04\x14\x00\x00\x00\x08\x00P\xb3T\\F\xc7MH"))
        self.assertFalse(is_db(b"SQLite format 3\x00\x10\x00\x01\x01\x00@"))
        # DSFF to SQL database
        create_test_dsff()
        with DSFF(TEST) as f:
            self.assertIsNotNone(f.to_db(text=True))
            self.assertIsNone(f.to_db())
        self.assertTrue(is_db(db := f"{TEST_BASENAME}.db"))
        self.assertIsInstance(load_db(db), dict)
        # SQL database to DSFF
        with DSFF() as f:
            f.from_db(TEST_BASENAME)
    
    def test_conversion_pyarrow_formats(self):
        if PYARROW:
            create_test_dsff()
            with DSFF(TEST) as f:
                self.assertIsNone(f.to_dataset())
            for fmt in ["feather", "orc", "parquet"]:
                with DSFF(INMEMORY) as f:
                    f.from_dataset(path=TEST_BASENAME)
                    self.assertIsNone(getattr(f, f"to_{fmt}")(TEST_BASENAME))
                    self.assertIsNotNone(getattr(f, f"to_{fmt}")(text=True))
                is_ = globals()[f'is_{fmt}']
                self.assertTrue(is_(fn := f"{TEST_BASENAME}.{fmt}"))
                self.assertFalse(is_(b"PK\x03\x04\x14\x00\x00\x00\x08\x00P\xb3T\\F\xc7MH"))
                self.assertIsInstance(globals()[f'load_{fmt}'](fn), dict)
                with DSFF(INMEMORY) as f:
                    self.assertIsNone(getattr(f, f"from_{fmt}")(TEST_BASENAME))
                    f.to_dataset(path=TEST_BASENAME)
                os.remove(f"{TEST_BASENAME}.{fmt}")
            rmdir(TEST_BASENAME)
            # test without the 'label' column
            with open(f"{TEST_BASENAME}.arff", 'w') as f:
                f.write(TEST_ARFF.replace("class", "test").replace("?", "-1"))
            with DSFF() as f:
                f.from_arff(TEST_BASENAME)
                self.assertIsNotNone(f._to_table())
    
    def test_in_memory(self):
        create_test_dsff()
        with DSFF(TEST) as f:
            self.assertIsNone(f.to_dataset())
            f.name = TEST
            self.assertIsNotNone(f.headers)
        self.assertTrue(DSFF.is_valid_format(TEST_BASENAME))
        with DSFF(INMEMORY) as f:
            self.assertRaises(EmptyDsffFile, f.to_arff)
            self.assertIsNone(f.from_dataset(TEST_BASENAME))
            self.assertIsNone(f.to_arff())
        self.assertRaises(ValueError, DSFF.is_valid_format, 0)
        self.assertTrue(DSFF.is_valid_format(f"undefined.arff"))
        os.remove(f"undefined.arff")
        rmdir(TEST_BASENAME)
        with DSFF(INMEMORY) as f:
            self.assertRaises(ValueError, f.from_arff)

