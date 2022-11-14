<p align="center"><img src="https://github.com/packing-box/python-dsff/raw/main/docs/pages/imgs/logo.png"></p>
<h1 align="center">DataSet File Format <a href="https://twitter.com/intent/tweet?text=DataSet%20File%20Format%20-%20XSLX-based%20format%20for%20handling%20datasets.%0D%0ATiny%20library%20for%20handling%20a%20dataset%20as%20an%20XSLX%20and%20for%20converting%20it%20to%20ARFF,%20CSV%20or%20a%20FilelessDataset%20structure%20as%20for%20the%20Packing%20Box.%0D%0Ahttps%3a%2f%2fgithub%2ecom%2fpacking-box%2fpython-dsff%0D%0A&hashtags=python,dsff,machinelearning"><img src="https://img.shields.io/badge/Tweet--lightgrey?logo=twitter&style=social" alt="Tweet" height="20"/></a></h1>
<h3 align="center">Store a dataset in XSLX-like format.</h3>

[![PyPi](https://img.shields.io/pypi/v/dsff.svg)](https://pypi.python.org/pypi/dsff/)
[![Read The Docs](https://readthedocs.org/projects/python-dsff/badge/?version=latest)](https://python-dsff.readthedocs.io/en/latest/?badge=latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/dsff.svg)](https://pypi.python.org/pypi/dsff/)
[![Known Vulnerabilities](https://snyk.io/test/github/packing-box/python-dsff/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/packing-box/python-dsff?targetFile=requirements.txt)
[![License](https://img.shields.io/pypi/l/dsff.svg)](https://pypi.python.org/pypi/dsff/)


This library contains code for handling the DataSet File Format (DSFF) based on the XSLX format and for converting it to [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html) (for use with the [Weka](https://www.cs.waikato.ac.nz/ml/weka) framework), [CSV](https://www.rfc-editor.org/rfc/rfc4180) or a [FilelessDataset structure](https://docker-packing-box.readthedocs.io/en/latest/usage/datasets.html) (from the [Packing Box](https://github.com/packing-box/docker-packing-box)).

```sh
pip install --user dsff
```

## :sunglasses: Usage

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

## :star: Related Projects

You may also like these:

- [Awesome Executable Packing](https://github.com/packing-box/awesome-executable-packing): A curated list of awesome resources related to executable packing.
- [Dataset of packed ELF files](https://github.com/packing-box/dataset-packed-elf): Dataset of ELF samples packed with many different packers.
- [Dataset of packed PE files](https://github.com/packing-box/dataset-packed-pe): Dataset of PE samples packed with many different packers.
- [Docker Packing Box](https://github.com/packing-box/docker-packing-box): Docker image gathering packers and tools for making datasets of packed executables.


## :clap:  Supporters

[![Stargazers repo roster for @packing-box/python-dsff](https://reporoster.com/stars/dark/packing-box/python-dsff)](https://github.com/packing-box/python-dsff/stargazers)

[![Forkers repo roster for @packing-box/python-dsff](https://reporoster.com/forks/dark/packing-box/python-dsff)](https://github.com/packing-box/python-dsff/network/members)

<p align="center"><a href="#"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>

