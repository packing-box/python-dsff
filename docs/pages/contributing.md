# Contributing

Contributions are welcome, for instance support for new formats.

## Reporting issues

Open an issue on [GitHub](https://github.com/packing-box/python-dsff/issues) and include:

- the DSFF version (`python -c "import dsff; print(dsff.__version__)"`);
- the code that triggers the issue and its output;
- if possible, a sample file.

## Security

Please do **not** report vulnerabilities in public issues. See the [security policy](https://github.com/packing-box/python-dsff/blob/main/SECURITY.md): report them privately through the repository's *Security* tab (*Report a vulnerability*).

Dependencies are monitored by Dependabot and audited with [pip-audit](https://github.com/pypa/pip-audit) by the `security` workflow (`.github/workflows/security.yml`), on every push and pull request to `main` and weekly.

## Adding a format

Add a module to `src/dsff/formats/` that defines `from_<format>`, `is_<format>`, `load_<format>` and `to_<format>` (see [How it works](internals.md#format-conversions)), list them in its `__all__` and import it in `src/dsff/formats/__init__.py`. The `from_*` and `to_*` functions are then bound to `DSFF` automatically.

## Development setup

```console
$ git clone https://github.com/packing-box/python-dsff
$ cd python-dsff
$ pip install -e .[all]
$ pip install pytest pytest-cov
$ pytest --cov=dsff
```

CI (`.github/workflows/python-package.yml`) runs the tests on Python 3.10 to 3.13 and publishes the coverage badge from the Python 3.13 run.

## Releasing

The version is stored in `src/dsff/VERSION.txt`. On every push to `main`, CI checks whether that version is already on PyPI. If not, it builds the package and publishes it.

## Building this documentation

```console
$ pip install -r docs/requirements.txt
$ mkdocs serve -f docs/mkdocs.yml          # live preview at http://127.0.0.1:8000
$ mkdocs build --strict -f docs/mkdocs.yml # what Read the Docs runs
```

Read the Docs builds the site from `.readthedocs.yaml` at the root of the repository.
