import io
import itertools
import json
import os
import sys
import re
import time

import googleapiclient.errors
import gspread as gspread
import numpy as np
import requests
import openai

import Levenshtein
import pandas as pd

import main

import src.ExceptionService.Exceptions
from config.Config import Config
from config.presets.AnyData import AnyData
from src.API import Api as API

openai.api_key = os.getenv('OPENAI_API_KEY')


@staticmethod
def cleartext(text):
    return re.sub(r'[^a-zа-я]', '', text)


def findMatches(where, what):
    from fuzzywuzzy import fuzz
    max_similarity = 0
    max_item = None
    for category in what:
        for item in where:
            similarity = fuzz.ratio(cleartext(category.lower()), cleartext(item.lower()))
            if similarity > max_similarity:
                max_similarity = similarity
                max_item = item
    return max_item


def export_to_excel(df, filename='output.xlsx'):
    # Получение максимальной длины столбца
    max_length = max([len(df[col]) for col in df.columns])

    # Дозаполнение столбцов значениями по умолчанию
    for col in df.columns:
        if len(df[col]) < max_length:
            df[col] = df[col].tolist() + [''] * (max_length - len(df[col]))

    # Экспорт датафрейма в Excel таблицу
    df.to_excel(filename, index=False)


def ExtractPatternFromText(pattern, text):
    match = re.findall(pattern, text, flags=re.IGNORECASE)
    return match


