import requests
import datetime as dt
import cx_Oracle

class Get_Logs:
    'Это класс для получения логов'
    def __init__(self, date = dt.datetime.strptime('23.01.2021', '%d.%m.%Y').date()):
        self.date = date
        self.url = f"http://www.dsdev.tech/logs/{self.date.strftime('%Y%m%d')}"
        self.data = requests.get(self.url).json()
        if self.data['error'] != '':
            self.error = True
            print(f"При обращении к логам обнаружена ошибка : \n\t{self.data['error']}")
        else:
            self.error = False
            print(f"Логи за {self.date.strftime('%d.%m.%Y')} успешно получены")
        self.sorted = False
        self.inserted_into_database = False

    def sort(self):
        if self.error == True:
            print('Невозможно сортировать логи с ошибкой')
            return None

        self.logs = []
        for primary_log in self.data['logs']:
            log = primary_log.copy()
            # Распознаем дату логов
            log['created_at'] = dt.datetime.strptime(log['created_at'], '%Y-%m-%dT%H:%M:%S')
            for log_sorted in self.logs:
                if log['created_at'] <= log_sorted['created_at']:
                    index = self.logs.index(log_sorted)
                    self.logs.insert(index, log)
                    break
            else:
                self.logs.append(log)
        self.sorted = True
        print('Логи отсортированы')
        return self.logs

    def insert_into_database(self, *, clear_table = False):
        if self.error == True:
            print('Невозможно вставить в базу данных логи с ошибкой')
            return None
        elif self.sorted == False:
            print('Нельзя вставлять в базу данных неотсортированные логи')
            return None
        elif self.inserted_into_database == True:
            print(f"Текущие логи за {self.date.strftime('%d.%m.%Y')} уже были вставлены в базу данных")
            return None

        conn = cx_Oracle.connect('user', 'password', 'database')
        cur = conn.cursor()

        check_query = "select count(*) from user_tables where table_name='LOGS'"
        cur.execute(check_query)
        check_table = cur.fetchall()[0][0]

        if check_table == 0:
            create_table_query = """create table logs (created_at date, user_id int, 
                first_name varchar2(50), second_name varchar2(50), message varchar2(4000))"""
            cur.execute(create_table_query)
            print('Таблица для логов создана')
        else:
            print('Таблица для логов уже существует')
            if clear_table == True:
                cur.execute('truncate table logs')
                print('Таблица очищена')

        for log in self.logs:
            insert_query = f"""insert into logs values
            (to_date('{log['created_at'].strftime('%d.%m.%Y %H:%M:%S')}', 'DD.MM.YYYY HH24:MI:SS'),
            {log['user_id']},
            '{log['first_name']}',
            '{log['second_name']}',
            '{log['message'].replace("'", "''")}')"""
            cur.execute(insert_query)
        cur.execute('commit')

        conn.close()
        self.inserted_into_database = True
        print(f"Логи вставлены в базу данных")


def get_date():
    date_correct = False
    while not (date_correct):
        date = input('Введите дату (дд.мм.гггг) : ')
        try:
            date = dt.datetime.strptime(date, '%d.%m.%Y').date()
        except ValueError:
            print('Дата введена некорректно')
        else:
            date_correct = True
    return date


if __name__ == "__main__":
    log_date = get_date()
    logs = Get_Logs(log_date)
    logs.sort()
    logs.insert_into_database()
    del log_date, logs