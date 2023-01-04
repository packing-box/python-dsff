# -*- coding: UTF-8 -*-
import hashlib
import os
import random
import zipfile
from datetime import datetime
from dsff import DSFF, BadDsffFile, BadInputData
from dsff.__common__ import INMEMORY, MISSING_TOKEN
from openpyxl.worksheet.worksheet import Worksheet
from unittest import TestCase


BAD = "THIS_FILE_DOES_NOT_EXIST"
TEST_NAME = "example-dataset"
TEST = ".%s.dsff" % TEST_NAME
TEST_BASENAME = ".%s" % TEST_NAME

TEST_DATA = [
    ["hash", "field1", "field2", "label"],
]
__count = 0
for i in range(10):
    label = random.randint(0, 1)
    if label == 1:
        __count += 1
    TEST_DATA.append([hashlib.md5(bytes(i)).hexdigest(),
                      random.random(),
                      bool(random.randint(0, 1)),
                      label if i != 5 else MISSING_TOKEN])
TEST_FEATURES = {'field1': "float feaure", 'field2': "boolean feature"}
TEST_METADATA = {'number': 10, 'counts': __count}

TEST_ARFF = """@RELATION ".example-dataset"
# test comment

@ATTRIBUTE field1 NUMERIC
@ATTRIBUTE field2 NUMERIC
@ATTRIBUTE class  NUMERIC

@DATA
0.7730324256399123,  1, 1
0.8362967783842694,  0, 1
0.13180945479377482, 0, 1
0.8170624057089075,  1, ?
0.6396790279088408,  1, 1
0.15569500307505724, 1, 1
0.21775348494485125, 0, ?
0.43648596037070286, 1, 0
0.4010220773876585,  1, 1
0.3091775358915919,  1, 0
"""


def create_bad_test_dsff():
    create_test_dsff()
    with DSFF(TEST, 'w+') as f:
        del f._DSFF__wb['features']
        f._DSFF__change = True


def create_test_dsff():
    with DSFF(TEST, 'w') as f:
        f.write(TEST_DATA, TEST_FEATURES, TEST_METADATA)


def rmdir(path):
    try:
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))
        os.rmdir(path)
    except:
        pass


def rmfile(path):
    try:
        os.remove(path)
    except:
        pass


class Unserializable:
    test = 1
TEST_OBJECT = Unserializable()

