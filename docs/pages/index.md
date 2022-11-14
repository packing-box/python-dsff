# Introduction

DSFF (DataSet File Format) is a tiny library relying on [`openpyxl`](https://pypi.org/project/openpyxl) that allows to store a dataset with its features for use with machine learning in an XSLX file whose structure is enforced. It is intended to make easy to store, edit and exchange a dataset.

It is used with the [Packing Box](https://github.com/packing-box/docker-packing-box) to export datasets in a convenient format.

-----

## Setup

This library is available on [PyPi](https://pypi.python.org/pypi/dsff/) and can be simply installed using Pip:

```sh
pip install --user dsff
```

-----

## Format

DSFF is straightforward and contains only the minimum for storing a dataset.

The following document properties of the XSLX format are used:

- `title`: this holds the name of the dataset
- `description`: this holds a serialized dictionary of the metadata from the dataset

An XSLX workbook format as a DSFF has two and only two worksheets:

1. `data`: the matrix of the whole dataset (including headers), eventually containing samples' metadata but mostly the feature values
2. `features`: the name-description pairs of each feature used in `data` (including two headers: `name` and `description`)

