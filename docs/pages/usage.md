# Usage

This library contains the `DSFF` class that can:

- Behave as a context manager
- Have items got (`data` and `features` return the related worksheets) or set (for setting, in order of precedence, standard XSLX properties and metadata contained in the `description` property)
- Write data, features and metadata
- Convert to the [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html) (for use with the [Weka](https://www.cs.waikato.ac.nz/ml/weka) framework) or [CSV](https://www.rfc-editor.org/rfc/rfc4180) formats or to a [FilelessDataset structure](https://docker-packing-box.readthedocs.io/en/latest/usage/datasets.html) (from the [Packing Box](https://github.com/packing-box/docker-packing-box))

-----

## Modes

The `DSFF` class can be instantiated using a mode of file operation. It works similarly to the native `file.open` function but with a more reduced set of modes. The following table indicates

Modes | r | r+ | w | w+
:----:|:-:|:--:|:-:|:--:
Read | * | * |  | *
Write |  | * | * | *
Create |  |  | * | *
Truncate |  |  | * | *

!!! note "Bound methods for conversions"

    When *Read* is available, the `to_*` (e.g. `to_arff`) methods are bound to the DSFF class. On the contrary, when *Write* is available, the `from_*` (e.g. `from_arff`) methods are bound to the DSFF class. As a consequence, the modes with "`+`" have both `to_*` and `from_*` methods attached.

The following pictures illustrate the available alternative formats and their applicable modes:

Converting from other formats to DSFF |  Converting from DSFF to other formats
:-------------------------------------------------------:|:-----------------------------------------------------:
![From alternative formats to DSFF](https://github.com/packing-box/python-dsff/raw/main/docs/pages/imgs/dsff-from.png) | ![From DSFF to alternative formats](https://github.com/packing-box/python-dsff/raw/main/docs/pages/imgs/dsff-to.png)

!!! warning "Lossy conversions"
    
    The following conversions only preserve the data (not the dictionary of features or metadata):
    
    - DSFF to [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html)
    - DSFF to [CSV](https://www.rfc-editor.org/rfc/rfc4180)

-----

## Usage

**Creating a DSFF from a FilelessDataset**

```python
>>> import dsff
>>> with dsff.DSFF() as f:
    f.write("/path/to/my-dataset")  # folder of a FilelessDataset (containing data.csv, features.json and metadata.json)
# while leaving the context, ./my-dataset.dsff is created
```

**Creating an [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html) file from a DSFF**

```python
>>> import dsff
>>> with dsff.DSFF("my-dataset.dsff") as f:
    f.to_arff()  # creates ./my-dataset.arff
```

**Creating a [CSV](https://www.rfc-editor.org/rfc/rfc4180) file from a DSFF**

```python
>>> import dsff
>>> with dsff.DSFF("my-dataset.dsff") as f:
    f.to_csv()  # creates ./my-dataset.csv
```

**Creating a FilelessDataset from a DSFF**

```python
>>> import dsff
>>> with dsff.DSFF("/path/to/my-dataset.dsff") as f:
    f.to_dataset()  # creates ./[dsff-title] with data.csv, features.json and metadata.json
```

