import enum


class Access(enum.IntEnum):
    QUERY = 0x01
    CHANGE = 0x02
    GRANT = 0x04
    JOIN = 0x08
    RUN = 0x10
    FULL = 0x1f
