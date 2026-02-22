# -*- coding: UTF-8 -*-
from .__common__ import *
from .csv import load_csv


__all__ = ["from_dataset", "is_dataset", "load_dataset", "to_dataset"]


def _parse(path):
    if not isdir(expanduser(path)):
        raise BadInputData("Not a folder")
    if len(missing := [f for f in ["data.csv", "features.json", "metadata.json"] if not isfile(join(path, f))]) > 0:
        raise BadInputData(f"Not a valid dataset folder (missing: {', '.join(missing)})")


def from_dataset(dsff, path=None, **kw):
    """ Populate the DSFF file from a Dataset structure. """
    _parse(path)
    dsff.write(path)


def is_dataset(path, **kw):
    """ Check if the input path is a valid Dataset. """
    try:
        _parse(path)
        return True
    except BadInputData:
        return False


def load_dataset(path, **kw):
    """ Load a dataset folder as a dictionary with data, features and metadata. """
    if not isdir(d := expanduser(str(path))):
        raise BadInputData("Not a folder")
    dp, fp, mp = join(d, "data.csv"), join(d, "features.json"), join(d, "metadata.json")
    data = {}
    data['data'] = load_csv(dp)['data']
    with open(fp) as f:
        data['features'] = json.load(f)
    with open(mp) as f:
        data['metadata'] = json.load(f)
    return data


def to_dataset(dsff, path=None, **kw):
    """ Create a dataset folder according to the following structure ;
    name
     +-- data.csv
     +-- features.json
     +-- metadata.json
    """
    makedirs(path, exist_ok=True)
    # handle data first
    dsff.logger.debug("> making data.csv...")
    with open(join(path, "data.csv"), 'w+') as f:
        writer = csvmod.writer(f, delimiter=";")
        for cells in dsff['data'].rows:
            writer.writerow([dsff._DSFF__eval(c.value) for c in cells])
    # then handle features dictionary
    dsff.logger.debug("> making features.json...")
    with open(join(path, "features.json"), 'w+') as f:
        json.dump(dsff.features, f, indent=2)
    # finally handle metadata dictionary
    dsff.logger.debug("> making metadata.json...")
    with open(join(path, "metadata.json"), 'w+') as f:
        json.dump(dsff.metadata, f, indent=2)

