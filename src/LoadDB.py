import io
import os
import src.ExceptionService.Exceptions as e

import requests
import pandas as pd
class DB_loader:

    path_db = '../db'

    #Google folder id (db)
    id = '1ZbSjOwV8wLUj813CrrtJGSuOD8zRCrG4LznuBM5k33w'

    def check_folder(self):
        if not os.path.exists(self.path_db): os.mkdir(self.path_db)
    def __init__(self):
       """
       Отловить случай, если нет доступа к сети.
       """
       self.check_folder()

    def getInfo(self, id, marketplace) -> list:
        """
        get_info method

        :param id: int , id желаемого поставщика
        :param marketplace: str, название маркетплейса (2 буквы: WB, OZ и т.д.)

        return -> list(str), соответствующий полученным данным из гугл таблицы.
        """

        # Получаем файл из гугл таблиц
        url = f"https://docs.google.com/spreadsheets/export?id={self.id}&exportFormat=csv"
        try:
            response = requests.get(url)
        except requests.RequestException():
            raise e.CustomError("Check Internet Connection")

        # Переделываем его в pandas объект
        db = pd.read_csv(io.StringIO(response.text))

        # Ищем строку соответствующую входным 'ID' и 'Marketplace'. Если нет совпадений - выбрасываем ошибку
        matches = db.loc[(db['ID'] == id) & (db['Marketplace'] == marketplace)]
        if len(matches.values) == 0:
            raise e.CustomError('Check ID')
        
        return matches.values.tolist()