# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = []


def _nowrite(m):
    raise NotImplementedError(f"none of {m}.write_table and {m}.write_{m} is implemented")


def _parse(ds):
    return {
        'data': [ds.schema.names] + [list(r.values()) for r in ds.to_pylist()],
        'features': {k.decode(): v.decode() for k, v in ds.schema.metadata.items()},
        'metadata': literal_eval(ds.schema.metadata.pop(b'__metadata__', b"{}").decode()),
    }


for module in ["feather", "orc", "parquet"]:
    __all__ += [f"from_{module}", f"is_{module}", f"load_{module}", f"to_{module}"]
    def gen_func(m):
        def from_(dsff, path=None, **kw):
            from os.path import basename, splitext
            dsff.write(**_parse(globals()[m].read_table(path)))
        from_.__name__ = f"from_{m}"
        def is_(data, **kw):
            try:
                globals()[m].read_table(pyarrow.BufferReader(data))
                return True
            except Exception:
                return False
        is_.__name__ = f"is_{m}"
        def load_(path, **kw):
            return _parse(globals()[m].read_table(path))
        load_.__name__ = f"load_{m}"
        def to_(dsff, path=None, text=False, **kw):
            with (BytesIO() if text else open(path, 'wb+')) as f:
                getattr(globals()[m], "write_table", getattr(globals()[m], f"write_{m}", _nowrite))(dsff._to_table(), f)
                if text:
                    return f.getvalue()
        to_.__name__ = f"to_{m}"
        return from_, text_or_path(is_), load_, to_
    globals()[f'from_{module}'], globals()[f'is_{module}'], globals()[f'load_{module}'], globals()[f'to_{module}'] = \
        gen_func(module)

