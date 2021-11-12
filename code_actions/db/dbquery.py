from os import path
from pandas import DataFrame
import re
import logging


class Dbquery:
    
    def __init__(self, dbconnection, queries):
        self.dbconnection = dbconnection
        self.queries = queries
		
    def _read(self, queryname, id_table):
        """
        Internal function for call read of dbconnection
        :param queryname: name of query in ini configuration (str)
        :param id_table: the id to filter rows in the select table
        :return: dataframe
        """
        sql = self.queries.get('SQL_READ', queryname)
        try:
            if id_table!=None:
                return self.dbconnection.read(sql, id_table)
            else:
                return self.dbconnection.read(sql, None)    
        except Exception as e:
            self._rollback(e)

    def _insert(self, queryname, data, return_id=False, **extras):
        """
        Internal function for call insert of dbconnection
        :param queryname: name of query in ini configuration (str)
        :param dframe: pandas dataframe
        :param return_id: if you want the inserted ID back (bool)
        :param extras: set value of fields that aren't in data but in query
        :return: success
        """
        sql = self.queries.get('SQL_INSERT', queryname)
        m = re.match("insert into (?P<table>\w+) ?\((?P<columns>[\S ]+)\)", sql, flags=re.IGNORECASE)
        columns = re.sub(' ', '', m.group('columns')).split(',')
        dframe = DataFrame(data, columns=columns)
        for key, value in extras.items():
            dframe[key] = value
        try:
            return self.dbconnection.insert(sql, dframe, return_id=return_id)
        except Exception as e:
            self._rollback(e)

    def _update(self, queryname, id_table):
        """
        Internal function for call read of dbconnection
        :param queryname: name of query in ini configuration (str)
        :param id_table: the id to select records to update
        :return: success
        """
        sql = self.queries.get('SQL_UPDATE', queryname)
        try:
            return self.dbconnection.update(sql, id_table)
        except Exception as e:
            self._rollback(e)

    def _delete(self, queryname, id_table):
        """
        Internal function for call read of dbconnection
        :param queryname: name of query in ini configuration (str)
        :param id_table: the id to filter rows in the select table
        :return: success
        """
        sql = self.queries.get('SQL_DELETE', queryname)
        try:
            return self.dbconnection.remove(sql, id_table)
        except Exception as e:
            self._rollback(e)

    def _commit(self):
        """
        Internal function for commit updates on dbconnection
        """
        try:
            self.dbconnection.commit()
        except Exception as e:
            self._rollback(e)

    def _rollback(self, error):
        """
        Internal function for rollback updates on dbconnection
        """
        logging.error(error)
        try:
            self.dbconnection.rollback()
        finally:
            raise DBOperationError(error)

    def _close(self):
        """
        Internal function for close connection
        """
        try:
            self.dbconnection.close()
        except Exception as e:
            raise DBConnectionError()

    def close(self):
        """
        Replace this method for do something after responce
        """
        pass
