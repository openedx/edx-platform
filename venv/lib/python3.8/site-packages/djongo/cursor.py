from logging import getLogger

from .database import DatabaseError
from .sql2mongo.query import Query

logger = getLogger(__name__)


class Cursor:

    def __init__(self,
                 client_conn,
                 db_conn,
                 connection_properties):
        self.db_conn = db_conn
        self.client_conn = client_conn
        self.connection_properties = connection_properties
        self.result = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.result is not None:
            self.result.close()

    def __getattr__(self, name):
        try:
            return getattr(self.result, name)
        except AttributeError:
            pass

        try:
            return getattr(self.db_conn, name)
        except AttributeError:
            raise

    @property
    def rowcount(self):
        if self.result is None:
            raise RuntimeError

        return self.result.count()

    @property
    def lastrowid(self):
        return self.result.last_row_id

    def execute(self, sql, params=None):
        try:
            self.result = Query(
                self.client_conn,
                self.db_conn,
                self.connection_properties,
                sql,
                params)
        except Exception as e:
            db_exe = DatabaseError()
            raise db_exe from e

    def fetchmany(self, size=1):
        ret = []
        for _ in range(size):
            try:
                ret.append(self.result.next())
            except StopIteration:
                break
            except Exception as e:
                db_exe = DatabaseError()
                raise db_exe from e

        return ret

    def fetchone(self):
        try:
            return self.result.next()
        except StopIteration:
            return None
        except Exception as e:
            db_exe = DatabaseError()
            raise db_exe from e

    def fetchall(self):
        return list(self.result)

