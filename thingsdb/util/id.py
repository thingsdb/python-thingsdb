import warnings
from typing import Any, Optional

def id(val: Any) -> Optional[int]:
    warnings.warn(
        "do not use this function as it is not compatible with named Ids",
        DeprecationWarning,
        stacklevel=2
    )
    if isinstance(val, str) and val.startswith('room:'):
        try:
            id = int(val[5:])
            return id
        except Exception:
            return None
    assert isinstance(val, dict)
    return val.get('#')


if __name__ == '__main__':
    print(id('room:123'))
    print(id('room:nil'))
    print(id({'#': 123}))
    print(id({}))
