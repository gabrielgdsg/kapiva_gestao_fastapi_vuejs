from psycopg2 import pool


class PostgresDatabase:

    __connection_pool = None

    @staticmethod
    def initialise(**kwargs):
        PostgresDatabase.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)

    @staticmethod
    def get_connection():
        return PostgresDatabase.__connection_pool.getconn()

    @staticmethod
    def return_connection(connection):
        PostgresDatabase.__connection_pool.putconn(connection)

    @staticmethod
    def close_all_connections():
        PostgresDatabase.__connection_pool.closeall()


class CursorFromConnectionFromPool:

    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = PostgresDatabase.get_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:  # This is equivalent to `if exception_value is not None`
            self.conn.rollback()
        else:
            self.cursor.close()
            self.conn.commit()
        PostgresDatabase.return_connection(self.conn)
