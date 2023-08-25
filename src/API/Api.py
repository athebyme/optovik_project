import requests
import json
import pandas as pd

import src.ExceptionService.Exceptions


class ServiceAPI:
    urlOzon = 'https://api-seller.ozon.ru'
    urlSpreadSheet = 'https://sheets.googleapis.com'
    ContentType = "application/json"

    """
    Загрузка и обновление товаров
    
    В результате работы метода вы получите task_id — номер задания на загрузку кода активации.
    
    /v2/product/list
    
    Метод позволяет использовать фильтры, чтобы разбить товары на группы 
    по статусу видимости или отслеживать изменение их статуса с помощью идентификатора товара.
    
    Метод возвращает пару значений offer_id и product_id — они нужны практически во всех запросах для
    идентификации товара, с которым будет производиться действие. Если вы загружали товары через шаблон,
    используйте этот метод для получения offer_id и product_id, чтобы в дальнейшем работать по API с товарами.
    """
    OzonRequestURL = {
        "product-import": "/v2/product/import",
        "product-import-geo-restrictions-catalog": "/v2/products/get-geo-restrictions-catalog-by-filter",
        "product-import-check": "/v1/product/import/info",
        "product-import-list": "/v2/product/list",


        "get-product-info": "/v2/product/info",
        "get-products-info": "/v2/product/info/list",

        "product-import-image": "/v1/product/pictures/import",
        "product-import-image-check": "/v1/product/pictures/info",

        "product-info-attributes": "/v3/products/info/attributes",
        "product-update-attributes": "/v1/product/attributes/update",

        "category-tree": "/v2/category/tree",
        "category-attributes": "/v3/category/attribute",
        "category-attribute-values": "/v2/category/attribute/values",

        "archive-items": "/v1/product/archive"
    }

    GoogleRequestURL = {
        "append": "/v4/spreadsheets/"
    }

    header = None

    def __init__(self, Host, ClientId, ApiKey, ContentType):
        self.header = {
            "Host": Host,
            "Client-Id": ClientId,
            "Api-Key": ApiKey,
            "Content-Type": ContentType
        }

    def sendResponse(self, url, body):
        response = requests.post(url, headers=self.header, data=json.dumps(body))
        try:
            response.raise_for_status()  # Генерирует исключение при неудачном запросе (например, ошибка 404)
            return response
        except requests.exceptions.RequestException as e:
            raise src.ExceptionService.Exceptions.CustomError(message="[!] Ошибка при отправке запроса: {0}\n"
                                                              "Подробно:{1}".format(e,json.dumps(response.json())),
                                                              error_type=requests.RequestException)

    def exportCsvLog(self, response):
        data_dict = pd.DataFrame.from_dict(json.loads(response)).T  # Развертываем словари во вложенных столбцах
        data_dict.to_csv(path_or_buf='./API_LOG.csv', index=False, header=True)  # Сохраняем DataFrame в CSV файл без индекса

    def createFilter(self, **kwargs) -> dict:
        """
    Создает словарь с фильтром на основе переданных аргументов.

    Args:
        **kwargs: Именованные аргументы с параметрами фильтра.

    Returns:
        dict: Словарь с фильтром.

    Possible Arguments:
        <offer_id>    -  Array of strings
        <product_id>  -  Array of strings <int64>
        <visibility>  -  string
        <last_id>     -  string
        <limit>       -  integer <int64>
        <sort_by>     -  string
        <sort_dir>    -  string
    """
        filter_dict = {key: value for key, value in kwargs.items() if value is not None}
        return filter_dict
    def createRequest(self, **kwargs) -> dict:
        """
    Создает тело запроса (body) с параметрами.

    Args:
        **kwargs: Именованные аргументы с параметрами запроса.

    Returns:
        dict: Словарь с телом запроса.

    """
        request = {key: value for key, value in kwargs.items() if value is not None}
        return request
