import asyncio
from thingsdb.client import Client
from thingsdb.model import Collection, Thing, ThingStrict, Enum


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
        await asyncio.sleep(100)

    finally:
        client.close()
        await client.wait_closed()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
