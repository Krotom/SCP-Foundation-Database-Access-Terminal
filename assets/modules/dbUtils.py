import sqlitecloud
import sqlite3


class GDBConn:
    def __init__(self):
        self.__gdb_conn_text = "sqlitecloud://chuyhbc6sz.sqlite.cloud:8860/scpDatabase.db?apikey=vOoybHOZcnaBFOpmbyoaxdnFqmSnHjiqV06tymiVHvg"
        self.__conn = sqlitecloud.connect(self.__gdb_conn_text)
        self.__cursorobj = self.__conn.cursor()

    def close(self):
        self.__cursorobj.close()
        self.__conn.close()

    def cursor(self):
        return self.__cursorobj

    def commit(self):
        self.__conn.commit()


class LDBConn:
    def __init__(self):
        self.__ldb_conn_text = "scpDatabase.db"
        self.__conn = sqlite3.connect(self.__ldb_conn_text)
        self.__cursorobj = self.__conn.cursor()

    def close(self):
        self.__cursorobj.close()
        self.__conn.close()

    def cursor(self):
        return self.__cursorobj

    def commit(self):
        self.__conn.commit()


if __name__ == '__main__':
    print("This file includes the database utility functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
