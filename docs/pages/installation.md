# Installation

## Requirements

- Python **3.10 or later**. CI runs on 3.10 to 3.13.
- [`openpyxl`](https://pypi.org/project/openpyxl/), which pip installs automatically.
- Optionally, [`pyarrow`](https://arrow.apache.org/docs/python/index.html) (with [`pandas`](https://pypi.org/project/pandas/)) for the [Apache Arrow](https://arrow.apache.org/) formats.

## From PyPI

```console
$ pip install dsff
```

To also handle the Apache Arrow formats (Feather, ORC and Parquet), install the `arrow` extra:

```console
$ pip install dsff[arrow]
```

The `all` extra installs every available extension:

```console
$ pip install dsff[all]
```

## From source

```console
$ git clone https://github.com/packing-box/python-dsff
$ cd python-dsff
$ pip install .
```

For development, use an editable install:

```console
$ pip install -e .
```

## Checking the installation

```python
>>> import dsff
>>> dsff.__version__
'1.2.3'
```

The `to_feather`, `to_orc` and `to_parquet` methods (and their `from_*` counterparts) only exist when `pyarrow` and `pandas` can be imported:

```python
>>> from dsff.formats import PYARROW
>>> PYARROW
True
```
