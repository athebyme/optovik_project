import sys
import re
import time
from collections import defaultdict
from typing import Any
from functools import lru_cache

import numpy as np
import pymorphy2
from numba import jit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

import pandas as pd

from src.AnyOtherCode import main

import src.ExceptionService.Exceptions
from config.Config import Config
from src.API import Api as API
from src.Product import Product
from src.Product.Product_Parser import ProductParser


# исправить все рег. шаблоны


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
                message='[!] Ошибка при получении API ключа. Проверьте Credentials',
                error_type=OSError
            )

    def checkFolders(self):
        pass

    def downloadProducts(self):
        main.Functions.download_universal([self.config.urlItems,
                                           self.config.urlStocks],
                                          path_def='../../SexOptovik')

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
    def process_products_import_list_api_with_decorator(func):
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

    @process_products_import_list_api_with_decorator
    def proccessProductArticulars(self, item):
        articular = self.cleanArticul(item['offer_id'], seller_code=str(self.config.id),
                                      marketplace=self.config.marketplace)
        if articular[0]:
            return 'good', articular[1]
        else:
            return 'error', articular[1]

    @process_products_import_list_api_with_decorator
    def getAllArticular(self, item):
        return item['offer_id']

    @staticmethod
    def filter_creator(filter_dict=None, **kwargs):
        if filter_dict is None:
            filter_params = {}
        else:
            filter_params = dict(filter_dict)

        if kwargs:
            for param, value in kwargs.items():
                filter_params[param] = value
        return filter_params

    def body_creator(self, filter, **kwargs):
        if filter is not None:
            request_body = {'filter': filter}
        else:
            request_body = {}
        request_body.update(kwargs)
        return self.API.createRequest(**request_body)

    def batch_divider(self, products, batch_size):
        return [products[i:i + batch_size] for i in range(0, len(products), batch_size)]

    @staticmethod
    @jit(nopython=True)
    def isInList(target, items):
        for i in range(len(items)):
            if target == items[i]:
                return i
        return -1

    @staticmethod
    def clean_barcodes(barcode):
        if re.search(r'#', barcode):
            match = re.search(r'#', barcode)
            if match:
                return barcode[:match.end() - 1]
        return barcode

    @staticmethod
    def product_info_attributes_decorator(filter_creator, body_creator, url_key, batch_divider):
        def actual_decorator(func):
            def wrapper(self, *args, **kwargs):
                results = defaultdict(list)
                filter_param = kwargs.get("filter", {})
                body_param = kwargs.get("body", {})
                if kwargs.get('batch') is None:
                    all_prods = kwargs.get("all_prods_ozon", [])
                    batch_size = kwargs.get('batch_size',
                                            1000)
                    divided_results = batch_divider(self, all_prods, batch_size)
                else:
                    divided_results = kwargs.get('batch')

                for i in range(len(divided_results)):
                    response_prod_attributes = self.API.sendResponse(
                        url=f'{self.API.urlOzon}{self.API.OzonRequestURL[url_key]}',
                        body=body_creator(self,
                                          filter=filter_creator(filter_param),
                                          **body_param
                                          )
                    ).json()

                    for item in response_prod_attributes['result']:
                        result_type, created_product = func(self, item, *args, **kwargs)
                        results[result_type].append(created_product)
                return results

            return wrapper

        return actual_decorator

    def get_prods_extra_info(self, divided_articulars, keys) -> dict:
        """
                Получение требуемой информации по товарам

        :param divided_articulars -> артикулы, разделенные по блокам
        :param keys -> список ключей, которые необходимо получить из метода. подробнее читать
        в документации метода get-product-info

        :return -> словарь типа ключ-значение по товару с OZON
        """
        articular_info = {}

        for divided_results in divided_articulars:
            response_prod_info = self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["get-products-info"]}',
                body=self.API.createRequest(offer_id=divided_results)
            ).json()

            items = response_prod_info.get('result', {}).get('items', [])
            for item in items:
                articular = item.get('offer_id', '')
                if articular:
                    articular_info[articular] = {}
                    for key in keys:
                        articular_info[articular][key] = str(
                            item.get(key,
                                     "[!] Error, check values"))  # значение по умолчанию может быть другим, если вы хотите
        return articular_info

    @product_info_attributes_decorator(filter_creator=filter_creator,
                                       body_creator=body_creator,
                                       url_key="product-info-attributes",
                                       batch_divider=batch_divider)
    def process_product(self,
                        product,
                        all_prods_optovik,
                        extra_information,
                        body,
                        filter,
                        batch=None,
                        batch_size=1000
                        ):
        cleanedArticular = self.cleanArticul(articular=product['offer_id'],
                                             seller_code=str(self.config.id),
                                             marketplace='oz',
                                             shortArticular=True
                                             )
        if cleanedArticular[0]:
            articularIndex = self.isInList(int(cleanedArticular[1]), all_prods_optovik) if 'Z1' not in cleanedArticular[
                1] else -1
        else:
            articularIndex = -1
        if 'id' in product['offer_id'] and articularIndex == -1:
            return "archive", product['id']
        updateState = False
        _updatedProduct = Product.Product.create_product(attribute_dict=product)
        if cleanedArticular[0] and (articularIndex != -1) and not pd.isna(self.ProductOptovik[1][articularIndex]) and (
                self.ProductOptovik[1][articularIndex] not in
                extra_information[
                    product['offer_id']][
                    'barcodes']):
            _updatedProduct.changeBarcode(self.clean_barcodes(self.ProductOptovik[1][articularIndex]) if not pd.isna(
                self.ProductOptovik[1][articularIndex]) else ProductParser.OzonDefaultBarcode)
            updateState = True
        elif len(extra_information[product['offer_id']][
                     'barcodes']) == 0 or 'OZNXXXXXXXXXX' in \
                extra_information[product['offer_id']]['barcodes']:
            newBarcode = ProductParser.OzonDefaultBarcode + \
                         extra_information[product['offer_id']]['sku']
            _updatedProduct.changeBarcode(newBarcode)
            updateState = True
        _updatedProduct.changeParam('price',
                                    extra_information[product['offer_id']]['price'])
        if updateState:
            return "update", _updatedProduct.attributes
        else:
            return "error", _updatedProduct.attributes

    def get_all_extra_info(self, divided_articulars, keys):
        articular_info = {}
        for divided_results in divided_articulars:
            response_prod_info = self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["get-products-info"]}',
                body=self.API.createRequest(offer_id=divided_results)
            ).json()

            items = response_prod_info.get('result', {}).get('items', [])
            for item in items:
                articular = item.get('offer_id', '')
                if articular:
                    articular_info[articular] = {}
                    for key in keys:
                        articular_info[articular][key] = str(
                            item.get(key, f"[!] Error: Check params, {key} is not found"))
        return articular_info

    def newCheckBarcodes(self, batch_size=1000):
        all_prods_ozon = self.getAllArticular()
        all_prods_optovik = np.array(self.ProductOptovik[0])
        divided_articulars = [all_prods_ozon[i:i + batch_size] for i in range(0, len(all_prods_ozon), batch_size)]
        keys = ['barcodes', 'price', 'fbo_sku']
        needProdsInformation = self.get_all_extra_info(divided_articulars, keys)

        results = defaultdict(list)
        for batch in divided_articulars:
            result = self.process_product(
                batch=batch,
                all_prods_optovik=all_prods_optovik,
                extra_information=needProdsInformation,
                body={"limit": 1000},
                filter={"offer_id": batch,
                        "visibility": "ALL"}
            )
            results.update(result)

    def checkBarcodes(self):
        @jit(nopython=True)
        def isInList(target, items):
            for i in range(len(items)):
                if target == items[i]:
                    return i
            return -1

        def clean_barcodes(barcode):
            if re.search(r'#', barcode):
                match = re.search(r'#', barcode)
                if match:
                    return barcode[:match.end() - 1]
            return barcode

        all_prods = self.getAllArticular()
        needProdsInformation = self.get_all_extra_info(all_prods, keys=['barcodes', 'price', 'fbo_sku'])

        archive_list = []
        upload_list = []

        ozon_import_limit = 100

        batch_size = 1000
        divided_results = [all_prods[i:i + batch_size] for i in range(0, len(all_prods), batch_size)]
        c = 0
        prods = np.array(self.ProductOptovik[0])
        for i in range(len(divided_results)):
            response_prod_attributes = self.API.sendResponse(
                url=f'{self.API.urlOzon}{self.API.OzonRequestURL["product-info-attributes"]}',
                body=self.API.createRequest(
                    filter=self.API.createFilter(
                        offer_id=divided_results[i],
                        visibility="ALL"
                    ),
                    limit=1000
                )
            ).json()

            for k in range(len(response_prod_attributes['result'])):
                c += 1
                cleanedArticular = self.cleanArticul(articular=response_prod_attributes['result'][k]['offer_id'],
                                                     seller_code=str(self.config.id),
                                                     marketplace='oz',
                                                     shortArticular=True
                                                     )
                if cleanedArticular[0]:
                    articularIndex = isInList(int(cleanedArticular[1]), prods) if 'Z1' not in cleanedArticular[
                        1] else -1
                else:
                    articularIndex = -1
                if 'id' in response_prod_attributes['result'][k]['offer_id'] and articularIndex == -1 or 'Z' in \
                        response_prod_attributes['result'][k]['offer_id']:
                    archive_list.append(response_prod_attributes['result'][k]['id'])
                updateState = False
                newBarcode = ""
                _updatedProduct = Product.Product.create_product(attribute_dict=response_prod_attributes['result'][k])
                if cleanedArticular[0] and (articularIndex != -1) and (self.ProductOptovik[1][articularIndex] not in
                                                                       needProdsInformation[
                                                                           response_prod_attributes['result'][k][
                                                                               'offer_id']]['barcodes']):
                    _updatedProduct.changeBarcode(clean_barcodes(self.ProductOptovik[1][articularIndex]) if not pd.isna(
                        self.ProductOptovik[1][articularIndex]) else ProductParser.OzonDefaultBarcode)
                    updateState = True
                elif len(needProdsInformation[response_prod_attributes['result'][k]['offer_id']][
                             'barcodes']) == 0 or 'OZNXXXXXXXXXX' in \
                        needProdsInformation[response_prod_attributes['result'][k]['offer_id']]['barcodes']:
                    newBarcode = ProductParser.OzonDefaultBarcode + \
                                 needProdsInformation[response_prod_attributes['result'][k]['offer_id']]['sku']
                    _updatedProduct.changeBarcode(newBarcode)
                    updateState = True
                _updatedProduct.changeParam('price',
                                            needProdsInformation[response_prod_attributes['result'][k]['offer_id']][
                                                'price'])
                if updateState:
                    upload_list.append(_updatedProduct.attributes)

                """
                ПЕРЕД ЗАПУСКОМ ПРОВЕРИТЬ КОД!
                """
                if len(archive_list) % 100 == 0 or (
                        len(archive_list) != 0 and i == len(divided_results) and k + 1 == len(
                    response_prod_attributes['result'])):
                    print("Статус архивирования:", self.API.sendResponse(
                        url=self.API.urlOzon + self.API.OzonRequestURL['archive-items'],
                        body=self.API.createRequest(
                            product_id=archive_list
                        )).json()['result'])
                    archive_list = []
                    continue
                if len(upload_list) % ozon_import_limit == 0 or (
                        len(upload_list) != 0 and i + 1 == len(divided_results) and k + 1 == len(
                    response_prod_attributes['result'])):
                    task_id_list = self.API.sendResponse(
                        url=self.API.urlOzon + self.API.OzonRequestURL['product-import'],
                        body=self.API.createRequest(
                            items=upload_list
                        )
                    ).json()['result']
                    checkStatus = self.API.sendResponse(
                        url=self.API.urlOzon + self.API.OzonRequestURL['product-import-check'],
                        body=self.API.createRequest(
                            task_id=task_id_list['task_id']
                        )
                    ).json()['result']
                    upload_list = []

                self.itemRemains(c, len(all_prods), text='Выгрузка баркодов')

    def importArticularOptovik(self):
        df = pd.read_csv('SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')
        self.ProductOptovik = [list(df.iloc[:, 0]), list(df.iloc[:, 14])]

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

    @staticmethod
    def itemRemains(i, total_items_count, text):
        ratio = 100.0 / total_items_count
        percentage = round(i * ratio, 3)
        sys.stdout.write(f'\r{text}. Выполнено: {percentage}%')
        sys.stdout.flush()

    def checkNewProduct(self, catsOzon, exist_products, df=None):
        def calculateNewItems(df, exist_articuls) -> int:
            totally = 0
            productInfo = df.iloc[:, 0]
            for i in range(len(productInfo)):
                if df.iloc[i, 0] not in exist_articuls:
                    totally += 1
            print(f'\nВсего найдено новых товаров: {totally}')
            return totally

        if df is None:
            df = pd.read_csv('SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')

        """
        [!] на этом этапе могут возникнуть ошибки ненахождения товаров [!]
        
            проверить данные dropna в случае ошибки. использовать другой опорный столбец
        -----------------------------------------------------------------------------------
        """

        productInfo = df.iloc[:, 3]
        productInfo.dropna(inplace=True)

        "----------------------------------------------------------------------------------"

        new_items_count = calculateNewItems(df=df,
                                            exist_articuls=exist_products)

        def unpack_json_category_types(category_ids) -> list:
            total_types_list = []
            all_attributes = {}

            # ==============================================================
            required = []
            # ======^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^==================

            if isinstance(category_ids, (str, int)):
                category_ids = [category_ids]
            json_response_all = self.API.sendResponse(
                url=self.API.urlOzon + self.API.OzonRequestURL["category-attributes"],
                body=self.API.createRequest(category_id=category_ids, attribute_type="ALL", language="DEFAULT")
            ).json()

            # ============================================================
            json_response_required = self.API.sendResponse(
                url=self.API.urlOzon + self.API.OzonRequestURL["category-attributes"],
                body=self.API.createRequest(category_id=category_ids, attribute_type="REQUIRED", language="DEFAULT")
            ).json().get('result')
            for item in json_response_required:
                required.append(item)

            # =========^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^=============

            for attributes in json_response_all['result']:
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
            return [total_types_list, all_attributes, required]

        def extractListCats(catsOzon, inited_categories, original_categories):
            for k, v in catsOzon.items():
                for category in v:
                    inited_categories[category[0]] = []
                    if category[0] not in original_categories:
                        original_categories.append(category[0])

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        def getCategoryTypes(catsOzon, type=None):
            """

                    Дополнительный функционал для получнеия типов по категориям из списка озона

                    создавалось для лучшей работы определителя категорий, но результат себя не оправдал

            :param catsOzon -> dict
            :param type -> какого типа нужно получить результат
            example:
                "Секс-игрушки": [(Вибратор, 12345), ...]
            """
            if type is None:
                type = dict()
            all_types = {}
            all_attributes = {}
            all_required = {}
            for k, v in catsOzon.items():
                # Делаем разбивку категорий на пакеты по 20
                categories_chunks = list(chunks(v, 20))
                for chunk in categories_chunks:
                    category_ids = [category[1] for category in chunk]  # извлекаем идентификаторы категорий
                    res = unpack_json_category_types(category_ids=category_ids)
                    all_types[k] = res[0]
                    all_attributes[k] = res[1]
                    all_required[k] = res[2]

            if isinstance(type, dict):
                return all_types, all_attributes

        def category_initializer() -> dict:
            done = 0
            inited_categories = {}
            original_categories = []
            extractListCats(catsOzon=catsOzon,
                            inited_categories=inited_categories,
                            original_categories=original_categories
                            )

            def add_item_by_category_name(my_dict, category_name, item):
                for key, array in my_dict.items():
                    if key == category_name:
                        array.append(item)
                        return

            # Функция для добавления элемента по айди категории
            def add_item_by_category_id(my_dict, category_id, item):
                for key, array in my_dict.items():
                    if key[1] == category_id:
                        array.append(item)
                        return

            def get_category_selection(product_type_lower, types_dict):
                product_type_mapping = {
                    'косметика, препараты': list(map(lambda x: x[0], types_dict['Интимная косметика'])),
                    'презервативы': list(map(lambda x: x[0], types_dict['Интимная косметика']))
                }

                return product_type_mapping.get(product_type_lower, original_categories)

            results = getCategoryTypes(catsOzon=catsOzon)
            res = self.loadFromSpread(spreadID='1zlsbQWPkikBlRiznlkv6asIdRdaGBBHbmQu8M_6mfOU',
                                      column=['Name', 'Description', 'Type', 'ID'],
                                      range_header='Полная база!A1:Z')

            morph = pymorphy2.MorphAnalyzer()
            knn = NearestNeighbors(n_neighbors=3, metric='cosine')
            vectorized = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
            for i in range(len(res[0])):
                product_type_lower = res[2][i].lower()
                category_selection = get_category_selection(product_type_lower, catsOzon)

                results = self.initialize_category(original_categories=category_selection,
                                                   description=res[1][i] + res[0][i],
                                                   morph=morph,
                                                   knn=knn,
                                                   vectorizer=vectorized)
                add_item_by_category_name(inited_categories, results[0], res[3][i])
                done += 1
                self.itemRemains(done, new_items_count, text='Обработка категорий новых товаров')
                # itemRemains(done)

            return inited_categories

        return category_initializer()

    def parse_products(self, category_ids, categories_ozon, df):
        all_ids_with_category = [(cat_id, int(item_id)) for cat_id, ids in category_ids.items() for item_id in ids]
        all_ids_only = [item_id for _, item_id in all_ids_with_category]
        filtered_items = df[df.iloc[:, 0].isin(all_ids_only)]

        morph = pymorphy2.MorphAnalyzer()
        knn = NearestNeighbors(n_neighbors=3, metric='cosine')
        vectorized = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))

        for i in range(len(filtered_items)):
            category_name = -1
            for item in all_ids_with_category:
                if item[1] == filtered_items.iloc[i][0]:
                    category_name = item[0]
                    break
            category_id = -1
            for k, v in categories_ozon.items():
                for category in v:
                    if category[0] == category_name:
                        category_id = category[1]
                        break
            category_attributes_required = self.API.sendResponse(
                url=self.API.urlOzon + self.API.OzonRequestURL["category-attributes"],
                body=self.API.createRequest(
                    attribute_type="REQUIRED",
                    category_id=[category_id],
                    language="DEFAULT"
                )
            ).json()
            category_attributes_required = category_attributes_required.get('result')[0].get('attributes')

            product_instance = ProductParser(filtered_items.iloc[i],
                                             API=self.API,
                                             morph=morph,
                                             knn=knn,
                                             vectorized=vectorized,
                                             required_attributes=category_attributes_required,
                                             category_id=category_id
                                             )

    def parse_instances(self, stack):
        for i in range(len(stack)):
            stack[i].parse()

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
            df = pd.DataFrame(out, index=None)
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
        # if 'A1' in range_header and False:
        #     df = pd.DataFrame(values)
        # else:
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
                if isinstance(col, int):
                    column_values.append(df[col].tolist())
                elif isinstance(col, str):
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
        print(f'\nПриветствую Вас, {self.config.shopName}\n')
        try:
            self.importCredentials()
            # self.downloadProducts()
        except src.ExceptionService.Exceptions.CustomError as e:
            print('[!] Ошибка.\nПодробнее: {0}'.format(e))
            sys.exit(1)
        self.createAPI()
        self.importArticularOptovik()
        existProducts = self.getExistArticuls()
        # self.newCheckBarcodes(batch_size=1000)
        # self.checkBarcodes()
        category_list_ozon = self.importCats()
        df = self.load_database_product(columns=[x for x in range(17)],
                                        loading_type='manual')

        items_by_category = self.get_categories('spread', exist_prods=existProducts,
                                                category_list_ozon=category_list_ozon)

        self.parse_products(items_by_category,
                            category_list_ozon,
                            df=df)

    def get_categories(self, _type, exist_prods, category_list_ozon=None):
        if _type == 'manual':
            return self.get_cats_manual(category_list_ozon=category_list_ozon,
                                        exist_prods=exist_prods)
        elif _type == 'spread':
            return self.get_cats_from_spread(exist_prods=exist_prods)

    def get_cats_from_spread(self, exist_prods) -> dict:
        categories = self.loadFromSpread(spreadID='1seOHrVIUluOxK3yXz3lQSHtZ84FyrGr-i0kQMAZ8BIE',
                                         range_header='cats!A1:Z',
                                         column=['ID', 'CATEGORY']
                                         )

        items_by_category = defaultdict(list)
        for i in range(len(categories[1])):
            if categories[0][i] not in exist_prods:
                items_by_category[categories[1][i]].append(categories[0][i])
        return items_by_category

    def get_cats_manual(self, category_list_ozon, exist_prods):
        return self.checkNewProduct(category_list_ozon,
                                    exist_products=exist_prods)

    def load_database_product(self, columns, loading_type='manual'):
        if loading_type == 'manual':
            df = pd.read_csv('SexOptovik/all_prod_info.csv', sep=';', encoding='cp1251')
            return df
        elif loading_type == 'api':
            return pd.DataFrame(self.loadFromSpread(spreadID='1nImAUNxnY_rw1jkut-HihxB0rUFPDipJFgeCfwXTCSg',
                                                    column=columns,
                                                    range_header='all-prod-info!A1:Z')
                                )

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
            raise src.ExceptionService.Exceptions.CustomError(message=
                                                              "Wrong attribute type:\nGot:{0}\nExpected{1}".format(
                                                                  type(attributes), type(dict)),
                                                              error_type=TypeError)
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
