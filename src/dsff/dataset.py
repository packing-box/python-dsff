# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = ["from_dataset", "to_dataset"]


def from_dataset(dsff, path=None):
    """ Populate the DSFF file from an ARFF file. """
    path = expanduser(path or dsff.name)
    dsff.logger.debug("creating DSFF from (Fileless)Dataset folder...")
    if not isdir(path):
        raise BadInputData("Not a folder")
    else:
        missing = []
        for f in ["data.csv", "features.json", "metadata.json"]:
            if not isfile(join(path, f)):
                missing.append(f)
        if len(missing) > 0:
            raise BadInputData("Not a valid dataset folder (missing: %s)" % ", ".join(missing))
    dsff.write(path)


def to_dataset(dsff, path=None):
    """ Create a dataset folder according to the Dataset structure ;
    name
     +-- data.csv
     +-- features.json
     +-- metadata.json
    """
    path = splitext(expanduser(path or dsff.name))[0]
    makedirs(path, exist_ok=True)
    dsff.logger.debug("converting DSFF to (Fileless)Dataset folder...")
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