# исправить все рег. шаблоны
def extract_sizes(row, col, df):
    # получить значение ячейки
    value = df.iloc[row, col]
    sizes = {}

    if pd.isna(value): return sizes

    # поиск значений с помощью регулярных выражений
    # length = re.findall(r'длина[\s\.:]+([\d\.,]+)\s*см', value, flags=re.IGNORECASE)
    length = re.findall(r'длина.*?([\d\.,]+)\s*(?:см|мм|м)', value, flags=re.IGNORECASE)
    if length:
        length = [float(l.replace(',', '.')) for l in length[0].split('-')]
        if 'мм' in value:
            sizes['длина'] = sum(length) / len(length) / 10
        elif 'м' in value:
            sizes['длина'] = sum(length) / len(length) * 100
        else:
            sizes['длина'] = sum(length) / len(length)

    width = re.findall(r'(?:макс\.?\s*ширина|ширина|ширина в самой широкой точке).*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|m)',
                       value, flags=re.IGNORECASE)
    if width:
        width = [float(w.replace(',', '.')) for w in width[0].split('-')]
        if 'мм' in value:
            sizes['ширина'] = sum(width) / len(width) / 10
        elif 'м' in value:
            sizes['ширина'] = sum(width) / len(width) * 100
        else:
            sizes['ширина'] = sum(width) / len(width)

    height = re.findall(r'высота.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|м)', value, flags=re.IGNORECASE)
    if height:
        height = [float(h.replace(',', '.')) for h in height[0].split('-')]
        if 'мм' in value:
            sizes['высота'] = sum(height) / len(height) / 10
        elif 'м' in value:
            sizes['высота'] = sum(height) / len(height) * 100
        else:
            sizes['высота'] = sum(height) / len(height)

    diameter = re.findall(r'(?:макс\.?\s*диаметр|диаметр).*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|m)', value,
                          flags=re.IGNORECASE)
    if diameter:
        diameter = [float(d.replace(',', '.')) for d in diameter[0].split('-')]
        if 'мм' in value:
            sizes['диаметр'] = sum(diameter) / len(diameter) / 10
        elif 'м' in value:
            sizes['диаметр'] = sum(diameter) / len(diameter) * 100
        else:
            sizes['диаметр'] = sum(diameter) / len(diameter)

    # объем
    volume = re.findall(r"\b(\d+(?:\.\d+)?)\s*(мл|л)\b|\bобъем[\s.:]+(\d+(?:\.\d+)?)\s*(мл|л)\b", value,
                        flags=re.IGNORECASE)
    if volume:
        try:
            v, unit = volume[0]
            if unit == 'л':
                sizes['объем'] = float(v.replace(',', '.')) * 1000
            else:
                sizes['объем'] = float(v.replace(',', '.'))
        except ValueError:
            sizes['объем'] = volume[0]

    # размер одежды
    size = re.findall(r'\b\d{2}-\d{2}\b|\b\w+\b\s+\d{2,3}[-/]\d{2,3}\b', value)
    if size:
        sizes['размер'] = size[0].replace('размер', '')

    # размеры если они записаны неочевидно
    size = re.findall(r'(\d+)\s*[x*]\s*(\d+)\s*[x*]\s*(\d+)\s*(cm|см)', value)
    if size:
        sizes['длина'] = int(size.group(1))
        sizes['высота'] = int(size.group(2))
        sizes['ширина'] = int(size.group(3))

    # вес
    weight = None
    # weight = re.findall(r'вес\s+(\S+)\s+(\d+(?:\.\d+)?)(?:\s*(г|гр|грамм|килограмм|кг|кило))?', value)
    if weight:
        weight_value = [lambda _: float(_) for _ in weight if isinstance(_, float)]
        # weight_units = weight.group(4)
        # weight_value = float(weight.group(3))

    # глубина
    depth = re.findall(r'глубина.*?[\s\.:]+([\d\.,]+).*?\s*(?:см|мм|inch)', value, flags=re.IGNORECASE)
    if depth:
        depth = [float(d.replace(',', '.')) for d in depth[0].split('-')]
        if 'мм' in value:
            sizes['глубина'] = sum(depth) / len(depth) / 10
        else:
            sizes['глубина'] = sum(depth) / len(depth)

    # максимальный и минимальный диаметры
    max_diameter = re.findall(r'макс(?:\.|имальный) диаметр.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                              flags=re.IGNORECASE)
    if max_diameter:
        sizes['максимальный диаметр'] = float(max_diameter[0].replace(',', '.'))

    min_diameter = re.findall(r'мин(?:\.|имальный) диаметр.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                              flags=re.IGNORECASE)
    if min_diameter:
        sizes['минимальный диаметр'] = float(min_diameter[0].replace(',', '.'))

    # максимальная и минимальная ширины
    max_width = re.findall(r'макс(?:\.|имальная) ширина.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                           flags=re.IGNORECASE)
    if max_width:
        sizes['максимальная ширина'] = float(max_width[0].replace(',', '.'))

    min_width = re.findall(r'мин(?:\.|имальная) ширина.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                           flags=re.IGNORECASE)
    if min_width:
        sizes['минимальная ширина'] = float(min_width[0].replace(',', '.'))

    # максимальная и минимальная высоты
    max_height = re.findall(r'макс(?:\.|имальная) высота.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                            flags=re.IGNORECASE)
    if max_height:
        sizes['максимальная высота'] = float(max_height[0].replace(',', '.'))

    min_height = re.findall(r'мин(?:\.|имальная) высота.*?[\s\.:]+([\d\.,]+)\s*(?:см|мм|inch)', value,
                            flags=re.IGNORECASE)
    if min_height:
        sizes['минимальная высота'] = float(min_height[0].replace(',', '.'))

    return sizes


class SexOptovik_ozon(main.Functions):
    ACCURANCY = 2  # больше - дольше

    config = Config()

    creds = {'Api-Key': '',
             'Client-Id': ''
             }

    API = None

    def __init__(self, config):
        super().__init__(needAuth=False)
        self.config = config
        self.start()

    def importCredentials(self) -> int:
        try:
            with open('./credentials/Ozon/API/ozon-seller-api-{0}.txt'.format(self.config.id), 'r') as f:
                self.creds['Api-Key'] = f.readline()
            with open('./credentials/Ozon/Client-Id/client-id-{0}.txt'.format(self.config.id), 'r') as f:
                self.creds['Client-Id'] = f.readline()
            return 0
        except OSError:
            raise src.ExceptionService.Exceptions.CustomError(
                '[!] Ошибка при получении API ключа. Проверьте Credentials')

    def checkFolders(self):
        pass

    def downloadProducts(self):
        main.Functions.download_universal([self.config.urlItems,
                                           self.config.urlStocks],
                                          path_def='./SexOptovik')

    def importCats(self) -> dict:
        return self.unpack_json(
            self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["category-tree"]}',
                body=self.API.createRequest(
                    category_id=17027484
                )).json()
        )

    def unpack_json(self, json_data) -> dict:
        result = {'all': {},
                  'cosmetic': {}
                  }

        def process_category(category, parent_title=None):
            category_id = category['category_id']
            title = category['title']
            children = category['children']

            if not children:
                result[parent_title][title] = category_id

            if category_id in [85697584, 17028960]:
                parent_title = 'cosmetic'
            elif category_id == 17035677:
                parent_title = 'clothe'
            else:
                parent_title = 'all'

            for child in children:
                process_category(child, parent_title)

        categories = json_data['result']
        for category in categories:
            process_category(category)
        self.FindingOtherCats(result,
                              self.API.sendResponse(
                                  url=f'{self.API.urlOzon}{self.API.OzonRequestURL["category-tree"]}',
                                  body=self.API.createRequest(
                                  )).json()
                              )

        return result

    def getCatViaChatGPT(self, what, where, additionalPrompt):
        success = False
        while not success:
            try:
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo-0613',
                    messages=[{'role': 'user',
                               'content': what + additionalPrompt + 'Список категорий откуда тебе надо выбрать 1 совпадение и отправить мне: ' + ', '.join(
                                   where)}],
                    temperature=0
                )
                success = True
                return response['choices'][0]['message']['content']
            except openai.error.ServiceUnavailableError as e:
                print('Ошибка сервера. Жду 15 сек')
                time.sleep(15)
            except openai.error.APIError:
                print('Ошибка сервера. Жду 15 сек')
                time.sleep(15)

    def FindingOtherCats(self, dict, json):

        def process_category(category):
            category_id = category['category_id']
            if category_id in [17027484]: return
            title = category['title']
            children = category['children']

            erotic_keywords = ['эротич' in title.lower(), 'бдсм' in title.lower(), '18+' in title.lower()]
            cosmetic_keywords = ['лубрикант' in title.lower(), 'презерватив' in title.lower(),
                                 'интим' in title.lower()]

            keywords_mapping = {
                'cosmetic': cosmetic_keywords,
                'all': erotic_keywords
            }

            for category, keywords in keywords_mapping.items():
                if not children and any(keywords):
                    dict[category][title] = category_id

            for child in children:
                process_category(child)

        categories = json['result']
        for category in categories:
            process_category(category)

        return dict

    def getCatList(self):
        pass

    def createAPI(self):
        self.API = API.ServiceAPI(Host="api-seller.ozon.ru",
                                  ApiKey=self.creds['Api-Key'],
                                  ClientId=self.creds['Client-Id'],
                                  ContentType="application/json")

    def checkNewProduct(self, catsOzon):

        def sendToSpreadSheet(upload):
            success = False
            while not success:
                try:
                    self.add_data_to_columns(
                        self.config.SpreadsheetService,
                        spreadsheet_id='1zlsbQWPkikBlRiznlkv6asIdRdaGBBHbmQu8M_6mfOU',
                        target_row_index=i + 1,
                        data={'id': upload[0], 'category': upload[1],
                              'name': upload[2], 'description': upload[3]}
                    )
                    success = True
                    upload = [[], [], [], []]
                except googleapiclient.errors.HttpError as e:
                    if e.status_code == 429:
                        print('bro chill, chill')
                    else:
                        return 1
            return 0

        df = pd.read_csv('./SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')
        productInfo = df.iloc[:, 3]
        productInfo.dropna(inplace=True)

        upload = [[], [], [], []]

        exist_aritucls = self.getInfo()
        for i in range(len(productInfo)):
            if (df.iloc[i, 0] not in exist_aritucls):

                send = df.iloc[i, 3] if not df.iloc[i, 3] is np.nan else df.iloc[i, 2]

                # if '#' in send:
                #     send = send[:send.find('#')-1]

                res = self.getCatViaChatGPT(what=send,
                                            where=(list(catsOzon['all'].keys()) + list(catsOzon['cosmetic'].keys())),
                                            additionalPrompt='Пришли только ОДНУ категорию ИЗ СПИСКА ниже, которой соответствует этот товар.')

                if '"' in res:
                    res = re.search('"([^"]+)"', res).group(1)


                upload[0].append(str(df.iloc[i, 0]))
                upload[1].append(res)
                upload[2].append(df.iloc[i, 2])
                upload[3].append(send)

                if (i + 1) % 50 == 0 or i == len(productInfo)-1:
                    sendToSpreadSheet(upload)
                # try:
                #     category = re.split(r'[\s*|#*|>*|,*]', (productInfo[i]+re.sub(r'[^а-яА-Я\s]', '',df.iloc[i,2])).lower())
                # except KeyError:
                #     category = re.split(r'[\s*|#*|>*|,*]', re.sub(r'[^а-яА-Я\s]', '', df.iloc[i,2]).lower())
                # category = list(set(category))
                #
                # for i in range(self.ACCURANCY+1):
                #     category.append(' ')
                #
                # category = set(list(map(str, itertools.product(category, self.ACCURANCY))))
                # res = findMatches(where=catsOzon, what=category)
                print(res, '<< ', i + 1)

    def getInfo(self) -> set:
        spreadsheet_id = '1zlsbQWPkikBlRiznlkv6asIdRdaGBBHbmQu8M_6mfOU'
        range_name = 'Лист1!A1:Z'

        # Запрос данных из таблицы
        result = self.config.SpreadsheetService.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                                            range=range_name).execute()
        values = result.get('values', [])

        # Преобразование в DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        df = df.dropna()
        # Получение списка значений из колонки "ID"
        id_values = [int(x) for x in df['ID'].tolist()]
        return set(id_values)

    def add_data_to_columns(self, sheets_service, spreadsheet_id, data, target_row_index):
        # Получение метаданных таблицы
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_properties = sheets[0]['properties']
        sheet_title = sheet_properties['title']
        grid_properties = sheet_properties['gridProperties']
        num_columns = grid_properties['columnCount']

        # Автонахождение столбца "ID" и "Category" по заголовкам
        id_column_index = None
        category_column_index = None
        name_column_index = None
        description_column_index = None

        header_range = f'{sheet_title}!1:1'
        headers = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=header_range).execute()
        if 'values' in headers:
            headers = headers['values'][0]
            for i in range(num_columns):
                if headers[i] == 'ID':
                    id_column_index = i + 1
                elif headers[i] == 'Category':
                    category_column_index = i + 1
                elif headers[i] == 'Name':
                    name_column_index = i + 1
                elif headers[i] == 'Description':
                    description_column_index = i + 1
                if id_column_index is not None and category_column_index is not None \
                        and name_column_index is not None and description_column_index is not None:
                    break

        # Определение диапазона для добавления данных
        range_id = f'{sheet_title}!{chr(id_column_index + 64)}:{chr(id_column_index + 64)}'
        range_category = f'{sheet_title}!{chr(category_column_index + 64)}:{chr(category_column_index + 64)}'
        range_name = f'{sheet_title}!{chr(name_column_index + 64)}:{chr(name_column_index + 64)}'
        range_description = f'{sheet_title}!{chr(description_column_index + 64)}:{chr(description_column_index + 64)}'

        # Получение текущих значений в столбцах
        values = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_id).execute()
        values_category = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                                     range=range_category).execute()
        values_description = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                                        range=range_description).execute()
        values_names = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                                  range=range_name).execute()
        # Извлечение текущих значений из ответа
        existing_values = values.get('values', [])
        existing_values_category = values_category.get('values', [])
        existing_values_description = values_description.get('values', [])
        existing_values_names = values_names.get('values', [])

        # Добавление новых значений в конец столбцов
        for i in range(len(data['id'])):
            existing_values.insert(len(existing_values), [str(data['id'][i])])
            existing_values_category.insert(len(existing_values), [data['category'][i]])
            existing_values_description.insert(len(existing_values), [data['description'][i]])
            existing_values_names.insert(len(existing_values), [data['name'][i]])

        # Подготовка данных для обновления
        data = [
            {
                'range': range_id,
                'values': existing_values
            },
            {
                'range': range_category,
                'values': existing_values_category
            },
            {
                'range': range_name,
                'values': existing_values_names
            },
            {
                'range': range_description,
                'values': existing_values_description
            }
        ]

        # Обновление значений в таблице
        success = False
        while not success:
            try:
                sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id,
                                                                        body=self.API.createRequest(
                                                                            data=data,
                                                                            valueInputOption="USER_ENTERED",
                                                                            includeValuesInResponse="false",
                                                                            responseValueRenderOption="FORMATTED_VALUE",
                                                                            responseDateTimeRenderOption="SERIAL_NUMBER"
                                                                        )).execute()
                success = True
            except TimeoutError:
                time.sleep(5)
        print('Data added successfully.')

    def start(self):
        A = AnyData()
        #existArticulsSet = self.getExistArticuls()
        try:
            self.importCredentials()
            #self.downloadProducts()
        except src.ExceptionService.Exceptions.CustomError as e:
            print('[!] Ошибка.\nПодробнее: {0}'.format(e))
            sys.exit(1)
        self.createAPI()
        dictCatId = self.importCats()

        self.checkNewProduct(dictCatId)

        #print(json.dumps(self.API.sendResponse(
        #    url=f'{self.API.urlOzon}{self.API.OzonRequestURL["category-tree"]}',
        #    body=self.API.createRequest(
        #        category_id=17027484
        #    )).json(), ensure_ascii=False, indent=4, sort_keys=True))
        # self.allocateNewProductCats(dictCatId)
        ind = 0

    def getExistArticuls(self, columnsExcel=None) -> set:

        if columnsExcel is None:
            columnsExcel = {}

        main.Functions.google_driver(google_ids=[self.config.driveIdExistItems],
                                     file_names=[f"{self.config.shopName}_OZ.csv"],
                                     path_os_type='./pool/SexOptovik/google_downloaded',
                                     service=self.config.DriveService)
        print('Считаю новые товары...')
        productListPath = f'./pool/SexOptovik/google_downloaded/{self.config.shopName}_OZ.csv'
        checkBrand = self.config.checkBrand

        goods, errors, lieBrands = main.Functions.getDataCsv(self,
                                                             path=productListPath,
                                                             sellerCode=str(self.config.id),
                                                             checkBrand=checkBrand,
                                                             marketplace='oz')

        df = pd.DataFrame({'OK': len(goods), 'ERRORS': len(errors), 'LIE': len(lieBrands)}, index=['>>'])
        print(df)
        print(f"\n\n{pd.DataFrame({'errors': list(errors)})}")

        return goods

    @staticmethod
    def measure_time(f):
        # Определяем вложенную функцию timed
        def timed(*args, **kw):
            # Запоминаем время начала выполнения
            ts = time.time()
            # Вызываем оригинальную функцию и сохраняем результат
            result = f(*args, **kw)
            # Запоминаем время конца выполнения
            te = time.time()
            # Выводим имя функции, аргументы и время выполнения
            print(f"{f.__name__}({args}, {kw}) {te - ts:.2f} sec")
            # Возвращаем результат оригинальной функции
            return result

        # Возвращаем вложенную функцию timed
        return timed

    def matchType(self, name, s=None):
        if not isinstance(name, set) or not isinstance(s, set) or not s:
            return None
        # Инициализируем переменные для хранения лучшего совпадения и минимального расстояния
        best_match = None
        min_distance = float("inf")
        # Перебираем все значения из set
        for i in name:
            for value in s:
                # Вычисляем расстояние Левенштейна между name и value с помощью модуля python-Levenshtein
                distance = Levenshtein.distance(i, value)
                # Если расстояние меньше минимального, обновляем лучшее совпадение и минимальное расстояние
                if distance < min_distance:
                    best_match = value
                    min_distance = distance
        # Возвращаем лучшее совпадение
        return best_match
