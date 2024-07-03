import psycopg2
from psycopg2 import Error
from psycopg2 import IntegrityError
class Database:
    def __init__(self, user = "postgres", password = "<PASSWORD>", host = "0.0.0.0", port = "5432", database = "name"):
        try:
            self.connection = psycopg2.connect(user="AmadeoMartell",
                                          password="",
                                          host="",
                                          port="",
                                          database="AITUstudents")

            self.cursor = self.connection.cursor()
            print("Информация о сервере PostgreSQL")
            print(self.connection.get_dsn_parameters(), "\n")
            self.cursor.execute("SELECT version();")
            record = self.cursor.fetchone()
            print("Вы подключены к - ", record, "\n")
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
    def selectAll(self):
        checkup_query = """SELECT * FROM studentdb"""
        self.cursor.execute(checkup_query)
        for row in self.cursor.fetchall():
            yield row

    def insertRecord(self, val1: int, val2: str, val3: int, val4: str):
        try:
            checkup_query = """INSERT INTO studentdb(id, name, age, major) VALUES(%s, %s, %s, %s)"""
            item_tuple = (val1, val2, val3, val4)
            self.cursor.execute(checkup_query, item_tuple)
            self.connection.commit()
            return True
        except IntegrityError as e:
            self.connection.rollback()
            return False

    def updateStudentField(self, id: int, field: str, val):
        try:
            checkup_query = f"UPDATE studentdb SET {field} = %s WHERE id = %s"
            item_tuple = (val, id)
            self.cursor.execute(checkup_query, item_tuple)
            self.connection.commit()
            return True
        except IntegrityError as e:
            self.connection.rollback()
            return False

    def deleteStudentField(self, id: int):
        try:
            checkup_query = f"DELETE FROM studentdb WHERE id = {id}"
            self.cursor.execute(checkup_query)
            self.connection.commit()
            return True
        except IntegrityError as e:
            self.connection.rollback()
            return False
    def closeConnection(self):
        self.cursor.close()
        self.connection.close()
        print("Соединение с PostgreSQL закрыто")