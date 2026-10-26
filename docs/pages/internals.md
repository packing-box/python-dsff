# How it works

## File format

DSFF is straightforward and contains only the minimum for storing a dataset. A `.dsff` file is an XSLX workbook (a ZIP archive) with two and only two worksheets, in this order:

1. `data`: the matrix of the whole dataset, headers included. It may contain the samples' metadata (such as `hash` or `realpath`) but mostly holds the feature values. The class column is named `label`. Missing values are written as `?`.
2. `features`: the name-description pairs of each feature used in `data`, under two headers: `name` and `description`.

The following document properties of the XSLX format are used:

- `title`: the name of the dataset;
- `description`: the metadata of the dataset, serialized as a JSON dictionary;
- `creator`: the user who saved the file, unless already set.

Booleans, integers and floats are stored as such in the cells, and any other value as a string. When read, a string holding a boolean, an integer or a float (as in files saved by older versions, which stored every value as a string) is converted, so that `"1"` comes back as an integer and `"2.5"` as a float.

## Validation

When a file is opened in `r` or `r+` mode, DSFF:

1. loads it with `openpyxl` from an open file, as `openpyxl` rejects the `.dsff` extension of a path; a file it cannot load raises `BadDsffFile`;
2. checks that the worksheets are exactly `data` and `features`;
3. checks that the first row of `features` is `name`, `description`.

Note that XSLX limits a worksheet to 1,048,576 rows.

## Format conversions

Each format lives in a module of `dsff.formats` (`arff`, `csv`, `dataset`, `db` and `pa` for Apache Arrow) that defines four functions:

- `is_<format>`: check whether some input is in this format;
- `load_<format>`: parse a file into a `{'data': ..., 'features': ..., 'metadata': ...}` dictionary;
- `from_<format>`: `load_<format>`, then `DSFF.write`;
- `to_<format>`: write the DSFF in this format.

When a `DSFF` is created, every `from_*` and `to_*` function is bound to the instance as a method. The wrapper fixes the target path (default name, extension) and, for `to_*`, refuses to convert an empty dataset. The Arrow functions are generated for Feather, ORC and Parquet, and are only defined when `pyarrow` and `pandas` can be imported.

| Format | Data | Features | Metadata |
|:--|:-:|:-:|:-:|
| ARFF | yes | as comments | as a comment |
| CSV | yes | no (names only on import) | no |
| SQLite (`db`), missing values as `NULL` | `data` table | `features` table | `metadata` table |
| FilelessDataset | `data.csv` | `features.json` | `metadata.json` |
| Feather, ORC, Parquet | table | schema metadata | schema metadata (`__metadata__`) |

When exporting to ARFF, the columns listed in `exclude` are dropped, the `label` column (if any) becomes the last attribute, a nominal one named `class`, and each other column becomes a `NUMERIC` attribute if all its values are numbers, a `STRING` one otherwise. String values are quoted, with backslash escapes. When importing, unquoted names, comments before `@RELATION` and quoted values are supported, and only the comments named after an attribute become feature descriptions.
