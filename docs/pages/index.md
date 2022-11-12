# Introduction

DSFF (DataSet File Format) is a tiny library relying on [`openpyxl`](https://pypi.org/project/openpyxl) that allows to store a dataset with its features for use with machine learning in an XSLX file whose structure is enforced. It is intended to make easy to store, edit and exchange a dataset.

It is used with the [Packing Box](https://github.com/packing-box/docker-packing-box) to export datasets in a portable format.

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

- `title`: this is the name of the dataset
- `description`: this holds a serialized dictionary of metadata

An XSLX workbook format as a DSFF has two and only two worksheets:

1. `data`: the matrix of the whole dataset (including headers), eventually containing samples' metadata but mostly the feature values
2. `features`: the name-description pairs of each feature used in `data` (including two headers: `name` and `description`)

-----

## Usage

This library contains the `DSFF` class that can:

- Behave as a context manager
- Have items got (`data` and `features` return the related worksheets) or set (for setting, in order of precedence, standard XSLX properties and metadata contained in the `description` property)
- Write data, features and metadata
- Convert to the [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html) (for use with the [Weka](https://www.cs.waikato.ac.nz/ml/weka) framework) or [CSV](https://www.rfc-editor.org/rfc/rfc4180) formats or to a [FilelessDataset structure](https://docker-packing-box.readthedocs.io/en/latest/usage/datasets.html) (from the [Packing Box](https://github.com/packing-box/docker-packing-box))

**Creating a DSFF from a FilelessDataset**

```python
>>> import dsff
>>> with dsff.DSFF() as f:
    f.write("/path/to/my-dataset")  # folder of a FilelessDataset (containing data.csv, features.json and metadata.json)
    f.to_arff()                     # creates ./my-dataset.arff
    f.to_csv()                      # creates ./my-dataset.csv
# while leaving the context, ./my-dataset.dsff is created
```

**Creating a FilelessDataset from a DSFF**

```python
>>> import dsff
>>> with dsff.DSFF("/path/to/my-dataset.dsff") as f:
    f.to_dataset()  # creates ./[dsff-title] with data.csv, features.json and metadata.json
```

