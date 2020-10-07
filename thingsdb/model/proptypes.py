import re
import functools
import logging


class PropTypes:

    @staticmethod
    def any_(v, klass, collection):
        if isinstance(v, dict):
            if '#' in v:
                return PropTypes.thing_(v, klass, collection)
            if '%' in v:
                return collection._get_enum_member(*v['%'])
            if '$' in v:
                return PropTypes.set_(v, nested=functools.partial(
                    PropTypes.thing_,
                    klass=klass,
                    collection=collection
                ))
            if '*' in v:
                pattern = v['*']
                flags = 0
                if pattern.endswith('i'):
                    flags |= re.IGNORECASE
                    pattern = pattern[:-2]
                else:
                    pattern = pattern[1:-1]
                return re.compile(pattern, flags)
            if '!':
                msg = v['error_msg']
                # TODO : Return correct exception
                return Exception(msg)
            logging.warning(f'unhandled dict: {v}')
        if isinstance(v, list):
            return PropTypes.array_(v, nested=functools.partial(
                PropTypes.any_,
                klass=klass,
                collection=collection
            ))
        return v

    @staticmethod
    def thing_(v, klass, collection, watch=False):
        if not isinstance(v, dict):
            raise TypeError(f'expecting type `dict`, got `{type(v)}`')

        thing_id = v.pop('#')
        thing = collection._things.get(thing_id)

        if thing is None:
            thing = klass(collection, thing_id)
        else:
            watch = False

        type_id = v.pop('.', None)
        if type_id is None:
            thing.__dict__.update(v)
        else:
            fmap = collection._types.get(type_id)
            if fmap:
                thing.__dict__.update(zip(fmap, v['']))

        if watch and not thing:
            collection._add_pending(thing)

        return thing

    @staticmethod
    def enum_(v, collection):
        return collection._get_enum_member(*v['%'])

    @staticmethod
    def str_(v):
        if not isinstance(v, str):
            raise TypeError(f'expecting type `str`, got `{type(v)}`')
        return v

    @staticmethod
    def utf8_(v):
        if not isinstance(v, str):
            raise TypeError(f'expecting type `str`, got `{type(v)}`')
        return v

    @staticmethod
    def bytes_(v):
        if not isinstance(v, bytes):
            raise TypeError(f'expecting type `bytes`, got `{type(v)}`')
        return v

    @staticmethod
    def raw_(v, _types=(str, bytes)):
        if not isinstance(v, _types):
            raise TypeError(f'expecting type `bytes`, got `{type(v)}`')
        return v

    @staticmethod
    def bool_(v):
        if not isinstance(v, bool):
            raise TypeError(f'expecting type `bool`, got `{type(v)}`')
        return v

    @staticmethod
    def int_(v):
        if not isinstance(v, int):
            raise TypeError(f'expecting type `int`, got `{type(v)}`')
        return v

    @staticmethod
    def uint_(v):
        if not isinstance(v, int):
            raise TypeError(f'expecting type `int`, got `{type(v)}`')
        if v < 0:
            raise ValueError(f'expecting an integer value >= 0, got {v}')
        return v

    @staticmethod
    def pint_(v):
        if not isinstance(v, int):
            raise TypeError(f'expecting type `int`, got `{type(v)}`')
        if v <= 0:
            raise ValueError(f'expecting an integer value > 0, got {v}')
        return v

    @staticmethod
    def nint_(v):
        if not isinstance(v, int):
            raise TypeError(f'expecting type `int`, got `{type(v)}`')
        if v >= 0:
            raise ValueError(f'expecting an integer value < 0, got {v}')
        return v

    @staticmethod
    def float_(v):
        if not isinstance(v, float):
            raise TypeError(f'expecting type `float`, got `{type(v)}`')
        return v

    @staticmethod
    def number_(v):
        if not isinstance(v, (float, int)):
            raise TypeError(
                f'expecting type `int` or `float`, got `{type(v)}`')
        return v

    @staticmethod
    def array_(v, nested):
        if not isinstance(v, list):
            raise TypeError(f'expecting a `list`, got `{type(v)}`')
        return [nested(item) for item in v]

    @staticmethod
    def set_(v, nested):
        if not isinstance(v, dict):
            raise TypeError(f'expecting a `dict`, got `{type(v)}`')
        v = v['$']
        return {nested(item) for item in v}

    @staticmethod
    def nillable(v, func=None):
        return v if v is None else func(v)
