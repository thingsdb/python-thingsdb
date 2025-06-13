import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from ..client import Client
from ..room import Room, event


async def setup(client: Client, collection: str = 'lock'):
    has_collection = await client.query("""//ti
        has_collection(name);
    """, name=collection, scope='/t')

    if has_collection:
        return

    await client.query("""//ti
        new_collection(name);
    """, name=collection, scope='/t')

    await client.query("""//ti

        set_type('Inner', {
            room: 'room',
            task: 'task',
            timeout: 'int',
            set_task: |this, lock_id| {
                this.task = task(
                    datetime().move('seconds', this.timeout),
                    |_, lock_id, room_id| wse(Lock(lock_id).release(room_id)),
                    [lock_id, this.room.id()],
                );
                nil;
            },
        });

        set_type('Lock', {
            queue: '[Inner]',
            go: |this| {
                if (!this.queue) return nil;
                inner = this.queue.first();
                inner.set_task(this.id());
                inner.room.set_name('go');
                inner.room.emit('go');
            },
            acquire: |this, timeout| {
                size = this.queue.len();
                immediately = size == 0;
                inner = Inner{timeout:,};
                this.queue.push(inner);
                immediately && inner.set_task(this.id());
                [immediately, inner.room.id(), size];
            },
            release: |this, room_id| try({
                if (this.queue.first().room.id() == room_id) {
                    this.queue.first().task.del();
                    this.queue.shift();
                    this.go();
                } else {
                    this.queue
                        .remove(|inner| inner.room.id() == room_id)
                        .each(|inner| inner.task.del());
                };
                nil;
            }),
        });

        set_type('Root', {
            lock: 'thing<Lock>',
            version: 'int'
        });

        new_procedure('acquire', |name, timeout| {
            .lock.get(name, .lock[name] = Lock{}).acquire(timeout);
        });

        new_procedure('test', |room_id| {
            room(room_id).name() == 'go';
        });

        new_procedure('locked', |name| {
            bool(.lock[name].queue);
        });

        new_procedure('release', |name, room_id| {
            wse(.lock[name].release(room_id));
        });

        .to_type('Root');
    """, scope=f'//{collection}')


class _InnerRoom(Room):

    future: asyncio.Future

    def on_init(self) -> None:
        self.future = asyncio.Future()

    async def on_join(self) -> None:
        # We might have missed the event during the join. If so, set the
        # future result to continue.
        ok = await self.client.run('test', self.id, scope=self.scope)
        if ok and not self.future.done():
            self.future.set_result(None)

    @event('go')
    def on_go(self):
        if not self.future.done():
            self.future.set_result(None)


@asynccontextmanager
async def lock(client: Client, name: str,
               scope: str = '//lock',
               timeout: int = 60) -> AsyncGenerator[int, None]:

    res: tuple[bool, int, int] = \
        await client.run('acquire', name, timeout, scope=scope)

    immediately, room_id, size = res
    if not immediately:
        room = _InnerRoom(room_id, scope=scope)
        await room.join(client, wait=None)
        try:
            await asyncio.wait_for(room.future, timeout=timeout*size)
        except asyncio.TimeoutError:
            pass

    try:
        yield room_id  # Lock Id assigned to the 'as' target (not required)
    finally:
        await client.run('release', name, room_id, scope=scope)


async def locked(client: Client, name: str, scope: str = '//lock') -> bool:
    res: bool = await client.run('locked', name, scope=scope)
    return res
