# -*- coding: UTF-8 -*-
from .__common__ import *


__all__ = []


def _nowrite(m):
    raise NotImplementedError(f"none of {m}.write_table and {m}.write_{m} is implemented")


for module in ["feather", "orc", "parquet"]:
    __all__ += [f"from_{module}", f"to_{module}"]
    def gen_func(m):
        def from_(dsff, path=None, exclude=DEFAULT_EXCL):
            dataset = globals()[m].read_table(path)
            dsff.write(data=[dataset.schema.names] + [list(r.values()) for r in dataset.to_pylist()],
                       metadata=literal_eval(dataset.schema.metadata.pop(b'__metadata__', b"{}").decode()),
                       features={k.decode(): v.decode() for k, v in dataset.schema.metadata.items()})
        from_.__name__ = f"from_{m}"
        def to_(dsff, path=None, text=False):
            with (BytesIO() if text else open(path, 'wb+')) as f:
                getattr(globals()[m], "write_table", getattr(globals()[m], f"write_{m}", _nowrite))(dsff._to_table(), f)
                if text:
                    return f.getvalue()
        to_.__name__ = f"to_{m}"
        return from_, to_
    globals()[f'from_{module}'], globals()[f'to_{module}'] = gen_func(module)

