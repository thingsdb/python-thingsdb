import datetime
from typing import Union as U
from typing import Optional


class Buildin:

    #
    # Build-in functions from the @thingsdb scope
    #

    async def collection_info(self, collection: U[int, str]) -> dict:
        """Returns information about a specific collection.

        This function requires QUERY privileges on the requested collection,
        or CHANGE privileges on the @thingsdb scope.

        This function does not generate a change.
        """
        return await self.query(
            'collection_info(collection)',
            collection=collection,
            scope='@t')

    async def collections_info(self) -> list:
        """Returns collection information about all collections in ThingsDB.
        """
        return await self.query('collections_info()', scope='@t')

    async def del_collection(self, collection: U[int, str]):
        """Delete a collection.

        This function generates a change.
        """
        return await self.query(
            'del_collection(collection)',
            collection=collection,
            scope='@t')

    async def del_expired(self):
        """Delete all expired tokens.

        Requires GRANT privileges on the @thingsdb scope.

        This function generates a change.
        """
        return await self.query('del_expired()', scope='@t')

    async def del_module(self, name: str):
        """Delete a module. A SIGTERM signal will be send to the process for
        the module which might cancel running futures.

        This function generates a change.
        """
        return await self.query('del_module(key)', name=name, scope='@t')

    async def del_node(self, node_id: int):
        """Delete a node from ThingsDB.

        Before deleting a node, the node must be offline. As long is the node
        is active, you are not allowed to delete the node. See shutdown for
        shutting down a node by using a query.

        This function generates a change.
        """
        return await self.query('del_node(id)', id=node_id, scope='@t')

    async def del_token(self, key: str):
        """Delete a token.

        This function requires GRANT privileges on the @thingsdb scope unless
        the given token belongs to the logged on user. In the latter case,
        only CHANGE privileges are required.

        This function generates a change.
        """
        return await self.query('del_token(key)', key=key, scope='@t')

    async def del_user(self, name: str):
        """Delete a user.

        It is not possible to delete your own user account and a bad_data_err()
        will be raised in case you try to. Any tokens associated with the user
        will also be deleted.

        This function requires GRANT privileges on the @thingsdb scope.

        This function generates a change.
        """
        return await self.query('del_user(name)', name=name, scope='@t')

    async def deploy_module(
            self,
            name: str,
            data: Optional[U[bytes, str]] = None):
        """Deploy a module on all nodes.

        The module must be configured first, using the new_module() function.
        This function is used to write the module data (or plain python code)
        to the module. After deploying the code, the module will be restarted
        on every node.

        Before deploying a module, it is strongly recommended to use a
        development environment before deploying the module into production.

        When the `data` argument is None, no data will be overwritten but the
        module will be restarted on all nodes. This might be useful if you want
        to force a module restart on all nodes.

        This function generates a change.
        """
        return await self.query(
            'deploy_module(name, data)',
            name=name,
            data=data,
            scope='@t')

    async def grant(self, target: U[int, str], user: str, mask: int):
        """Grant, collection or general, privileges to a user.

        Access to a user is provided by setting a bit mask to either the @node,
        @thingsdb or a @collection scope.

        To use this function, at least CHANGE privileges on the @thingsdb scope
        and GRANT privileges on the target scope are required.

        It is not possible to set privileges on a specific node scope.
        Therefore scope @node will apply to all nodes in ThingsDB.

        The following pre-defined masks are available:
        (from thingsdb.util import Access)

        Mask	          | Description
        ----------------- | ------------
        Access.QUERY (1)  | Gives read access.
        Access.CHANGE (2) | Gives modify access.
        Access.GRANT (4)  | Gives modify and grant (and revoke) privileges.
        Access.JOIN (8)   | Gives join (and leave) privileges.
        Access.RUN (16)   | Gives run procedures access.
        Access.FULL (31)  | A mask for full privileges.

        It is not possible to have GRANT privileges without also having CHANGE
        privileges. However, ThingsDB automatically applies the required
        privileges so when setting for example GRANT privileges, ThingsDB makes
        sure that the user also gets CHANGE privileges.

        This function generates a change.
        """
        return await self.query(
            'grant(target, user, mask)',
            target=target,
            user=user,
            mask=mask,
            scope='@t')

    async def has_collection(self, name: str):
        """Determines if a collection exists in ThingsDB.

        This function does not generate a change.
        """
        return await self.query('has_collection(name)', name=name, scope='@t')

    async def has_module(self, name: str):
        """Determines if a module exists in ThingsDB.

        The scope restriction of the module has no impact on the result of this
        function.

        This function does not generate a change.
        """
        return await self.query('has_module(name)', name=name, scope='@t')

    async def has_node(self, node_id: int):
        """Determines if a node exists in ThingsDB.

        This function does not generate a change.
        """
        return await self.query('has_node(id)', id=node_id, scope='@t')

    async def has_token(self, token: str):
        """Determines if a token exists in ThingsDB.

        This function requires GRANT privileges on the @thingsdb scope.

        This function does not generate a change.
        """
        return await self.query('has_token(token)', token=token, scope='@t')

    async def has_user(self, name: str):
        """Determines if a user exists in ThingsDB.

        This function requires GRANT privileges on the @thingsdb scope.

        This function does not generate a change.
        """
        return await self.query('has_user(name)', name=name, scope='@t')

    async def module_info(self, name: str) -> dict:
        return await self.query('module_info(name)', name=name, scope='@t')

    async def modules_info(self) -> list:
        return await self.query('modules_info()', scope='@t')

    async def new_collection(self, name: str):
        """Create a new collection.

        This function generates a change.
        """
        return await self.query('new_collection(name)', name=name, scope='@t')

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
            'new_token(user, expiration_time, description)',
            user=user,
            expiration_time=expiration_time,
            description=description,
            scope='@t')

    async def new_user(self, name: str):
        """Creates a new user to ThingsDB. The new user is created without a
        password, token and access privileges. You probably want to set a
        password or add a new token, and assign some privileges using grant(…).

        This function requires GRANT privileges on the @thingsdb scope.

        This function generates a change.
        """
        return await self.query('new_user(name)', name=name, scope='@t')

    async def rename_collection(
            self,
            collection: U[int, str],
            new_name: str) -> None:
        return await self.query(
            'rename_collection(collection, new_name)',
            collection=collection,
            new_name=new_name,
            scope='@t')

    async def rename_module(self, name: str, new_name: str) -> None:
        return await self.query(
            'rename_module(name, new_name)',
            name=name,
            new_name=new_name,
            scope='@t')

    async def rename_user(self, name: str, new_name: str) -> None:
        return await self.query(
            'rename_user(name, new_name)',
            name=name,
            new_name=new_name,
            scope='@t')

    # TODO: restore

    async def revoke(self, target: U[int, str], user: str, mask: int):
        return await self.query(
            'revoke(target, user, mask)',
            target=target,
            user=user,
            mask=mask,
            scope='@t')

    # TODO: set_module_conf
    # TODO: set_module_scope

    async def set_password(self, user: str, new_password: str = None) -> None:
        return await self.query(
            'set_password(user, new_password)',
            user=user,
            new_password=new_password,
            scope='@t')

    async def set_time_zone(self, collection: U[int, str], zone: str):
        """By default each collection will be created with time zone UTC.

        This function can be used to change the time zone for a collection. If
        changed, the functions datetime(..) and timeval(..) will use the
        collections time zone unless specified otherwise. See time_zones_info()
        for a list of all available timezones.

        Use collection_info(..) to view the current time zone for a collection.

        This function generates a change.
        """
        return await self.query(
            'set_time_zone(collection, zone)',
            collection=collection,
            zone=zone,
            scope='@t')

    async def time_zones_info(self) -> list:
        """Returns all available time zones in ThingsDB.

        This function does not generate a change.
        """
        return await self.query('time_zones_info()', scope='@t')

    async def user_info(self, user: Optional[str] = None) -> dict:
        if user is None:
            return await self.query('user_info()', scope='@t')
        return await self.query('user_info(user)', user=user, scope='@t')

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

    async def node_info(self, scope='@n') -> dict:
        return await self.query('node_info()', scope=scope)

    async def nodes_info(self, scope='@n') -> list:
        return await self.query('nodes_info()', scope=scope)

    async def reset_counters(self, scope='@n') -> None:
        """Resets the counters for the ThingsDB node you are connected too.

        Other nodes are not affected. This will set the started_at counter
        value to the current UNIX time-stamp in seconds and all other counters
        to 0 (zero).

        This function does not generate a change.
        """
        return await self.query('reset_counters()', scope=scope)

    async def restart_module(self, name: str) -> None:
        """Restarts a given module on the select node scope.

        If you want to restart the module on all nodes, you can use the
        deploy_module(name, None) function with None as second argument.

        This function does not generate a change.
        """
        return await self.query('restart_module(name)', name=name, scope='@t')

    async def set_log_level(self, log_level: str, scope='@n') -> None:
        assert log_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        return await self.query(
            'set_log_level(log_level)', log_level=log_level, scope=scope)

    async def shutdown(self, scope='@n') -> None:
        """Shutdown the node in the selected scope.

        This is a clean shutdown, allowing all other nodes (and clients) to
        disconnect. Be CAREFUL using this function!!!

        At least CHANGE privileges on the @node scope are required to shutdown
        a node.

        This function does not generate a change.
        """
        return await self.query('shutdown()', scope=scope)
