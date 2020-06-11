import asyncio
from thingsdb.client import Client
from thingsdb.model import Collection, Thing, ThingStrict, Enum
from thingsdb.util import event


class Color(Enum):
    RED = "#f00"
    BLUE = "#0f0"
    GREEN = "#00f"


class Brick(Thing):
    color = 'Color', Color

    def on_init(self, *args, **kwars):
        super().on_init(*args, **kwars)
        print(f'''
        Init Brick:
            id: {self.id()}
            color name: {self.color.name}
            color value: {self.color.value}
        ''')

    def on_update(self, event, jobs):
         super().on_update(event, jobs)
         print('ON BOOK UPDATE (Color: {}'.format(self.color))

    @event('new-color')
    def on_new_color(self, color):
        print(f'brick with id {self.id()} as a new color: {color}')


class Lego(Collection):
    bricks = '[Brick]', Brick


async def example():
    client = Client()
    lego = Lego()
    await client.connect('localhost')
    try:
        await client.authenticate('admin', 'pass')
        try:
            await lego.build(
                client,
                scripts=['.bricks = [];'],
                delete_if_exists=False)
        except KeyError:
            pass
        await lego.load(client)

        # ... now the collection will be watched for 100 seconds
        while True:
            await asyncio.sleep(3)
            if lego and lego.bricks:
                brick = lego.bricks[0]
                await brick.emit('new-color', 'RED')
                break
            await lego.query('.bricks.push(Brick{});')

        await asyncio.sleep(300)

    finally:
        client.close()
        await client.wait_closed()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
