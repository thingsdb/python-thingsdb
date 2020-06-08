"""Decorator for handleing events."""

def event(ev):

    def _event(fun):
        def wrapper(self, *args):
            fun(self, *args)

        wrapper._ev = ev
        return wrapper

    return _event
