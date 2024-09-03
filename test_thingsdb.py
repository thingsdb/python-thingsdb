import unittest
import asyncio
from thingsdb.client import Client


class TestPlayground(unittest.TestCase):

    async def async_test_playground(self):
        want = "Welcome at ThingsDB!"

        client = Client(ssl=True)

        await client.connect('playground.thingsdb.net', 9400)
        try:
            await client.authenticate('Fai6NmH7QYxA6WLYPdtgcy')
            data = await client.query(
                code='.greetings[index];',
                index=1,
                scope='//Doc')
            self.assertEqual(data, want)

        finally:
            await client.close_and_wait()

    def test_playground(self):
        asyncio.run(self.async_test_playground())


TestPlayground().test_playground()
