import sys
import re
import time
from typing import Tuple, Set, Any
from functools import lru_cache
import pymorphy2
from numba import njit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

import openai

import pandas as pd

import main

import src.ExceptionService.Exceptions
from config.Config import Config
from config.presets.AnyData import AnyData
from src.API import Api as API

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


class Product():
    def __init__(self):
        pass

class SexOptovik_ozon(main.Functions):
    ACCURANCY = 2  # больше - дольше

    config = Config()

    creds = {'Api-Key': '',
             'Client-Id': ''
             }

    API = None
    ProductOptovik = tuple[list(), list()]

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
        big_categories_with_ids = {'Сувениры': [],
                                   'Одежда': []
                                   }
        filtered = {
            "Сувениры": [
                92451036,
                92451043,
                47579342,
                56322589,
                17031662,
                17035783,
                17035672,
                44396240,
                17031686,
                92451028,
                92451029,
                17035680,
                17031677,
                88084839
            ],
            "Одежда":
                [17031674,
                 47579342,
                 17031689,
                 17035677,
                 17031681,
                 17031680,
                 17035672,
                 17035673,
                 17035680,
                 38142203,
                 74414685]
        }
        combined_set = {value for values_list in filtered.values() for value in values_list}

        def extract_children_with_ids(children):
            # Функция для извлечения пар (название-айди) детей категории
            return [(child['title'], child['category_id']) for child in children if
                    not child['children'] and child['category_id'] not in combined_set]

        for category in json_data['result'][0]['children']:
            # Обходим детей главной категории
            big_category_name = category['title']
            children_with_ids = extract_children_with_ids(category['children'])
            big_categories_with_ids[big_category_name] = children_with_ids

        self.find_other_categories(big_categories_with_ids,
                                   self.API.sendResponse(
                                       url=f'{self.API.urlOzon}{self.API.OzonRequestURL["category-tree"]}',
                                       body=self.API.createRequest(
                                       )).json(),
                                   filtered=filtered
                                   )

        return big_categories_with_ids

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

    def find_other_categories(self, dict, json, filtered):
        def checkSubCategories(dict, catId, filtered) -> bool:
            for i in list(dict.values()):
                for j in i:
                    if catId == j[1] and catId not in list(filtered.values())[0]:
                        return True
            return False

        def process_category(category):
            category_id = category['category_id']
            if checkSubCategories(dict, category_id, filtered) or category_id in [1000003681]:
                return
            title = category['title']
            children = category['children']

            erotic_keywords = [
                'эротич' in title.lower() and category_id not in filtered['Одежда'] + filtered['Сувениры'],
                'бдсм' in title.lower() and category_id not in filtered['Одежда'] + filtered['Сувениры'],
                '18+' in title.lower() and category_id not in filtered['Одежда'] + filtered['Сувениры']]
            cosmetic_keywords = [keyword in title.lower() for keyword in self.config.keywords_cosmetic or
                                 'тампоны' in title.lower()]
            clothe_keywords = [category_id in filtered['Одежда']]
            souvenirs_keywords = [category_id in filtered['Сувениры']]

            keywords_mapping = {
                'Интимная косметика': cosmetic_keywords,
                'Секс игрушки': erotic_keywords,
                'Одежда': clothe_keywords,
                'Сувениры': souvenirs_keywords
            }

            for category, keywords in keywords_mapping.items():
                if not children and any(keywords):
                    dict[category].append((title, category_id))

            for child in children:
                process_category(child)

        categories = json['result']
        for category in categories:
            process_category(category)

        return dict

    def getCatList(self):
        pass

    @staticmethod
    def defineCategoryList(category_information, dict) -> list:
        souvenirs_keywords = any(
            list(filter(lambda x: x.lower() in category_information.lower(), ['батарейки',
                                                                              'печатная продукция',
                                                                              'приколы',
                                                                              'фанты']
                        )))
        sextoys_keywords = any(
            list(filter(lambda x: x.lower() in category_information.lower(), ['секс-игрушки'
                                                                              ])))
        cosmetic_keywords = any(
            list(filter(lambda x: x.lower() in category_information.lower(), ['косметика',
                                                                              'препараты'
                                                                              ])))
        bdsm_keywords = any(
            list(filter(lambda x: x.lower() in category_information.lower(), ['бдсм'
                                                                              ])))
        clothe_keywords = any(
            list(filter(lambda x: x.lower() in category_information.lower(), ['белье'
                                                                              ])))


        condoms = 'презерватив' in category_information.lower()

        if souvenirs_keywords:
            return dict['Сувениры']
        elif sextoys_keywords:
            return dict['Секс игрушки']
        elif cosmetic_keywords:
            return dict['Интимная косметика'] + dict['No Use 18+'] + dict['Парфюмерия с феромонами']
        elif bdsm_keywords:
            return dict['БДСМ'] + [('БДСМ одежда', 17035677),
                                   ('Эротическое белье', 38142203)]
        elif clothe_keywords:
            return dict['Одежда']
        elif condoms:
            return [('Презервативы', 22825295)]

    def createAPI(self):
        self.API = API.ServiceAPI(Host="api-seller.ozon.ru",
                                  ApiKey=self.creds['Api-Key'],
                                  ClientId=self.creds['Client-Id'],
                                  ContentType="application/json")

    @staticmethod
    def process_products_api_with_decorator(func):
        def wrapper(self, *args, **kwargs):
            results = []
            last_id = ""
            json = self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["product-import-list"]}',
                body=self.API.createRequest(last_id=last_id)
            ).json()

            while json['result']['last_id'] != "":
                for i in json['result']['items']:
                    result = func(self, i)
                    results.append(result)

                json = self.API.sendResponse(
                    url=f'{self.API.urlOzon}{self.API.OzonRequestURL["product-import-list"]}',
                    body=self.API.createRequest(last_id=json['result']['last_id'])
                ).json()

            return results

        return wrapper

    @process_products_api_with_decorator
    def proccessProductArticulars(self, item):
        articular = self.cleanArticul(item['offer_id'], seller_code=str(self.config.id),
                                      marketplace=self.config.marketplace)
        if articular[0]:
            return 'good', articular[1]
        else:
            return 'error', articular[1]

    @process_products_api_with_decorator
    def proccessProductsBarcodes(self, item):
        return item['offer_id']

    def checkBarcodes(self):
        results = self.proccessProductsBarcodes()

        batch_size = 1000
        divided_results = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]

        c = 0

        for i in range(len(divided_results)):
            response = self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["get-products-info"]}',
                body=self.API.createRequest(
                    offer_id=divided_results[i]
                )
            ).json()
            for product in response['result']['items']:
                if not product['barcode'] or len(product['barcodes']) == 0:
                    cleanedArticular = self.cleanArticul(articular=product['offer_id'],
                                                         seller_code=str(self.config.id),
                                                         marketplace='oz',
                                                         shortArticular=True
                                                         )
                    # проверка оптовика
                    if cleanedArticular[0] and cleanedArticular[1] in self.ProductOptovik[0]:
                        self.updateAttribute(attributes={

                        })

    def importArticularOptovik(self):
        df = pd.read_csv('./SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')
        self.ProductOptovik = tuple[list(df.iloc[:, 0]), list(df.iloc[:, 14])]

    def importProductListAPI(self) -> tuple[set[Any], set[Any], set[Any]]:
        good, error, lie = set(), set(), set()
        results = self.proccessProductArticulars()
        for result_type, result_value in results:
            if result_type == 'good':
                good.add(result_value)
            elif result_type == 'error':
                error.add(result_value)
            elif result_type == 'lie':
                lie.add(result_value)

        return good, error, lie


    def checkNewProduct(self, catsOzon, exist_products):
        def calculateNewItems(df, exist_articuls) -> int:
            totally = 0
            productInfo = df.iloc[:, 3]
            productInfo.dropna(inplace=True)
            for i in range(len(productInfo)):
                if (df.iloc[i, 0] not in exist_articuls):
                    totally+=1
            print(f'Всего найдено новых товаров: {totally}')
            return totally

        """
        можно поменять на список, полученный через API
        """
        df = pd.read_csv('./SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')
        productInfo = df.iloc[:, 3]
        productInfo.dropna(inplace=True)

        newItems = calculateNewItems(df=df,
                                    exist_articuls=exist_products)
        def unpack_json_category_types(category_ids) -> list:
            total_types_list = []
            all_attributes = {}
            if isinstance(category_ids, (str, int)):
                category_ids = [category_ids]
            json_response = self.API.sendResponse(
                url=self.API.urlOzon + self.API.OzonRequestURL["category-attributes"],
                body=self.API.createRequest(category_id=category_ids, attribute_type="ALL", language="DEFAULT")
            ).json()
            for attributes in json_response['result']:
                category_id = attributes['category_id']
                attribute = attributes['attributes']
                all_attributes[category_id] = attribute
                for value in attribute:
                    if value['name'] == 'Тип':
                        getTypesList = self.API.sendResponse(
                            url=self.API.urlOzon + self.API.OzonRequestURL["category-attribute-values"],
                            body=self.API.createRequest(category_id=category_id,
                                                        attribute_id=value['id'],
                                                        language="DEFAULT",
                                                        limit=50,
                                                        last_value_id=0
                                                        )
                        ).json()
                        for i in range(len(getTypesList['result'])):
                            total_types_list.append(getTypesList['result'][i]['value'])
            return [total_types_list, all_attributes]




        def extractListCats(catsOzon, inited_categories,original_categories):
            for k, v in catsOzon.items():
                for category in v:
                    inited_categories[category[0]] = []
                    if category[0] not in original_categories:
                        original_categories.append(category[0])

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        def getCategoryTypes(catsOzon, type=dict()):
            """
            :param: catsOzon -> dict
            :param: type -> какого типа нужно получить результат
            example:
                "Секс-игрушки": [(Вибратор, 12345), ...]
            """
            all_types = {}
            all_attributes = {}
            for k,v in catsOzon.items():
                # Делаем разбивку категорий на пакеты по 20
                categories_chunks = list(chunks(v, 20))
                for chunk in categories_chunks:
                    category_ids = [category[1] for category in chunk]  # извлекаем идентификаторы категорий
                    res = unpack_json_category_types(category_ids=category_ids)
                    all_types[k] = res[0]
                    all_attributes[k] = res[1]

            if isinstance(type,dict):
                return all_types, all_attributes

        def category_initializer() -> dict:
            done = 0
            inited_categories = {}
            original_categories = []
            extractListCats(catsOzon=catsOzon,
                            inited_categories=inited_categories,
                            original_categories=original_categories
                            )
            types_dict, all_attributes = getCategoryTypes(catsOzon=catsOzon)

            def getCategoryName(category_id):
                for k, v in catsOzon.items():
                    for category in v:
                        if category[1] == category_id: return category[0]

            names = {}
            required = set()

            for k, v in all_attributes.items():
                for category in v:
                    cat_name = getCategoryName(category)
                    names[cat_name] = [('id', category)]
                    for attribute in v[category]:
                        names[cat_name].append(attribute['name'])
                        if attribute['is_required']:
                            required.add(attribute['name'])
            def add_item_by_category_name(my_dict, category_name, item):
                for key, array in my_dict.items():
                    if key[0] == category_name:
                        array.append(item)
                        return
            def itemRemains(i):
                print(f'Выполнено: {round(float(i/newItems)*100, 3)}%')

            def get_category_selection(product_type_lower, types_dict):
                product_type_mapping = {
                    'косметика, препараты': list(map(lambda x: x[0], types_dict['Интимная косметика'])),
                    'презервативы': list(map(lambda x: x[0], types_dict['Интимная косметика']))
                }

                return product_type_mapping.get(product_type_lower, original_categories)

            # Функция для добавления элемента по айди категории
            def add_item_by_category_id(my_dict, category_id, item):
                for key, array in my_dict.items():
                    if key[1] == category_id:
                        array.append(item)
                        return

            res = self.loadFromSpread(spreadID='1zlsbQWPkikBlRiznlkv6asIdRdaGBBHbmQu8M_6mfOU',
                                      column=['Name', 'Description', 'Type'],
                                      range_header='Полная база!A1:Z')

            morph = pymorphy2.MorphAnalyzer()
            knn = NearestNeighbors(n_neighbors=3, metric='cosine')
            vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
            for i in range(len(res[0])):


                """                ТУТ ВОЗНИКАЮТ ПРОБЛЕМЫ
                
                words_combination_only_cyrillic = set(filter(
                    lambda x: is_cyrillic(x),
                    (res[2][i]+res[1][i]).split())
                )
                inner_string = ' '.join(words_combination_only_cyrillic)
                
                """
                product_type_lower = res[2][i].lower()
                category_selection = get_category_selection(product_type_lower, catsOzon)

                results = self.initialize_category(original_categories=category_selection,
                                                   description=res[1][i]+res[0][i],
                                                   morph=morph,
                                                   knn=knn,
                                                   vectorizer=vectorizer)
                add_item_by_category_name(inited_categories, results[0], res[0][i])
                done+=1
                #print(results[0], "|--|", res[0][i])
                #itemRemains(done)


            return inited_categories

        return category_initializer()

    def outToExcel(self, out, path):
        # Проверяем тип данных out
        if isinstance(out, dict):
            # Находим максимальную длину массивов в словаре
            max_len = max(len(arr) for arr in out.values())

            # Заполняем недостающие значения массивов в словаре NaN
            for key, arr in out.items():
                if len(arr) < max_len:
                    out[key] = arr + [float('nan')] * (max_len - len(arr))

            # Преобразуем словарь в DataFrame
            df = pd.DataFrame(out)
        elif isinstance(out, (list, tuple)):
            # Преобразуем массив в DataFrame
            df = pd.DataFrame(out)
        else:
            raise ValueError("Неподдерживаемый тип данных. out должен быть словарем или массивом (list или tuple).")

        # Выгружаем DataFrame в Excel
        df.to_excel(path, encoding='cp1251')

    def initialize_category(self, original_categories, description, morph, knn, vectorizer):

        @lru_cache(maxsize=10000)
        def lemmatize(text):
         words = text.split()
         res = list()
         for word in words:
             p = morph.parse(word)[0]
             res.append(p.normal_form)

         return ' '.join(res)
        categories = [lemmatize(cat.lower().replace(">", "").replace("#", "")) for cat in original_categories]

        vectors = vectorizer.fit_transform(categories)

        knn.fit(vectors)

        def get_nearest_categories(desc):
             desc = lemmatize(desc.lower().replace(">", "").replace("#", ""))
             vec = vectorizer.transform([desc])
             distances, indices = knn.kneighbors(vec)
             return [original_categories[i] for i in indices[0]]

        return get_nearest_categories(description)

    def loadFromSpread(self, spreadID, range_header, column) -> list:
        # Запрос данных из таблицы
        result = self.config.SpreadsheetService.spreadsheets().values().get(spreadsheetId=spreadID,
                                                                            range=range_header).execute()
        values = result.get('values', [])

        # Преобразование в DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        df = df.dropna()

        # Получение списка значений из колонки(-ок)
        if isinstance(column, (int, str)):
            column_values = df[column].tolist()
            column_values = [int(x) for x in column_values]
            return [column_values]
        elif isinstance(column, list):
            column_values = []
            for col in column:
                column_values.append(df[col].tolist())
            return column_values
        else:
            return []

    def loadToSpreadSheet(self, sheets_service, spreadsheet_id, data, target_row_index):
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
        try:
            self.importCredentials()
            # self.downloadProducts()
        except src.ExceptionService.Exceptions.CustomError as e:
            print('[!] Ошибка.\nПодробнее: {0}'.format(e))
            sys.exit(1)
        self.createAPI()
        self.importArticularOptovik()
        existProducts = self.getExistArticuls()
        # self.checkBarcodes()

        items = self.checkNewProduct(self.importCats(),
                                     exist_products=existProducts)
        self.outToExcel(out=items,
                        path='./output.xlsx')

        print(items)

    def getExistArticuls(self) -> set:
        goods, errors, lieBrands = self.importProductListAPI()

        df = pd.DataFrame({'OK': len(goods), 'ERRORS': len(errors), 'LIE': len(lieBrands)}, index=['>>'])
        print(df)
        print(f"\n\n{pd.DataFrame({'errors': list(errors)})}")

        return goods

    def updateAttribute(self, attributes):
        """
        attributes:
        словарь с параметрами:
        items - list:
            {
            attributes - list:
                {
                complex_id - int
                id - int
                values - list:
                    {
                        dictionary_value_id - int
                        value - string
                    }
                }
            offer_id - string (артикул)
            }
        """
        if not isinstance(attributes, dict):
            raise src.ExceptionService.Exceptions.CustomError("Wrong attribute type:\
            \nGot:{0}\nExpected{1}".format(type(attributes), type(dict)))
        else:
            pass


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
