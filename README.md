[![CI](https://github.com/thingsdb/python-thingsdb/workflows/CI/badge.svg)](https://github.com/thingsdb/python-thingsdb/actions)
[![Release Version](https://img.shields.io/github/release/thingsdb/python-thingsdb)](https://github.com/thingsdb/python-thingsdb/releases)

# Python connector for ThingsDB

> This library requires Python 3.7 or higher.

---------------------------------------

  * [Installation](#installation)
  * [Quick usage](#quick-usage)
  * [Client](#client)
    * [authenticate](#authenticate)
    * [close](#close)
    * [close_and_wait](#close_and_wait)
    * [connect](#connect)
    * [connect_pool](#connect_pool)
    * [get_default_scope](#get_default_scope)
    * [get_event_loop](#get_event_loop)
    * [get_rooms](#get_rooms)
    * [is_connected](#is_connected)
    * [is_websocket](#is_websocket)
    * [query](#query)
    * [reconnect](#reconnect)
    * [run](#run)
    * [set_default_scope](#set_default_scope)
    * [wait_closed](#wait_closed)
  * [Room](#room)
    * [methods](#room-methods)
    * [properties](#room-properties)
    * [join](#join)
    * [leave](#leave)
    * [emit](#emit)
    * [no_join](#no_join)
  * [Failed packages](#failed-packages)
  * [WebSockets](#websockets)
---------------------------------------

## Installation

Just use pip:

```
pip install python-thingsdb
```

Or, clone the project and use setup.py:

```
python setup.py install
```

## Quick usage

```python
import asyncio
from thingsdb.client import Client

async def hello_world():
    client = Client()

    # replace `localhost` with your ThingsDB server address
    await client.connect('localhost')

    try:
        # replace `admin` and `pass` with your username and password
        # or use a valid token string
        await client.authenticate('admin', 'pass')

        # perform the hello world code...
        print(await client.query('''
            "Hello World!";
        '''))

    finally:
        # the will close the client in a nice way
        await client.close_and_wait()

# run the hello world example
asyncio.run(hello_world())
```

## Client

This is an client using `asyncio` which can be used for running queries to
ThingsDB.


```python
thingsdb.client.Client(
    auto_reconnect: bool = True,
    ssl: Optional[Union[bool, ssl.SSLContext]] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Client
```
Initialize a ThingsDB client

#### Args

- *auto_reconnect (bool, optional)*:
    When set to `True`, the client will automatically
    reconnect when a connection is lost. If set to `False` and the
    connection gets lost, one may call the [reconnect()](#reconnect) method to
    make a new connection. The auto-reconnect option will listen to
    node changes and automatically start a reconnect loop if the
    *shutting-down* status is received from the node.
    Defaults to `True`.
- *ssl (SSLContext or bool, optional)*:
    Accepts an ssl.SSLContext for creating a secure connection
    using SSL/TLS. This argument may simply be set to `True` in
    which case a context using `ssl.PROTOCOL_TLS` is created.
    Defaults to `None`.
- *loop (AbstractEventLoop, optional)*:
    Can be used to run the client on a specific event loop.
    If this argument is not used, the default event loop will be
    used. Defaults to `None`.

### authenticate

```python
async Client().authenticate(
    *auth: Union[str, tuple],
    timeout: Optional[int] = 5
) -> None
```

Authenticate a ThingsDB connection.

#### Args

- *\*auth (str or (str, str))*:
    Argument `auth` can be be either a string with a token or a
    tuple with username and password. (the latter may be provided
    as two separate arguments
- *timeout (int, optional)*:
    Can be be used to control the maximum time in seconds for the
    client to wait for response on the authentication request.
    The timeout may be set to `None` in which case the client will
    wait forever on a response. Defaults to 5.

### close

```python
Client().close() -> None
```

Close the ThingsDB connection.

This method will return immediately so the connection may not be
closed yet after a call to `close()`. Use the [wait_closed()](#wait_closed) method
after calling this method if this is required.

### close_and_wait

```python
async Client().close_and_wait() -> None
```

Close and wait for the the connection to be closed.

This is equivalent of combining [close()](#close)) and [wait_closed()](#wait_closed).

### connect

```python
Client().connect(
    host: str,
    port: int = 9200,
    timeout: Optional[int] = 5
) -> asyncio.Future
```

Connect to ThingsDB.

This method will *only* create a connection, so the connection is not
authenticated yet. Use the [authenticate(..)](#authenticate) method after creating a
connection before using the connection.

#### Args

- *host (str)*:
    A hostname, IP address, FQDN or URI _(for WebSockets)_ to connect to.
- *port (int, optional)*:
    Integer value between 0 and 65535 and should be the port number
    where a ThingsDB node is listening to for client connections.
    Defaults to 9200. For WebSocket connections the port must be
    provided with the URI _(see host argument)_.
- *timeout (int, optional)*:
    Can be be used to control the maximum time the client will
    attempt to create a connection. The timeout may be set to
    `None` in which case the client will wait forever on a
    response. Defaults to 5.

### Returns

Future which should be awaited. The result of the future will be
set to `None` when successful.

> Do not use this method if the client is already
> connected. This can be checked with `client.is_connected()`.

### connect_pool

```python
Client().connect_pool(
    pool: list,
    *auth: Union[str, tuple]
) -> asyncio.Future
```

Connect using a connection pool.

When using a connection pool, the client will randomly choose a node
to connect to. When a node is going down, it will inform the client
so it will automatically re-connect to another node. Connections will
automatically authenticate so the connection pool requires credentials
to perform the authentication.

#### Examples

```python
await connect_pool([
    'node01.local',             # address or WebSocket URI as string
    'node02.local',             # port will default to 9200 or ignored for URI
    ('node03.local', 9201),     # ..or with an explicit port (ignored for URI)
], "admin", "pass")
```

#### Args

- *pool (list of addresses)*:
    Should be an iterable with node address strings, or tuples
    with `address` and `port` combinations in a tuple or list. For WebSockets,
    the address must be an URI with the port included. (e.g: `"ws://host:9270"`)
- *\*auth (str or (str, str))*:
    Argument `auth` can be be either a string with a token or a
    tuple with username and password. (the latter may be provided
    as two separate arguments

### Returns

Future which should be awaited. The result of the future will be
set to `None` when successful.

> Do not use this method if the client is already
> connected. This can be checked with `client.is_connected()`.


### get_default_scope

```python
Client().get_default_scope() -> str
```

Get the default scope.

The default scope may be changed with the [set_default_scope()](#set_default_scope) method.

#### Returns

The default scope which is used by the client when no specific scope is specified.


### get_event_loop

```python
Client().get_event_loop() -> asyncio.AbstractEventLoop
```

Can be used to get the event loop.

#### Returns

The event loop used by the client.

### get_rooms

```python
Client().get_rooms() -> tuple
```

Can be used to get the rooms which are joined by this client.

#### Returns

A `tuple` with unique `Room` instances.

### is_connected

```python
Client().is_connected() -> bool
```

Can be used to check if the client is connected.

#### Returns
`True` when the client is connected else `False`.


### is_websocket

```python
Client().is_websocket() -> bool
```

Can be used to check if the client is using a WebSocket connection.

#### Returns
`True` when the client is connected else `False`.

### query

```python
Client().query(
        code: str,
        scope: Optional[str] = None,
        timeout: Optional[int] = None,
        skip_strip_code: bool = False,
        **kwargs: Any
) -> asyncio.Future
```

Query ThingsDB.

Use this method to run `code` in a scope.

#### Args

- *code (str)*:
    ThingsDB code to run.
- *scope (str, optional)*:
    Run the code in this scope. If not specified, the default scope
    will be used. See https://docs.thingsdb.net/v0/overview/scopes/
    for how to format a scope.
- *timeout (int, optional)*:
    Raise a time-out exception if no response is received within X
    seconds. If no time-out is given, the client will wait forever.
    Defaults to `None`.
- *skip_strip_code (bool, optional)*:
    This can be set to `True` which can be helpful when line numbers
    in syntax errors need to match. When `False`, the code will be
    stripped from white-space and comments to reduce the code size.
- *\*\*kwargs (any, optional)*:
    Can be used to inject variable into the ThingsDB code.

#### Examples

Although we could just as easy have wrote everything in the
ThingsDB code itself, this example shows how to use **kwargs for
injecting variable into code. In this case the variable `book`.

```python
res = await client.query(".my_book = book;", book={
    'title': 'Manual ThingsDB'
})
```

#### Returns

Future which should be awaited. The result of the future will
contain the result of the ThingsDB code when successful.

> If the ThingsDB code will return with an exception, then this
> exception will be translated to a Python Exception which will be
> raised. See thingsdb.exceptions for all possible exceptions and
> https://docs.thingsdb.net/v0/errors/ for info on the error codes.

### reconnect

```python
async Client().reconnect() -> Optional[Future]
```

Re-connect to ThingsDB.

This method can be used, even when a connection still exists. In case
of a connection pool, a call to `reconnect()` will switch to another
node. If the client is already re-connecting, this method returns `None`,
otherwise, the reconnect `Future` is returned, await of the Future is
possible but not required.

### run

```python
Client().run(
    procedure: str,
    *args: Optional[Any],
    scope: Optional[str] = None,
    timeout: Optional[int] = None,
    **kwargs: Any
) -> asyncio.Future
```

Run a procedure.

Use this method to run a stored procedure in a scope.

#### Args

- *procedure (str)*:
    Name of the procedure to run.
- *\*args (any)*:
    Arguments which are injected as the procedure arguments.
    Instead of positional, the arguments may also be parsed using
    keyword arguments but not both at the same time.
- *scope (str, optional)*:
    Run the procedure in this scope. If not specified, the default
    scope will be used.
    See https://docs.thingsdb.net/v0/overview/scopes/ for how to
    format a scope.
- *timeout (int, optional)*:
    Raise a time-out exception if no response is received within X
    seconds. If no time-out is given, the client will wait forever.
    Defaults to `None`.
- *\*\*kwargs (any, optional)*:
     Arguments which are injected as the procedure arguments.
    Instead of by name, the arguments may also be parsed using
    positional arguments but not both at the same time.

#### Returns

Future which should be awaited. The result of the future will
contain the result of the ThingsDB procedure when successful.


> If the ThingsDB code will return with an exception, then this
> exception will be translated to a Python Exception which will be
> raised. See thingsdb.exceptions for all possible exceptions and
> https://docs.thingsdb.net/v0/errors/ for info on the error codes.


### set_default_scope

```python
Client().set_default_scope(scope: str) -> None
```

Set the default scope.

Can be used to change the default scope which is initially set to `@t`.

#### Args
- *scope (str)*:
    Set the default scope. A scope may start with either the `/`
    character, or `@`. Examples: `"//stuff"`, `"@:stuff"`, `"/node"`


### wait_closed

```python
async Client().wait_closed() -> None
```

Wait for a connection to close.

Can be used after calling the `close()` method to determine when the
connection is actually closed.


## Room

Rooms can be implemented to listen for events from ThingsDB rooms.

Se the example code:

```python
from thingsdb.room import Room, event

class Chat(Room):

    @event('msg')
    def on_msg(self, msg):
        print(msg)

```

This will listen for `msg` events on a ThingsDB room. To connect out class to a
room, you have to initialize the class with a `roomId` of some ThingsDB code which
returns the `roomId` as integer value. For example:

```python
# Create a chat instance. In this example we initialize our chat with some ThingsDB code
chat = Chat("""//ti
    // Create .chat room if the room does not exist.
    .has('chat') || .chat = room();

    // return the roomId.
    .chat.id();
""")

# Now we can join the room. (we assume that you have a ThingsDB client)
await chat.join(client)
```

#### Room Init Args
- *room (int/str)*:
    The room Id or ThingsDB code which returns the Id of the room.
    Examples are `123`, `'.my_room.id();'`
- *scope (str)*:
    Collection scope. If no scope is given, the scope will later
    be set to the default client scope once the room is joined.


## Room Methods

Besides implementing an `@event` handler, a room has also some methods which can be implemented to control or initialize a room.

### on_init(self) -> None
Called when a room is joined. This method will be called only once,
thus *not* after a re-connect like the `on_join(..)` method. This
method is guaranteed to be called *before* the `on_join(..)` method.

### on_join(self) -> None:
Called when a room is joined. Unlike the `on_init(..)` method,
the `on_join(..)` method will be called again after a re-connect.

This is an async method and usually the best method to perform
some ThingsDB queries (if required).

Unless the `wait` argument to the Room.join(..) function is explicitly
set to `0` or `None`, the first call to this method will finish before the
call to `Room.join()` is returned.

### on_leave(self) -> None:
Called after a leave room request. This event is *not* triggered
by ThingsDB when a client disconnects or when a node is shutting down.

### on_delete(self) -> None:
Called when the room is removed from ThingsDB.

### on_emit(self, event: str, *args) -> None:
Called when no event handler is configured for the event.
By default, the `on_emit` will display a "debug" log message when called to
show that no handler for the event is found.

## Room Properties

The following properties are available on a room instance. Note that some properties
might return `None` as long as a room is not joined.

Property | Description
-------- | -----------
`id`     | Returns the roomId.
`scope`  | Returns the scope of the room.
`client` | Returns the associated client of the room.

### join

```python
Room().join(client: Client, wait: Optional[float] = 60.0) -> None
```

Joins the room.

#### Args
- client *(thingsdb.client.Client)*:
        ThingsDB client instance.
- wait *(float)*:
    Max time (in seconds) to wait for the first `on_join` call.
    If wait is set to `0` or `None`, the join method will not wait for
    the first `on_join` call to happen.


### leave

```python
Room().leave() -> None
```

Leave the room. If the room is not found, a `LookupError` will be raised.

### emit

```python
Room().emit(event: str, *args: Optional[Any],) -> asyncio.Future
```

Emit an event to a room.

#### Args

- *event (str)*:
    Name of the event to emit.
- *\*args (any)*:
    Additional argument to send with the event.

#### Returns

Future which should be awaited. The result of the future will
be set to `None` when successful.

### no_join

```python
Room().no_join(client: Client) -> None
```

Only translate the code _(or test the Id)_ to a room Id. This is useful if you only
want to use the room to emit events and not listen to events.

#### Args
- client *(thingsdb.client.Client)*:
        ThingsDB client instance.


## Failed packages

```python
set_package_fail_file(fn: str = '') -> None
```

Configure a file name to dump the last failed package.

Only the MessagePack data will be stored in this file, not the package
header. This is useful for debugging packages which fail to unpack.
Note that only a single fail file can be used which is active (or not) for
all clients.

When empty (`''`), a failed package will *not* be dumped to file.

```python
from thingsdb.client import set_package_fail_file

set_package_fail_file('/tmp/thingsdb-invalid-data.mp')

# When a package is received which fails to unpack, the data from this package
# will be stored to file.
```


## WebSockets

Since ThingsDB 1.6 has received WebSocket support. The Python client is able to use the WebSockets protocol by providing the `host` as URI.
For WebSocket connections,the `port` argument will be ignored and must be specified with the URI instead.

Default the `websockets` package is **not included** when installing this connector.

If you want to use WebSockets, make sure to install the package:

```
pip install websockets
```

For example:

```python
import asyncio
from thingsdb.client import Client

async def hello_world():
    client = Client()

    # replace `ws://localhost:9270` with your URI
    await client.connect('ws://localhost:9270')

    # for a secure connection, use wss:// and provide an SSL context, example:
    # (ssl can be set either to True or False, or an SSLContext)
    #
    #   client = Client(ssl=True)
    #   await client.connect('wss://localhost:9270')

    try:
        # replace `admin` and `pass` with your username and password
        # or use a valid token string
        await client.authenticate('admin', 'pass')

        # perform the hello world code...
        print(await client.query('''
            "Hello World!";
        ''')

    finally:
        # the will close the client in a nice way
        await client.close_and_wait()

# run the hello world example
asyncio.run(hello_world())
```
