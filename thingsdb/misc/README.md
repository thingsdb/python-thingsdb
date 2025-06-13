# Lock

This lock provides distributed mutual exclusion, allowing you to synchronize
access to shared resources or critical sections of code across multiple
independent Python programs or services, even if they are running on different
machines.

It functions similarly to `asyncio.Lock()`, which is designed for concurrency
within a single process, but extends this capability to a multi-process,
multi-host environment by leveraging ThingsDB as its backend. This ensures that
only one client can acquire the lock at any given time, preventing race
conditions and maintaining data integrity in a distributed system.

The `timeout` parameter defines the maximum duration a lock can be held.
If a client fails to explicitly release the lock (e.g., due to a crash),
ThingsDB will automatically release it after this period, preventing deadlocks.
Separately, the expression `queue_size * timeout` indicates the total maximum
time a client will actively attempt to acquire the lock if it's currently
unavailable.

Example code:

```python
import asyncio
from functools import partial
from thingsdb.client import Client
from thingsdb.misc import lock


async def main():
    # ThingsDB client
    client = Client()

    # Multiple locks may be created, make sure you give each lock a unique name
    mylock = partial(lock.lock, client=client, name='my-lock', timeout=30)

    await client.connect('localhost')
    try:
        await client.authenticate('admin', 'pass')

        # This will set-up a lock collection
        # It will only do work the first time, but no harm in keep calling
        await lock.setup(client)

        # Wait for a lock
        async with mylock():
            print('In here')
            await asyncio.sleep(5.0)  # simulate some work
            print('Done here')

    finally:
        await client.close_and_wait()


if __name__ == '__main__':
    asyncio.run(main())
```

To observe the distributed lock in action, you can execute the example Python
script simultaneously in multiple separate terminal windows.

You can determine if a specific distributed lock is currently held by using
the `lock.locked()` asynchronous function.

To check the lock's status:

```python
is_locked = await lock.locked(client, 'my-lock')
```
