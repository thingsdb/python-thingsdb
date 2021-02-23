"""Decorator for handleing events."""


def event(ev):

    def _event(fun):
        fun._ev = ev
        return fun

    return _event
