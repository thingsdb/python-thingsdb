import datetime
from typing import Union as U
from typing import Optional


class Buildin:

    #
    # Build-in functions from the @thingsdb scope
    #

    async def collection_info(self, collection: U[int, str]) -> dict:
        return await self.query(
            f'collection_info(collection)',
            collection=collection,
            scope='@t')

    async def collections_info(self):
        return await self.query('collections_info()', scope='@t')

    async def del_collection(self, collection: U[int, str]):
        return await self.query(
            f'del_collection(collection)',
            collection=collection,
            scope='@t')

    async def del_expired(self):
        return await self.query('del_expired()', scope='@t')

    async def del_module(self, name: str):
        return await self.query(f'del_module(key)', name=name, scope='@t')

    async def del_node(self, node_id: int):
        return await self.query(f'del_node(id)', id=node_id, scope='@t')

    async def del_token(self, key: str):
        return await self.query(f'del_token(key)', key=key, scope='@t')

    async def del_user(self, name: str):
        return await self.query(f'del_user(name)', name=name, scope='@t')

    # TODO: deploy module

    async def grant(self, target: U[int, str], user: str, mask: int):
        return await self.query(
            f'grant(target, user, mask)',
            target=target,
            user=user,
            mask=mask,
            scope='@t')

    async def has_collection(self, name: str):
        return await self.query(f'has_collection(name)', name=name, scope='@t')

    async def has_module(self, name: str):
        return await self.query(f'has_module(name)', name=name, scope='@t')

    async def has_node(self, node_id: int):
        return await self.query(f'has_node(id)', id=node_id, scope='@t')

    async def has_token(self, token: str):
        return await self.query(f'has_token(token)', token=token, scope='@t')

    async def has_user(self, name: str):
        return await self.query(f'has_user(name)', name=name, scope='@t')

    async def module_info(self, name: str) -> dict:
        return await self.query(f'module_info(name)', name=name, scope='@t')

    async def modules_info(self) -> list:
        return await self.query('modules_info()', scope='@t')

    async def new_collection(self, name: str):
        return await self.query(f'new_collection(name)', name=name, scope='@t')

    # TODO: new module
    # TODO: new node

    async def new_token(
            self,
            user: str,
            expiration_time: Optional[datetime.datetime] = None,
            description: str = ''):

        if expiration_time is not None:
            expiration_time = int(datetime.datetime.timestamp(expiration_time))

        return await self.query(
            f'new_token(user, expiration_time, description)',
            user=user,
            expiration_time=expiration_time,
            description=description,
            scope='@t')

    async def new_user(self, name: str):
        return await self.query(f'new_user(name)', name=name, scope='@t')

    async def rename_collection(
            self,
            collection: U[int, str],
            new_name: str) -> None:
        return await self.query(
            f'rename_collection(collection, new_name)',
            collection=collection,
            new_name=new_name,
            scope='@t')

    async def rename_module(self, name: str, new_name: str) -> None:
        return await self.query(
            f'rename_module(name, new_name)',
            name=name,
            new_name=new_name,
            scope='@t')

    async def rename_user(self, name: str, new_name: str) -> None:
        return await self.query(
            f'rename_user(name, new_name)',
            name=name,
            new_name=new_name,
            scope='@t')

    # TODO: restore

    async def revoke(self, target: U[int, str], user: str, mask: int):
        return await self.query(
            f'revoke(target, user, mask)',
            target=target,
            user=user,
            mask=mask,
            scope='@t')

    # TODO: set_module_conf
    # TODO: set_module_scope

    async def set_password(self, user: str, new_password: str = None) -> None:
        return await self.query(
            f'set_password(user, new_password)',
            user=user,
            new_password=new_password,
            scope='@t')

    async def set_time_zone(self, collection: U[int, str], zone: str):
        return await self.query(
            f'set_time_zone(collection, zone)',
            collection=collection,
            zone=zone,
            scope='@t')

    async def time_zones_info(self) -> list:
        return await self.query('time_zones_info()', scope='@t')

    async def user_info(self, user: Optional[str] = None) -> dict:
        if user is None:
            return await self.query('user_info()', scope='@t')
        return await self.query(f'user_info(user)', user=user, scope='@t')

    async def users_info(self) -> list:
        return await self.query('users_info()', scope='@t')

    #
    # Build-in functions from the @node scope
    #

    async def backup_info(self, backup_id: int, scope='@n'):
        return await self.query('backup_info(id)', id=backup_id, scope=scope)

    async def backups_info(self, scope='@n') -> list:
        return await self.query('backups_info()', scope=scope)

    async def counters(self, scope='@n'):
        return await self.query('counters()', scope=scope)

    async def del_backup(
            self,
            backup_id: int,
            delete_files: bool = False,
            scope='@n'):
        return await self.query(
            'del_backup(id, delete_files)',
            id=backup_id,
            delete_files=delete_files,
            scope=scope)

    async def has_backup(self, backup_id: int, scope='@n'):
        return await self.query('has_backup(id)', id=backup_id, scope=scope)

    # TODO: new_backup

    async def node_info(self, scope='@n'):
        return await self.query('node_info()', scope=scope)

    async def nodes_info(self, scope='@n') -> list:
        return await self.query('nodes_info()', scope=scope)

    async def reset_counters(self, scope='@n') -> None:
        return await self.query('reset_counters()', scope=scope)

    async def restart_module(self, name: str):
        return await self.query(f'restart_module(name)', name=name, scope='@t')

    async def set_log_level(self, log_level: str, scope='@n') -> None:
        assert log_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        return await self.query(
            f'set_log_level(log_level)', log_level=log_level, scope=scope)

    async def shutdown(self, scope='@n') -> None:
        return await self.query('shutdown()', scope=scope)
