import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values
import pandas.io.sql as psql


class Dbconnection:

    def __init__(self, schema, database, user, password, dbhost, dbport):
        self._properties = dict(
            database=database,
            user=user,
            password=password,
            host=dbhost,
            port=dbport,
            options=f'-c search_path={schema}'
        )
        self._pool = psycopg2.pool.ThreadedConnectionPool(1,1,**self._properties)
       # self._conn = psycopg2.connect(**self._properties)

    #@property
    def conn(self):
        return self._pool.getconn()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    def commit(self):
        # Commit della connection a DB (altrimenti le modifiche effettuate non vengono applicate sul database)
        self.conn.commit()

    def rollback(self):
        # Rollback to clean wrong DB modifications
        self.conn.rollback()

    def read(self, sql, idTable):
        """
        :param sql: read sql to execute
        :param idTable: the id to filter rows in the select table
        :return: a dataframe of the selected rows, -1 otherwise
        """
        connection = None
        try:
            connection = self.conn()
            cursor = connection.cursor()
            if idTable!=None:
                cursor.execute(sql,[idTable])
            else:
                cursor.execute(sql)    
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return(-1)
        finally:
            if connection :
                connection.close()
                self._pool.putconn(connection) 

    def insert(self, sql, dframe,return_id = False):
        """
        :param sql: insert query to execute
        :param dframe: data_frame to insert in the database
                       Columns order and types must be coherent with the input SQL
        :param return_id: Bool if you want the inserted ID back
        :return: the inserted ID
        """
        connection = None
        id_out = -1
        try:
            connection = self.conn()
            cursor = connection.cursor()
            values_list = [tuple(x) for x in dframe.values]
            # Execute multiple insert
            execute_values(cursor, sql, values_list)
            # If main table retrieve autoincrement ID
            if return_id:
                id_out = cursor.fetchone()[0]
            connection.commit()
            return id_out
        except Exception as e:
            print(e)
            return(-1)
        finally:
            if connection:
                connection.close()
                self._pool.putconn(connection) 

    def update(self, sql, idTable):
      """
      :param sql: update_sql query
      :param idTable: id to select records to update
      :return:  None
      """
      with self.conn.cursor() as c:
          c.execute(sql, (idTable,))


    def remove(self, delete_sql, idTable):
        """
        :param delete_sql: delete sql to execute
        :param idTable: the id of the rows to delete
        """
        with self.conn.cursor() as c:
            c.execute(delete_sql, (idTable,))
