import logging
import mariadb
import sys


log = logging.getLogger(__name__)
log.setLevel('INFO')


class MariaDBConnection:

    @staticmethod
    def maria_connection():
        try:
            conn = mariadb.connect(
                user="python.test",
                password="123456",
                host="url.com",
                port=3306,
                database="test_data")
        except mariadb.Error as e:
            log.error(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        log.info('success to connect db')

        return conn.cursor(), conn
