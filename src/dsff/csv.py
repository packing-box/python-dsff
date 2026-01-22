# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_csv", "to_csv"]


def from_csv(dsff, path=None, exclude=DEFAULT_EXCL):
    """ Populate the DSFF file from a CSV file. """
    path = fix_path(dsff, path, ".csv")
    dsff.logger.debug(f"creating DSFF from {path}...")
    dsff.write(path)
    features = {}
    for headers in dsff['data'].rows:
        for header in headers:
            if header.value in exclude:
                continue
            features[header.value] = ""
        break
    dsff.write(features=features)


def to_csv(dsff, path=None, text=False):
    """ Create a CSV from the data worksheet, saved as a file or output as a string. """
    path = fix_path(dsff, path, ".csv", True)
    dsff.logger.debug(f"extracting data from DSFF to {[path,'CSV'][text]}...")
    with (StringIO() if text else open(path, 'w+')) as f:
        writer = csvmod.writer(f, delimiter=";")
        for row in dsff.data:
            writer.writerow(row)
        if text:
            return f.getvalue()

