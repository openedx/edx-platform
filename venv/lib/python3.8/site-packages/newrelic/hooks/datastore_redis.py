# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from newrelic.api.datastore_trace import DatastoreTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper

_redis_client_methods = (
    "bgrewriteaof",
    "bgsave",
    "client_kill",
    "client_list",
    "client_getname",
    "client_setname",
    "config_get",
    "config_set",
    "config_resetstat",
    "config_rewrite",
    "dbsize",
    "debug_object",
    "echo",
    "flushall",
    "flushdb",
    "info",
    "lastsave",
    "object",
    "ping",
    "save",
    "sentinel",
    "sentinel_get_master_addr_by_name",
    "sentinel_master",
    "sentinel_masters",
    "sentinel_monitor",
    "sentinel_remove",
    "sentinel_sentinels",
    "sentinel_set",
    "sentinel_slaves",
    "shutdown",
    "slaveof",
    "slowlog_get",
    "slowlog_reset",
    "time",
    "append",
    "bitcount",
    "bitop",
    "bitpos",
    "decr",
    "delete",
    "dump",
    "exists",
    "expire",
    "expireat",
    "get",
    "getbit",
    "getrange",
    "getset",
    "incr",
    "incrby",
    "incrbyfloat",
    "keys",
    "mget",
    "mset",
    "msetnx",
    "move",
    "persist",
    "pexpire",
    "pexpireat",
    "psetex",
    "pttl",
    "randomkey",
    "rename",
    "renamenx",
    "restore",
    "set",
    "setbit",
    "setex",
    "setnx",
    "setrange",
    "strlen",
    "substr",
    "ttl",
    "type",
    "watch",
    "unwatch",
    "blpop",
    "brpop",
    "brpoplpush",
    "lindex",
    "linsert",
    "llen",
    "lpop",
    "lpush",
    "lpushx",
    "lrange",
    "lrem",
    "lset",
    "ltrim",
    "rpop",
    "rpoplpush",
    "rpush",
    "rpushx",
    "sort",
    "scan",
    "scan_iter",
    "sscan",
    "sscan_iter",
    "hscan",
    "hscan_inter",
    "zscan",
    "zscan_iter",
    "sadd",
    "scard",
    "sdiff",
    "sdiffstore",
    "sinter",
    "sinterstore",
    "sismember",
    "smembers",
    "smove",
    "spop",
    "srandmember",
    "srem",
    "sunion",
    "sunionstore",
    "zadd",
    "zcard",
    "zcount",
    "zincrby",
    "zinterstore",
    "zlexcount",
    "zrange",
    "zrangebylex",
    "zrangebyscore",
    "zrank",
    "zrem",
    "zremrangebylex",
    "zremrangebyrank",
    "zremrangebyscore",
    "zrevrange",
    "zrevrangebyscore",
    "zrevrank",
    "zscore",
    "zunionstore",
    "pfadd",
    "pfcount",
    "pfmerge",
    "hdel",
    "hexists",
    "hget",
    "hgetall",
    "hincrby",
    "hincrbyfloat",
    "hkeys",
    "hlen",
    "hset",
    "hsetnx",
    "hmset",
    "hmget",
    "hvals",
    "publish",
    "eval",
    "evalsha",
    "script_exists",
    "script_flush",
    "script_kill",
    "script_load",
    "setex",
    "lrem",
    "zadd",
)

_redis_multipart_commands = set(["client", "cluster", "command", "config", "debug", "sentinel", "slowlog", "script"])

_redis_operation_re = re.compile(r"[-\s]+")


def _conn_attrs_to_dict(connection):
    return {
        "host": getattr(connection, "host", None),
        "port": getattr(connection, "port", None),
        "path": getattr(connection, "path", None),
        "db": getattr(connection, "db", None),
    }


def _instance_info(kwargs):
    host = kwargs.get("host") or "localhost"
    port_path_or_id = str(kwargs.get("port") or kwargs.get("path", "unknown"))
    db = str(kwargs.get("db") or 0)

    return (host, port_path_or_id, db)


def _wrap_Redis_method_wrapper_(module, instance_class_name, operation):
    def _nr_wrapper_Redis_method_(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        dt = DatastoreTrace(product="Redis", target=None, operation=operation)

        transaction._nr_datastore_instance_info = (None, None, None)

        with dt:
            result = wrapped(*args, **kwargs)

            host, port_path_or_id, db = transaction._nr_datastore_instance_info
            dt.host = host
            dt.port_path_or_id = port_path_or_id
            dt.database_name = db

            return result

    name = "%s.%s" % (instance_class_name, operation)
    wrap_function_wrapper(module, name, _nr_wrapper_Redis_method_)


def instrument_redis_client(module):
    if hasattr(module, "StrictRedis"):
        for name in _redis_client_methods:
            if name in vars(module.StrictRedis):
                _wrap_Redis_method_wrapper_(module, "StrictRedis", name)

    if hasattr(module, "Redis"):
        for name in _redis_client_methods:
            if name in vars(module.Redis):
                _wrap_Redis_method_wrapper_(module, "Redis", name)


def instrument_redis_commands_core(module):
    for name in _redis_client_methods:
        if hasattr(module, "CoreCommands"):
            if hasattr(module.CoreCommands, name):
                _wrap_Redis_method_wrapper_(module, "CoreCommands", name)
        if hasattr(module, "DataAccessCommands"):
            if hasattr(module.DataAccessCommands, name):
                _wrap_Redis_method_wrapper_(module, "DataAccessCommands", name)


def _nr_Connection_send_command_wrapper_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None or not args:
        return wrapped(*args, **kwargs)

    host, port_path_or_id, db = (None, None, None)

    try:
        dt = transaction.settings.datastore_tracer
        if dt.instance_reporting.enabled or dt.database_name_reporting.enabled:
            conn_kwargs = _conn_attrs_to_dict(instance)
            host, port_path_or_id, db = _instance_info(conn_kwargs)
    except:
        pass

    transaction._nr_datastore_instance_info = (host, port_path_or_id, db)

    # Older Redis clients would when sending multi part commands pass
    # them in as separate arguments to send_command(). Need to therefore
    # detect those and grab the next argument from the set of arguments.

    operation = args[0].strip().lower()

    # If it's not a multi part command, there's no need to trace it, so
    # we can return early.

    if operation.split()[0] not in _redis_multipart_commands:
        return wrapped(*args, **kwargs)

    # Convert multi args to single arg string

    if operation in _redis_multipart_commands and len(args) > 1:
        operation = "%s %s" % (operation, args[1].strip().lower())

    operation = _redis_operation_re.sub("_", operation)

    with DatastoreTrace(
        product="Redis", target=None, operation=operation, host=host, port_path_or_id=port_path_or_id, database_name=db
    ):
        return wrapped(*args, **kwargs)


def instrument_redis_connection(module):
    wrap_function_wrapper(module, "Connection.send_command", _nr_Connection_send_command_wrapper_)
