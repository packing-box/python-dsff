# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_csv", "is_csv", "load_csv", "to_csv"]


def from_csv(dsff, path=None, exclude=DEFAULT_EXCL, **kw):
    """ Populate the DSFF file from a CSV file. """
    dsff.write(**load_csv(path))


@text_or_path
def is_csv(text, **kw):
    """ Check if the input text or path is a valid CSV. """
    try:
        dialect = csvmod.Sniffer().sniff(text := ensure_str(text))
        csvmod.Sniffer().has_header(text)
        return True
    except (csvmod.Error, UnicodeDecodeError):
        return False


def load_csv(path, exclude=DEFAULT_EXCL, **kw):
    """ Load a CSV file as a dictionary with data, features and metadata. """
    data = {'metadata': {}}
    with open(expanduser(path)) as f:
        data['data'] = [r for r in csvmod.reader(f, delimiter=CSV_DELIMITER)]
    data['features'] = {h: "" for h in data['data'][0] if h not in exclude}
    return data


def to_csv(dsff, path=None, text=False, **kw):
    """ Create a CSV from the data worksheet, saved as a file or output as a string. """
    with (StringIO() if text else open(path, 'w+')) as f:
        writer = csvmod.writer(f, delimiter=";")
        for row in dsff.data:
            writer.writerow(row)
        if text:
            return f.getvalue()

