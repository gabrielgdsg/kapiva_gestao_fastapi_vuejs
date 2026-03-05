from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)


class PostgresDatabase:

    __connection_pool = None

    @staticmethod
    def initialise(**kwargs):
        """Initialize the connection pool with error handling."""
        try:
            PostgresDatabase.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)
            logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise RuntimeError(f"Database connection pool initialization failed: {str(e)}")

    @staticmethod
    def get_connection():
        """Get a connection from the pool with error handling."""
        if PostgresDatabase.__connection_pool is None:
            raise RuntimeError("Database connection pool not initialized. Call initialise() first.")
        try:
            return PostgresDatabase.__connection_pool.getconn()
        except pool.PoolError as e:
            logger.error(f"Failed to get connection from pool: {str(e)}")
            raise RuntimeError(f"Database connection pool exhausted or unavailable: {str(e)}")

    @staticmethod
    def return_connection(connection):
        """Return a connection to the pool with error handling."""
        if PostgresDatabase.__connection_pool is None:
            logger.warning("Attempted to return connection but pool is not initialized")
            return
        try:
            PostgresDatabase.__connection_pool.putconn(connection)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")

    @staticmethod
    def close_all_connections():
        """Close all connections in the pool."""
        if PostgresDatabase.__connection_pool is None:
            return
        try:
            PostgresDatabase.__connection_pool.closeall()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {str(e)}")


class CursorFromConnectionFromPool:

    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = PostgresDatabase.get_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        try:
            if exception_value:  # This is equivalent to `if exception_value is not None`
                self.conn.rollback()
            else:
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {str(e)}")
            if not exception_value:  # Only rollback if we weren't already handling an exception
                try:
                    self.conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {str(rollback_error)}")
        finally:
            # Always close cursor and return connection, even if there was an error
            if self.cursor and not self.cursor.closed:
                try:
                    self.cursor.close()
                except Exception as e:
                    logger.error(f"Error closing cursor: {str(e)}")
            PostgresDatabase.return_connection(self.conn)
