from functools import lru_cache

from src.Product import Product
from src.dataConfigs.regEx import rePattern
from src.Rich.RichPattern import Rich

import re
import pandas as pd


class ProductParser:
    OzonDefaultBarcode = 'OZN'

    def __init__(self, data, **kwargs):
        """
            Передаем строку из data frame с данными по товару
        """
        self.attribute_mapping_required = None
        self.attributes = None
        self.json = None
        self.API = None
        attributes = ['knn', 'morph', 'vectorized', 'API', 'required_attributes', 'category_id']
        for attr in attributes:
            setattr(self, attr, kwargs.get(attr))
        self.data = data
        self.p = rePattern()

        self.parse()
        self.p = None

    def parse(self):
        self.json = self.create_json()
        self.add_to_json(param='category_id',
                         new_value=self.category_id,
                         is_attribute=False
                         )
        self.create_attribute_mapping(category_id=self.category_id)
        self.fill_required_attributes()
        self.fill_total_attributes()
        return Product.Product.create_product(attribute_dict=self.attributes)

    def add_to_json(self, param, new_value, is_attribute, changing=False, attribute_id=None):
        if not is_attribute:
            self.json[param] = new_value
        else:
            if changing:
                for i in range(len(self.json['attributes'])):
                    if self.json['attributes'][i]['id'] == attribute_id:
                        self.json['attributes'][i] = new_value
                        break
            else:
                self.json['attributes'].append(new_value)

    @staticmethod
    def create_json():
        return {
            "category_id": "",
            "depth": 300,
            "dimension_unit": "mm",
            "height": 150,
            "images": [],
            "primary_image": "",
            "name": "",
            "attributes": [],
            "complex_attributes": [],
            "barcode": "",
            "currency_code": "RUB",
            "offer_id": "",
            "price": "",
            "old_price": "99999",
            "premium_price": "",
            "vat": "0",
            "weight": 600,
            "weight_unit": "g",
            "width": 110
        }

    def parse_sizes(self, INPUT_DATA, keywords=None):
        translation_dict = {
            "длина": "length",
            "глубина": "depth",
            "ширина": "width",
            "объем": "volume",
            "вес": "weight",
            "диаметр": "diameter",
            "общий": "common"
        }

        if keywords is None:
            keywords = self.p.ExtractParams
        if type(INPUT_DATA) is not list:
            INPUT_DATA = [INPUT_DATA]
        result = {}
        for text in INPUT_DATA:
            for word in keywords:
                pattern = r'{}(?:\s+([\w.-]+(?:\s+[\w.-]+)*))?\s+(\d+[\.,]?\d*)(?:\s*-\s*(\d+[\.,]?\d*))?'.format(word)
                matches = re.findall(pattern, text)
                for match in matches:
                    value1 = match[1].replace(',', '.')
                    value2 = match[2].replace(',', '.') if match[2] else value1
                    value1, value2 = float(value1), float(value2)
                    words_between = match[0] if match[0] else ''
                    if words_between == '':
                        words_between = 'общий'
                    word_english = translation_dict.get(word, word)
                    words_between_english = translation_dict.get(words_between, words_between)

                    if word_english not in result:
                        result[word_english] = {words_between_english: {'min': value1, 'max': value2}}
                    else:
                        result[word_english] = [result[word_english],
                                                {words_between_english: {'min': value1, 'max': value2}}]
        return result

    def get_knn(self, sample_of, text):

        @lru_cache(maxsize=10000)
        def lemmatize(text_sample):
            words = text_sample.split()
            res = list()
            for word in words:
                p = self.morph.parse(word)[0]
                res.append(p.normal_form)

            return ' '.join(res)

        categories = [lemmatize(cat.lower().replace(">", "").replace("#", "")) for cat in sample_of]

        vectors = self.vectorized.fit_transform(categories)

        self.knn.fit(vectors)

        def get_nearest_categories(desc):
            desc = lemmatize(desc.lower().replace(">", "").replace("#", ""))
            vec = self.vectorized.transform([desc])
            distances, indices = self.knn.kneighbors(vec)
            return [sample_of[i] for i in indices[0]]

        return get_nearest_categories(text)

    def get_manual_information(self, category_id, attribute_id, limit=50) -> list:
        return self.API.sendResponse(
            url=self.API.urlOzon + self.API.OzonRequestURL["category-attribute-values"],
            body=self.API.createRequest(category_id=category_id,
                                        attribute_id=attribute_id,
                                        language="DEFAULT",
                                        limit=limit,
                                        last_value_id=0
                                        )
        ).json()['result']

    def get_all_dictionary_values(self, category_id, attribute_id):
        various = self.get_manual_information(category_id=category_id,
                                              attribute_id=attribute_id)
        result = []
        for param in various:
            result.append(tuple([param['id'], param['value']]))
        return result

    def get_best_match(self, category_id, attribute_id, text, best_of=1) -> list:

        def create_map(values):
            res = {}
            for item in values:
                res[item[1]] = item[0]
            return res

        all_values = self.get_all_dictionary_values(category_id=category_id,
                                                    attribute_id=attribute_id)

        mapping = create_map(all_values)

        result_type = self.get_knn(sample_of=[x[1] for x in all_values],
                                   text=text)

        if best_of > 1:
            ...
        else:
            return [{"dictionary_id": mapping.get(result_type[0]), "value": result_type[0]}]

    def get_model(self):
        model = self.data.iloc[1]
        match = re.search(r'-([\w\d]{1,4})$', model)

        if match:
            fragment = match.group(1)
            stripped_fragment = re.sub(r'[a-zA-Z]*$', '', fragment)
            if re.fullmatch(r'\d*', stripped_fragment):
                return model[:match.start()]

            return model[:match.start()] + '-' + stripped_fragment
        return re.sub(r'[a-zA-Z]*$', '', model)

    @staticmethod
    def get_sex(text) -> list:

        types = [("Мужской", 22880),
                 ("Женский", 22881)]

        mapping = {
            "для геев": [{"dictionary_id": types[0][1], "value": types[0][0]}],
            "для женщин": [{"dictionary_id": types[1][1], "value": types[1][0]}],
            "для женщин и мужчин": [{"dictionary_id": types[1][1], "value": types[1][0]},
                                    {"dictionary_id": types[0][1], "value": types[0][0]}],
            "для лесбиянок": [{"dictionary_id": types[1][1], "value": types[1][0]}],
            "для мужчин": [{"dictionary_id": types[0][1], "value": types[0][0]}],
            "для пары": [{"dictionary_id": types[1][1], "value": types[1][0]},
                         {"dictionary_id": types[0][1], "value": types[0][0]}],
            "default": [{"dictionary_id": types[1][1], "value": types[1][0]},
                        {"dictionary_id": types[0][1], "value": types[0][0]}]
        }
        return mapping.get(text.lower())

    def get_color(self, category_id) -> list:
        values = []

        color_data = re.split(r',', self.data.iloc[9])
        i = 0
        for color in color_data:
            best_match = self.get_best_match(category_id=category_id,
                                             attribute_id=10096,
                                             text=color)[0]

            for k, v in best_match.items():
                values.append({})
                values[i][k] = v
            i += 1
        return values

    @staticmethod
    def get_volume(volume_text) -> list:
        values = [{"value": re.sub(r'[^0-9]', '', volume_text)}]
        return values

    def create_attribute_mapping(self, category_id):

        """
                в mapping храним массивы словарей вида:
                [{
                    "dictionary_id": int      <- если получилось извлечь
                    "value": str              <- значение
                }
                ...
                ]
        """

        self.attribute_mapping_required = {
            85: [{"value": self.data.iloc[4]}],  # бренд
            8229: self.get_best_match(category_id=category_id, attribute_id=8229,
                                      text=self.data.iloc[2] if not pd.isna(self.data.iloc[2]) else self.data.iloc[3]),
            # тип
            9048: [{"value": self.data.iloc[1]} if not pd.isna(self.data.iloc[1]) else {
                "value": f"model-{self.data.iloc[0]}"}],  # 'Название модели (для объединения в одну карточку)'
            10350: [{"value": 35}],  # макс температура
            10351: [{"value": 10}],  # мин температура
            22773: self.get_best_match(category_id=category_id, attribute_id=22773,
                                       text=self.data.iloc[2] + self.data.iloc[3]),  # 'Вид кондитерского изделия 18+'
            31: [{"value": self.data.iloc[4]}],  # 'Бренд в одежде и обуви'

            4298: None,  # 'Российский размер (обуви)'
            4295: None,  # 'Российский размер'

            # """
            # Детская одежда: 98 / 104 / 110 / 116 и т. д.
            # Взрослая одежда: 44 / 46 / 48 / 50 и т. д.
            # Бюстгальтеры: 65A / 70B / 70C / 80D и т. д.
            # Колготки: 1 / 2 / 3 / 4 и т. д.
            # Шапки: 54 / 55 / 56 / 57 и т. д.
            # Перчатки: 7 / 7,5 / 8 / 8,5 и т. д.
            # Обувь: 38 / 39 / 40 / 41 и т. д.
            # Смежные размеры укажите последовательно через точку с запятой (например: 42;44;46).
            # """

            9070: [{"value": True}],  # 'Признак 18+'
            # """
            # 'ВАЖНО!!! Признак для товаров, которые содержат эротику, сцены секса,
            #  изображения с нецензурными выражениями, даже если они написаны частично или со спец. символами,
            #   а также для товаров категории 18+ (только для взрослых).'
            # """

            9163: self.get_sex(self.data.iloc[8]) if not pd.isna(self.data.iloc[8]) else self.get_sex("default"),
            # 'Пол'
            8292: [{"value": self.get_model()}],  # 'Объединить на одной карточке'
            10096: self.get_color(category_id=category_id),  # 'Цвет товара'
            8050: [{"value": f"{self.data.iloc[2]}; {self.data.ilco[7]}"}],  # 'Состав'
            8163: self.get_volume(self.data.iloc[2] if pd.isna(self.data.iloc[10]) else self.data.iloc[10]),
            # 'Объем, мл'
            8205: [{"value": 65}],
            9782: [{"dictionary_id": 970661099, "value": "Не опасен"}],
            4180: [{"value": f"{self.get_best_match(category_id=category_id, attribute_id=8229, text=self.data.iloc[2] if not pd.isna(self.data.iloc[2]) else self.data.iloc[3])['value']}," #тип
                             f"{self.data.iloc[4]}," #бренд
                             f"{self.get_model()}"} #модель
                    ], #'Название'
            # """
            # Название пишется по принципу:
            #     Тип + Бренд + Модель (серия + пояснение) + Артикул производителя + , (запятая) + Атрибут
            #     Название не пишется большими буквами (не используем caps lock).
            #     Перед атрибутом ставится запятая. Если атрибутов несколько, они так же разделяются запятыми.
            #     Если какой-то составной части названия нет - пропускаем её.
            #     Атрибутом может быть: цвет, вес, объём, количество штук в упаковке и т.д.
            #     Цвет пишется с маленькой буквы, в мужском роде, единственном числе.
            #     Слово цвет в названии не пишем.
            #     Точка в конце не ставится.
            #     Никаких знаков препинания, кроме запятой, не используем.
            #     Кавычки используем только для названий на русском языке.

            #     Примеры корректных названий:

            #     Смартфон Apple iPhone XS MT572RU/A, space black
            #     Кеды Dr. Martens Киноклассика, бело-черные, размер 43
            #     Стиральный порошок Ariel Магия белого с мерной ложкой, 15 кг
            #     Соус Heinz Xtreme Tabasco суперострый, 10 мл
            #     Игрушка для животных Четыре лапы "Бегающая мышка" БММ, белый
            # """


            4184: None  # 'ISBN' << пропускаем
        }

    def fill_values(self, attribute) -> list:
        """
                     [
                        {
                            "dictionary_value_id": 61577
                        }
                    ]

        OR

                    [
                        {
                            "value": "iHome-5"
                        }
                    ]
        """

        return self.get_mapping_result(attribute_id=attribute['id'])

    def get_mapping_result(self, attribute_id):
        return self.attribute_mapping_required.get(attribute_id, None)

    def fill_required_attributes(self):

        """

                НУЖНО, ЧТОБЫ В "values" ПОПАДАЛО:

                1) DICTIONARY_ID -> ИДЕНТИФИКАТОР ДЛЯ АТРИБУТА ИЗ СПРАВОЧНИКА.
                *ЕСЛИ СПРАВОЧНИКА НЕТ! -> НЕ НУЖНО ЗАПОЛНЯТЬ

                2) VALUE -> ЗАВИСИТ ОТ is_collection = true OR false

                ЕСЛИ TRUE: ПОДУМАТЬ, КАК ОБРАБОТАТЬ СЛУЧАИ, ГДЕ МОЖНО УКАЗАТЬ НЕСКОЛЬКО ЗНАЧЕНИЙ
                ЕСЛИ FALSE: :str: value

                т.е. примеры

                1) если справочник есть, значение одно
                "values":[
                    {
                        "dictionary_value_id": int
                        "value": str
                    }
                ]


                2) если справочника нет, значение одно
                "values":[
                    {
                        "value": str
                    }
                ]


                3) если справочник есть, значений несколько
                "values":[
                    {
                        "dictionary_value_id": int,
                        "value": str
                    },
                    {
                        "dictionary_value_id": int,
                        "value": str
                    }
                ]


        """

        for attribute in self.required_attributes:
            self.add_to_json(is_attribute=True,
                             changing=False,
                             new_value={
                                 "complex_id": 0,
                                 "id": attribute['id'],
                                 "values": self.fill_values(attribute)
                             },
                             param=None)
    def fill_total_attributes(self):
        sizes = self.parse_sizes(INPUT_DATA=self.data.iloc[10])
        ...