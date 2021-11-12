from .dbconnection import Dbconnection
from .dbquery import Dbquery
from configparser import RawConfigParser


class Dbwrapper:

    def __init__(self, schema, database, user, password, dbhost, dbport):
        self.connection = Dbconnection(
            schema, database, user, password, dbhost, dbport)
        configSql = RawConfigParser()
        configSql.read('db/configSQL.ini')
        self.queries = configSql
        self.dbquery = Dbquery(self.connection, configSql)

    def select_avviso_comune(self, id_comune):
        result = self.dbquery._read('read_avviso_comune', id_comune)
        avviso = 'BOT_NOTFOUND'
        if result:
            avviso = result[0][0]
        return avviso

    def select_no_response_comune(self, id_comune):
        result = self.dbquery._read('read_no_response_comune', id_comune)
        noresponse = ''
        if result:
            noresponse = result[0][0]
        return noresponse

    def select_vide_comune(self, id_comune):
        result = self.dbquery._read('read_vide_comune', id_comune)
        vide_flag = False
        if result:
            vide_flag = result[0][0]
        return vide_flag

    def select_vide_url_comune(self, id_comune):
        result = self.dbquery._read('read_vide_url_comune', id_comune)
        vide_url = ''
        if result:
            vide_url = result[0][0]
        return vide_url

    def select_questions(self, id_comune):
        return self.dbquery._read('read_questions',  id_comune)

    def select_categories(self, id_comune):
        return self.dbquery._read('read_categories',  id_comune)

    def insert_feedback(self, datetime: str, id_session: int, id_tenant: int, content: str, last_question: str, last_answer: str, question_id: int):
        self.dbquery._insert('insert_feedback', data=[
                             [datetime, id_session, id_tenant, content, last_question, last_answer, question_id]])
