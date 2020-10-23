import datetime
from typing import Union as U


class Buildin:

    async def collection_info(self, collection: U[int, str]) -> dict:
        return await self.query(
            f'collection_info({collection!r})',
            scope='@t')

    async def collections_info(self):
        return await self.query('collections_info()', scope='@t')

    async def counters(self, scope='@n'):
        return await self.query('counters()', scope=scope)

    async def del_collection(self, collection: U[int, str]):
        return await self.query(
            f'del_collection({collection!r})',
            scope='@t')

    async def del_expired(self):
        return await self.query('del_expired()', scope='@t')

    async def del_token(self, key: str):
        return await self.query(f'del_token({key!r})', scope='@t')

    async def del_user(self, name: str):
        return await self.query(f'del_user({name!r})', scope='@t')

    async def grant(self, target: U[int, str], user: str, mask: int):
        return await self.query(
            f'grant({target!r}, {user!r}, {mask})',
            scope='@t')

    async def has_collection(self, name: str):
        return await self.query(f'has_collection({name!r})', scope='@t')
    
    async def has_token(self, token: str):
        return await self.query(f'has_token({token!r})', scope='@t')

    async def has_user(self, name: str):
        return await self.query(f'has_user({name!r})', scope='@t')

    async def new_collection(self, name: str):
        return await self.query(f'new_collection({name!r})', scope='@t')

    async def new_token(
            self,
            user: str,
            expiration_time: datetime.datetime = None,
            description: str = ''):

        if expiration_time is None:
            expiration_time = 'nil'
        else:
            expiration_time = int(datetime.datetime.timestamp(expiration_time))

        return await self.query(
            f'new_token({user!r}, {expiration_time}, {description!r})',
            scope='@t')
    
    async def new_user(self, name: str):
        return await self.query(f'new_user({name!r})', scope='@t')

    async def node_info(self, scope='@n'):
        return await self.query('node_info()', scope=scope)

    async def nodes_info(self, scope='@n') -> list:
        return await self.query('nodes_info()', scope=scope)
    
    async def rename_collection(
        self, 
        collection: U[int, str], 
        new_name: str) -> None:
        return await self.query(
            f'rename_collection({collection!r}, {new_name!r})', scope='@t')

    async def rename_user(self, user: str, new_name: str) -> None:
        return await self.query(
            f'rename_user({user!r}, {new_name!r})', scope='@t')

    async def reset_counters(self, scope='@n') -> None:
        return await self.query('reset_counters()', scope=scope)

    async def revoke(self, target: U[int, str], user: str, mask: int):
        return await self.query(
            f'grant({target!r}, {user!r}, {mask})',
            scope='@t')

    async def set_log_level(self, log_level: str, scope='@n') -> None:
        assert log_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        return await self.query(f'set_log_level({log_level})', scope=scope)
    
    async def set_password(self, user: str, new_password: str = None) -> None:
        if new_password is None:
            new_password = 'nil'
        return await self.query(
            f'set_password({user!r}, {new_password!r})', scope='@t')

    async def shutdown(self, scope='@n') -> None:
        return await self.query('shutdown()', scope=scope)

    async def user_info(self, user: str = None) -> dict:
        if user is None:
            return await self.query('user_info()', scope='@t')
        return await self.query(f'user_info({user!r})', scope='@t')

    async def users_info(self) -> list:
        return await self.query('users_info()', scope='@t')
