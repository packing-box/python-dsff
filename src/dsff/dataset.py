# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_dataset", "to_dataset"]


def from_dataset(dsff, path=None):
    """ Populate the DSFF file from a Dataset structure. """
    path = fix_path(dsff, path)
    dsff.logger.debug(f"creating DSFF from {path}...")
    if not isdir(path):
        raise BadInputData("Not a folder")
    else:
        if len(missing := [f for f in ["data.csv", "features.json", "metadata.json"] if not isfile(join(path, f))]) > 0:
            raise BadInputData(f"Not a valid dataset folder (missing: {', '.join(missing)})")
    dsff.write(path)


def to_dataset(dsff, path=None):
    """ Create a dataset folder according to the Dataset structure ;
    name
     +-- data.csv
     +-- features.json
     +-- metadata.json
    """
    path = fix_path(dsff, path, split=True)
    makedirs(path, exist_ok=True)
    dsff.logger.debug(f"converting DSFF to (Fileless)Dataset {path}...")
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

