"""Keep data in sync between multiple services using ThingsDB.

Make sure you start with an empty collection and configure your token and
collection. (THINGSDB_AUTH_TOKEN and THINGSDB_COLLECTION)

Start the `bookstore.py` multiple times on different ports, for example:

python bookstore.py 5050
python bookstore.py 5051

Call the `add_book` handler on the one of the web servers (For example 5050)
```
curl \
    --location \
    --request POST 'http://127.0.0.1:5050/add_book' \
    --header 'Content-Type: application/json' \
    --data-raw '{"title": "A short history of nearly everything"}'
```

Observe that the book is synchronized with the other web server (5051):

```
curl \
    --location \
    --request GET 'http://127.0.0.1:5051/get_books'
```
"""
from sys import argv
from functools import partial
from asyncio import get_event_loop
from aiohttp import web
from thingsdb.client import Client
from thingsdb.room import Room, event

THINGSDB_AUTH_TOKEN = 'YOUR_TOKEN'
THINGSDB_COLLECTION = '//YOUR_COLLECTION'

bookstore = None


class BookStore(Room):

    def on_init(self):
        self.books = []
        self.add_book = partial(self.client.run, 'add_book')

    async def on_join(self):
        self.books = await self.client.query("""//ti
            .books;  // Just return all the books
        """)

    @event('add-book')
    def on_add_book(self, book):
        self.books.append(book)


def on_cleanup():
    client.close()
    return client.wait_closed()


async def add_book(request):
    book = await request.json()
    # Use the procedure to add the book
    await bookstore.add_book(book)
    return web.HTTPNoContent()


# We hve the books in memory
async def get_books(request):
    return web.json_response({
        "book_titles": [book['title'] for book in bookstore.books]
    })


async def setup(client):
    global bookstore

    await client.connect('playground.thingsdb.net', '9400')
    await client.authenticate(THINGSDB_AUTH_TOKEN)

    bookstore = BookStore("""//ti
        if (!has_type('Book')) {

            new_procedure('add_book', |book| {
                book = Book(book);
                .books.push(book);  // add the book to our books list
                .ev.emit('add-book', book);  // emit the add-book event
            });

            // Set-up the collection, this will run only the first time.
            set_type('Book', {
                title: 'str',
            });

            set_type('BookStore', {
                books: '[Book]',
                ev: 'room',
            });

            // Convert the collection to type BookStore. This works
            // only on an empty collection, if the collectoins is not empty
            // you can use .clear(); first to empty the collection.
            .to_type('BookStore');
        };

        .ev.id();  // Return the event room id
    """)
    await bookstore.join(client)


if __name__ == '__main__':
    port = int(argv[1])

    app = web.Application()

    # Handlers
    app.add_routes([
        web.post("/add_book", add_book),
        web.get("/get_books", get_books),
    ])

    client = Client(ssl=True)
    client.set_default_scope(THINGSDB_COLLECTION)

    loop = get_event_loop()
    loop.run_until_complete(setup(client))

    app.on_cleanup.append(lambda _: on_cleanup())
    web.run_app(app, port=port, loop=loop)
