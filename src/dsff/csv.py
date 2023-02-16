# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_csv", "to_csv"]


def from_csv(dsff, path=None, exclude=DEFAULT_EXCL):
    """ Populate the DSFF file from an ARFF file. """
    path = expanduser(path or dsff.name)
    if not path.endswith(".csv"):
        path += ".csv"
    dsff.logger.debug("creating DSFF from CSV file...")
    dsff.write(path)
    features = {}
    for headers in dsff['data'].rows:
        for header in headers:
            features[header.value] = ""
        break
    dsff.write(features=features)


def to_csv(dsff, path=None, text=False):
    """ Create a CSV from the data worksheet, saved as a file or output as a string. """
    path = splitext(expanduser(path or dsff.name))[0]
    if not path.endswith(".csv"):
        path += ".csv"
    dsff.logger.debug("extracting data from DSFF to CSV file...")
    with (StringIO() if text else open(path, 'w+')) as f:
        writer = csvmod.writer(f, delimiter=";")
        for cells in dsff['data'].rows:
            writer.writerow([dsff._DSFF__eval(c.value) for c in cells])
        if text:
            return f.getvalue()

