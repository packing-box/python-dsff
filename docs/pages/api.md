# Python API

Everything is available from the top-level `dsff` package.

## `DSFF`

```python
dsff.DSFF(path=None, mode=None, logger=None)
```

`path`
:   Path to the `.dsff` file. The `.dsff` extension is appended when missing. Use `"<memory>"` (`dsff.formats.INMEMORY`) for a workbook that is never saved.

`mode`
:   One of `r`, `r+`, `w` or `w+` (see [Modes](usage.md#modes)). It defaults to `r` when a path is given and to `w` otherwise.

`logger`
:   A `logging.Logger`; defaults to the logger named `DSFF`.

Opening a file in `r` or `r+` mode checks that it is a valid DSFF and raises `FileNotFoundError` or `BadDsffFile` otherwise. Opening it in `w` or `w+` mode with a path removes an existing file at that path and starts an empty workbook.

The class is a context manager: leaving the context saves the workbook (except in `r` mode, in memory, or when an exception was raised) and closes it.

In `r` mode, `write`, `from_*` and setting an item raise `ValueError`.

### Methods

`write(data=None, features=None, metadata=None, missing="?")`
:   Write any of the three parts of a dataset, then save:

    - `data`: a matrix (list of rows, the first one holding the headers), the path to a `;`-delimited `data.csv`, or the path to a FilelessDataset folder (which also provides `features.json` and `metadata.json`);
    - `features`: a dictionary of feature names and descriptions, or the path to a `features.json`;
    - `metadata`: a dictionary, or the path to a `metadata.json`.

    The worksheets that are written are cleared first. `None` values in `data` are written as `missing`. Booleans, integers and floats, including strings that hold one (such as `"1"` from a CSV), are stored as such; any other value is stored as a string. Invalid input raises `BadInputData`.

`save()`
:   Save the workbook. Only defined in the `r+`, `w` and `w+` modes.

`close()`
:   Close the workbook without saving.

`to_<format>(path=None, ...)`
:   Convert the dataset to another format, where `<format>` is `arff`, `csv`, `dataset`, `db`, and with `pyarrow` installed, `feather`, `orc` or `parquet`. `path` defaults to the name of the DSFF. The extension of the format is appended unless `path` already ends with it (no extension for `dataset`, which is a folder). Except for `to_dataset`, `text=True` returns the content (as a string, or bytes for Arrow formats) instead of writing a file. An empty DSFF raises `EmptyDsffFile`.

`from_<format>(path=None, ...)`
:   Populate the DSFF from a file in another format (same formats as above). `path` is used as is if it is a file, otherwise with the extension of the format appended.

Format-specific keyword arguments:

| Method | Argument | Default | Meaning |
|:--|:--|:--|:--|
| `to_arff`, `from_arff` | `target` | `"label"` | Name of the column holding the class |
| `to_arff`, `from_arff` | `missing` | `"?"` | Token for missing values |
| `to_arff`, `load_csv` | `exclude` | `("hash", "realpath", "format", "size", "ctime", "mtime")` | Columns that are not features |
| `to_db` | `primary_index` | `0` | Index of the column used as the primary key, if its values are unique and none is missing |
| `to_db` | `missing` | `"?"` | Token for missing values, stored as `NULL` |

### Items and properties

`f["data"]`, `f["features"]`
:   The `openpyxl` worksheets.

`f[name]`, `f[name] = value`
:   A standard XSLX document property (such as `creator` or `title`) if it exists, otherwise a key of the metadata. Setting a value also stores it in the metadata. `description` always refers to the metadata, as this property holds it.

`len(f)`
:   Number of rows in the `data` worksheet, headers included.

| Property | Description |
|:--|:--|
| `data` | Rows of the `data` worksheet, with values evaluated as Python literals when possible |
| `features` | Dictionary of feature names and descriptions |
| `headers` | Names of the features |
| `metadata` | Dictionary of metadata |
| `name` | Name of the dataset (settable): the XSLX `title`, or the file name without extension |
| `path` | Path to the `.dsff` file |
| `mode` | Mode the file was opened with |
| `logger` | Logger in use |

### Static methods

`DSFF.format(text_or_path)`
:   Return the name of the format (`arff`, `csv`, `db`, ...) of the given text, bytes or path, or `None` if none matches.

`DSFF.is_valid_format(text_or_path)`
:   Whether `DSFF.format` recognizes the input.

## Module-level functions

For each format, `dsff` exposes:

`is_<format>(text_or_path, ...)`
:   Whether the input (text, bytes or path; a path for `is_dataset`) is valid in this format. A string is taken as a path if it is a single line and points to an existing file or folder. `is_dsff` checks for a DSFF file.

`load_<format>(path, ...)`
:   Load the file as a dictionary with the `data`, `features` and `metadata` keys, which can be passed to `DSFF.write(**...)`.

```python
>>> import dsff
>>> dsff.is_csv("a;b\n1;2\n")
True
>>> d = dsff.load_csv("my-dataset.csv")
>>> with dsff.DSFF("my-dataset", "w") as f:
...     f.write(**d)
```

## Exceptions

These exceptions are registered as builtins when `dsff` is imported:

| Exception | Base | Raised when |
|:--|:--|:--|
| `BadDsffFile` | `OSError` | The file is not a valid DSFF |
| `BadInputData` | `ValueError` | Input to `write` or `from_*` is invalid |
| `EmptyDsffFile` | `ValueError` | Converting a DSFF without data |
