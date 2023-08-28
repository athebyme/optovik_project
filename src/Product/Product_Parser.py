from functools import lru_cache

from src.dataConfigs.regEx import rePattern
from src.Rich.RichPattern import Rich

import re
import pandas as pd
import html


class ProductParser:
    OzonDefaultBarcode = 'OZN'

    def __init__(self, data, **kwargs):
        """
            Передаем строку из data frame с данными по товару
        """
        self.sizes = None
        self.attribute_mapping_required = None
        self.attributes = None
        self.json = None
        self.API = None

        attributes = ['knn', 'morph', 'vectorized', 'API', 'category_attributes', 'category_id', 'config', 'annotation']
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
        self.create_sizes_dictionary(size_data=self.data.iloc[10])
        self.create_attribute_mapping(category_id=self.category_id)
        self.fill_attributes()
        # self.check_sizes()
        self.fill_total_attributes()
        # return Product.Product.create_product(attribute_dict=self.json)

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

    def create_sizes_dictionary(self, size_data):
        self.sizes = self.get_sizes(INPUT_DATA=size_data)

    def get_sizes(self, INPUT_DATA, keywords=None):
        translation_dict = {
            "длина": "length",
            "глубина": "depth",
            "ширина": "width",
            "объем": "volume",
            "вес": "weight",
            "диаметр": "diameter",
            "общий": "default"
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

    def get_knn(self, sample_of, text, k=1):

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

        self.knn.n_neighbors = k
        self.knn.fit(vectors)

        def get_nearest_categories(desc):
            desc = lemmatize(desc.lower().replace(">", "").replace("#", ""))
            vec = self.vectorized.transform([desc])
            distances, indices = self.knn.kneighbors(vec)
            return [sample_of[i] for i in indices[0]]

        return get_nearest_categories(text)

    def get_manual_information(self, category_id, attribute_id, limit=50, last_id=0) -> dict:
        return self.API.sendResponse(
            url=self.API.urlOzon + self.API.OzonRequestURL["category-attribute-values"],
            body=self.API.createRequest(category_id=category_id,
                                        attribute_id=attribute_id,
                                        language="DEFAULT",
                                        limit=limit,
                                        last_value_id=last_id
                                        )
        ).json()

    def get_all_dictionary_values(self, category_id, attribute_id, limit):
        various = self.get_manual_information(category_id=category_id,
                                              attribute_id=attribute_id,
                                              limit=limit)
        result = []
        if attribute_id == 9461 and False:
            while various['has_next'] or len(various.get('result')) != 0:
                various = various.get('result')
                for param in various:
                    result.append(tuple([param['id'], param['value']]))
                last_id = various[(len(various) - 1)]['id']
                various = self.get_manual_information(category_id=category_id,
                                                      attribute_id=attribute_id,
                                                      limit=limit,
                                                      last_id=last_id)
        else:
            various = various.get('result')
            for param in various:
                result.append(tuple([param['id'], param['value']]))
        return result

    def get_best_match(self, category_id, attribute_id, text, best_of=1, limit=50) -> list:

        def create_map(values_dict):
            res = {}
            for item in values_dict:
                res[item[1]] = item[0]
            return res

        all_values = self.get_all_dictionary_values(category_id=category_id,
                                                    attribute_id=attribute_id,
                                                    limit=limit
                                                    )

        mapping = create_map(all_values)

        result_type = self.get_knn(sample_of=[x[1] for x in all_values],
                                   text=text,
                                   k=best_of)

        if best_of > 1:
            values = []
            for i in range(best_of):
                values.append({"dictionary_id": mapping.get(result_type[i]), "value": result_type[i]})
            return values

        else:
            return [{"dictionary_id": mapping.get(result_type[0]), "value": result_type[0]}]

    @staticmethod
    def get_model(model_data):
        model = model_data
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
        for color in color_data:
            best_match = self.get_best_match(category_id=category_id,
                                             attribute_id=10096,
                                             text=color)[0]

            values.append(best_match)
        return values

    @staticmethod
    def get_integer_values(text) -> str:
        return re.sub(r'[^0-9]', '', str(text))

    @staticmethod
    def get_decimal_values(text) -> str:
        return re.sub(r'[^0-9.]', '', text.replace(',', "."))

    def get_product_type(self, product_information):
        return self.get_best_match(category_id=self.category_id, attribute_id=8229,
                                   text=product_information)

    def get_volume(self, volume_text) -> list:
        match = re.match(r'\d*\s?(мл|л)', volume_text)
        value = 100
        if match is not None:
            value = match.group(0)
        values = [{"value": self.get_integer_values(value)}]
        return values

    @staticmethod
    def get_package_size(product_type, units) -> list:

        package_size = [{"value": ''}]

        default_values = {
            'depth-large': 500,
            'height-large': 400,
            'width-large': 200,

            'depth-default': 300,
            'height-default': 200,
            'width-default': 100
        }

        unit_coefficients = {
            'cm': 0.1,
            'mm': 1,
            'm': 0.001
        }
        unit = unit_coefficients.get(units)

        if product_type.lower() == 'секс-игрушки':
            """
                    РАЗМЕР БОЛЬШИХ УПАКОВОК
            """
            package_size[0][
                'value'] = f'{default_values["depth-large"] * unit}x{default_values["height-large"] * unit}x{default_values["width-large"] * unit}'
        else:
            package_size[0][
                'value'] = f'{default_values["depth-default"] * unit}x{default_values["height-default"] * unit}x{default_values["width-default"] * unit}'

        return package_size

    def get_annotation(self) -> list:
        return [{"value": self.get_cleaned_html(f'{self.data.iloc[2]}. {self.annotation}. {self.data.iloc[4]}').replace(
            '"', '')}]

    def get_weight_converted(self, weight_text, units_from, units_to, result_type):
        """
            Граммы - дефолт
        """
        unit_coefficients = {
            'g': 1,
            'kg': 1000
        }

        unit = unit_coefficients.get(units_from) / unit_coefficients.get(units_to)
        if result_type.__name__ == "float":
            return float(self.get_decimal_values(weight_text)) * unit
        elif result_type.__name__ == "int":
            return int(float(self.get_decimal_values(weight_text)) * unit)

    def get_weight(self, weight_text, units, result_type):
        mapping = {
            'г': 'g',
            'кг': 'kg'
        }
        weight_pattern = r'\d*([.,])?\d*\s?(кг|г)'
        match = re.match(weight_pattern, weight_text.lower())
        value = "500"
        default_units = 'г'
        if match is not None:
            value = match.group(0)
            default_units = match.group(2)
        return [
            {"value": str(self.get_weight_converted(self.get_decimal_values(value),
                                                    units_from=mapping.get(default_units,
                                                                           'g'),
                                                    units_to=units,
                                                    result_type=result_type
                                                    ))}]

    @staticmethod
    def get_age_restrictions() -> list:
        return [{"value": "18+", "dictionary_id": 42701}]

    def get_product_purpose(self, text) -> list:
        return self.get_best_match(category_id=self.category_id,
                                   attribute_id=4543,
                                   text=text,
                                   best_of=5
                                   )

    def get_country(self, country_data):
        countries = re.split(r'-', country_data)

        result = []

        for country in countries:
            recognized = self.get_best_match(category_id=self.category_id,
                                             attribute_id=4389,
                                             text=country,
                                             limit=1000)
            if recognized not in result:
                result.append(recognized[0])
        return result

    @staticmethod
    def get_warranty(period, _type) -> list:
        default_values = {
            'd': 365,
            'm': 12,
            'y': 1
        }
        if _type.__name__ == 'int':
            return [{"value": default_values.get(period)}]
        else:
            return [{"value": str(default_values.get(period))}]

    def get_commercial_type(self, product_information):
        return self.get_best_match(category_id=self.category_id,
                                   attribute_id=9461,
                                   text=product_information,
                                   best_of=1,
                                   limit=5000)

    def get_rich(self, img_data, product_name, product_annotation) -> list:
        image_url_pc = self.get_images(img_data, img_size=1200)[0]
        image_url_mobile = self.get_images(img_data, img_size=600)[0]

        rich = Rich(
            img_url_pc=image_url_pc,
            img_url_mobile=image_url_mobile,
            name=product_name,
            breathe=product_annotation
        )
        return [{"value": rich.create_rich()}]

    def get_search_keywords(self, product_information, product_features) -> list:
        search_keyword_result = [{"value": ""}]
        matching_types = self.get_best_match(category_id=self.category_id,
                                             attribute_id=9461,
                                             text=product_information,
                                             best_of=5,
                                             limit=500)
        for i in range(len(matching_types) - 1):
            search_keyword_result[0]['value'] += matching_types[i]['value'] + ";"
        search_keyword_result[0]['value'] += matching_types[len(matching_types) - 1]['value']

        if not pd.isna(product_features):
            search_keyword_result[0]['value'] += ";" + product_features
        return search_keyword_result

    def get_material(self, material_data) -> list:
        result = []

        materials = re.split(r',', material_data)
        for material in materials:
            matching = self.get_best_match(category_id=self.category_id,
                                           attribute_id=4541,
                                           best_of=1,
                                           limit=200,
                                           text=material
                                           )[0]['value']
            result.append({"value": matching})

    def get_size_params(self, param, default_value, units):
        units_coefficients = {
            'cm': 1,
            'mm': 10
        }
        if param in ['width', 'diameter']:
            match = self.sizes.get('width', default_value) if self.sizes.get('width',
                                                                             default_value) is not None else self.sizes.get(
                'diameter', default_value)
        else:
            match = self.sizes.get(param, default_value)

        value = 30
        if match != default_value:
            for k, v in match.items():
                for values in list(v.values()):
                    if value != values:
                        value = values
            return [{"value": str(value * units_coefficients.get(units))}]
        else:
            return None

    def get_stimulation_type(self, product_annotation) -> list:
        result = [{"value": ""}]
        matching = self.get_best_match(category_id=self.category_id,
                                       attribute_id=4574,
                                       best_of=5,
                                       limit=100,
                                       text=product_annotation
                                       )
        result[0]['value'] = matching[0]['value']
        for match in matching:
            if match['value'] not in result[0]['value']:
                result[0]['value'] += '; ' + match['value']
        return result

    @staticmethod
    def has_vibration(product_information):
        if re.search(r'(с вибрацией)|(вибро)', product_information.lower()):
            return [{'value': "С вибрацией", "dictionary_id": 74819}]
        else:
            return [{'value': "Без вибрации", "dictionary_id": 74818}]

    @staticmethod
    def get_package_information(package_information):
        return [{'value': package_information}]

    def get_sex_toy_size(self):

        for_mapping_mins = [7, 12, 20, 25, 100]

        mapping = {
            for_mapping_mins[0]: [{'value': "Mini: 5-7 см", 'dictionary_id': 970962250}],
            for_mapping_mins[1]: [{'value': "Small: 8-12 см", 'dictionary_id': 970962251}],
            for_mapping_mins[2]: [{'value': "Medium: 13-20 см", 'dictionary_id': 970962252}],
            for_mapping_mins[3]: [{'value': "Large: 21-25 см", 'dictionary_id': 970962253}],
            for_mapping_mins[4]: [{'value': "Extra large: от 26 см", 'dictionary_id': 970962254}],
        }

        ind = 0

        for param, values in self.sizes.items():
            for param_value, l in values:
                for k, v in param_value.items():
                    for min_max, value in v.items():
                        if value > for_mapping_mins[ind] and ind < 5:
                            ind += 1

        return mapping.get(for_mapping_mins[ind])

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
            # бренд
            85: [{"value": self.data.iloc[4]}],

            # Тип """ ПОДУМАТЬ НАД ВОЗМОЖНОСТЬЮ ОШИБКИ: ЕСЛИ ТУТ ТИП ОПРЕДЕЛИЛСЯ ОДИН, ТО НАПРИМЕР КОММЕРЧЕСКИЙ ТИП
            # МОЖЕТ ОПРЕДЕЛИТЬСЯ НЕ ТАКИМ ЖЕ, ЧТО В ТЕОРИИ, В СЛУЧАЕ ОТЛОВА ТАКИХ ОШИБОК ОЗОНОМ МОЖЕТ ПРИВЕСТИ К
            # ОШИБКЕ ПРИ ЗАГРУЗКЕ """

            8229: self.get_product_type(
                product_information=self.data.iloc[2] if not pd.isna(self.data.iloc[2]) else self.data.iloc[3]),

            # 'Название модели (для объединения в одну карточку)'
            9048: [{"value": self.data.iloc[1]} if not pd.isna(self.data.iloc[1]) else {
                "value": f"model-{self.data.iloc[0]}"}],

            # макс температура
            10350: [{"value": "40"}],

            # мин температура
            10351: [{"value": "10"}],

            # 'Вид кондитерского изделия 18+'
            22773: self.get_best_match(category_id=category_id,
                                       attribute_id=22773,
                                       text=self.data.iloc[2] + self.data.iloc[3]),

            # 'Бренд в одежде и обуви'
            31: [{"value": self.data.iloc[4]}],

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

            # """ 'Признак 18+'
            # 'ВАЖНО!!! Признак для товаров, которые содержат эротику, сцены секса,
            #  изображения с нецензурными выражениями, даже если они написаны частично или со спец. символами,
            #   а также для товаров категории 18+ (только для взрослых).'
            # """
            9070: [{"value": True}],

            # 'Пол'
            9163: self.get_sex(self.data.iloc[8]) if not pd.isna(self.data.iloc[8]) else self.get_sex("default"),

            # 'Объединить на одной карточке'
            8292: [{"value": self.get_model(self.data.iloc[1])}],

            10096: self.get_color(category_id=category_id),  # 'Цвет товара'
            # """ 'Укажите базовый или доминирующий цвет вашего товара, выбрав значение из списка. Если точного
            # соответствия вы не находите, используйте ближайшие похожие цвета. \n\nСложные цвета нужно описывать
            # перечислением простых цветов. Например, если вы описываете шмеля, и у него, очевидно, преобладают
            # чёрный, жёлтый и белый цвета, то укажите их все простым перечислением. \n\nПомните, что атрибут Цвет
            # товара - это базовый цвет, все любые другие цвета вы можете прописать в атрибуте Название цвета.\n', """

            # 'Состав'
            8050: [{"value": f"{self.data.iloc[2]}; {self.data.iloc[7]}"}],

            # 'Объем, мл'
            8163: self.get_volume(self.data.iloc[2] + self.data.iloc[10]),

            8205: [{"value": "65"}],
            9782: [{"dictionary_id": 970661099, "value": "Не опасен"}],
            4180: [{
                "value": f"{self.get_best_match(category_id=category_id, attribute_id=8229, text=self.data.iloc[2] if not pd.isna(self.data.iloc[2]) else self.data.iloc[3])[0]['value']},"  # тип
                         f"{self.data.iloc[4]},"  # бренд
                         f"{self.get_model(self.data.iloc[1])}"}],  # Модель
            # 'Название'
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
            #     Кеды Dr. Martens Кино классика, бело-черные, размер 43
            #     Стиральный порошок Ariel Магия белого с мерной ложкой, 15 кг
            #     Соус Heinz tree Tabasco супер острый, 10 мл
            #     Игрушка для животных Четыре лапы "Бегающая мышка" БММ, белый
            # """

            4082: self.get_package_size(self.data.iloc[10], units='cm'),
            # 'Размер упаковки (Длина х Ширина х Высота), см'
            4191: self.get_annotation(),

            # 4164: self.get_warranty('m', str.__name__),  # 'Гарантия на товар, мес.'

            4382: self.get_package_size(self.data.iloc[10], units='mm'),  # 'Размеры, мм',
            4383: self.get_weight(weight_text=self.data.iloc[2] + self.data.iloc[10],
                                  units='g',
                                  result_type=int),  # 'Вес товара, г',
            4389: self.get_country(country_data=self.data.iloc[5]),  # 'Страна-изготовитель'
            4497: self.get_weight(weight_text=self.data.iloc[2] + self.data.iloc[10],
                                  units='g',
                                  result_type=float
                                  ),  #: 'Вес с упаковкой, г'
            4535: self.get_age_restrictions(),  # Возрастные ограничения'
            4543: self.get_product_purpose(
                text=self.get_annotation()[0]["value"] + self.data.iloc[2] + self.data.iloc[3]),
            # 'Назначение товара 18+'
            4593: self.get_weight(weight_text=self.data.iloc[2] + self.data.iloc[10],
                                  units='g',
                                  result_type=int),  # 'Вес, г'
            7578: self.get_warranty('d', _type=str),  # 'Срок годности в днях'
            8962: [{"value": "1"}],  # Единиц в одном товаре
            9024: [{"value": self.data.iloc[1]}],  # 'Артикул' """ : 'Цифро-буквенный код товара для его учета,
            # является уникальным среди товаров бренда. Не является EAN/серийным номером/штрих-кодом,
            # не равен названию модели товара - для этих параметров есть отдельные атрибуты. Артикул выводится в
            # карточке товара на сайте и может использоваться при автоматическом формировании названия товара.', """
            9461: self.get_commercial_type(self.data.iloc[2] + self.data.iloc[3]),  # 'Коммерческий тип'
            10097: [{"value": self.data.iloc[9]}],  # 'Название цвета',
            # 11254: self.get_rich(img_data=self.data.iloc[13],
            #                      product_name=self.data.iloc[2],
            #                      product_annotation=self.get_annotation()[0]["value"]),  # 'Rich-контент JSON',
            11650: [{"value": "1"}],  # 'Количество заводских упаковок'
            22336: self.get_search_keywords(product_information=self.data.iloc[2] + self.data.iloc[3],
                                            product_features=self.data.iloc[7]
                                            ),  # Ключевые слова
            4541: self.get_material(self.data.iloc[15] if not pd.isna(self.data.iloc[15]) else 'ПВХ'),  # 'Материал'
            4566: self.get_size_params(param='length',
                                       units='cm',
                                       default_value=30),  # 'Длина, см'
            4568: self.get_size_params(param='width',
                                       units='mm',
                                       default_value=20
                                       ),  # 'Ширина/диаметр, мм'

            4574: self.get_stimulation_type(self.data.iloc[3] + self.get_annotation()[0]['value']),  # 'Вид стимулятора'
            4578: self.has_vibration(self.data.iloc[2] + self.data.iloc[3] + self.get_annotation()[0]['value']),
            # 'Вибрация'
            4589: self.get_package_information(self.data.iloc[11]) if not pd.isna(self.data.iloc[11]) else self.get_product_type(
                    product_information=self.data.iloc[2] if not pd.isna(self.data.iloc[2]) else self.data.iloc[3]),
            # 'Состав комплекта'
            # 12817: self.get_sex_toy_size(),  # 'Размер секс-игрушек'

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
        match = self.get_mapping_result(attribute_id=attribute['id'])
        if match is not None:
            return match
        return None

    def check_sizes(self):
        size_ids = [4568, 4566, 4568]
        for i in range(len(size_ids)):
            if self.attribute_mapping_required.get(size_ids[i], None) is None:
                if i + 1 <= len(size_ids) and self.attribute_mapping_required.get(size_ids[i + 1], None) is not None:
                    self.add_to_json(is_attribute=True,
                                     changing=True,
                                     attribute_id=size_ids[i],
                                     new_value=self.attribute_mapping_required.get(size_ids[i + 1]),
                                     param=None
                                     )

    def get_mapping_result(self, attribute_id):
        return self.attribute_mapping_required.get(attribute_id, None)

    def fill_attributes(self):

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

        for attribute in self.category_attributes:
            res = self.fill_values(attribute)
            if res is not None:
                self.add_to_json(is_attribute=True,
                                 changing=False,
                                 new_value={
                                     "complex_id": 0,
                                     "id": attribute['id'],
                                     "values": res
                                 },
                                 param=None)

    @staticmethod
    def get_barcode(barcode_data) -> str:
        divided_barcodes = re.split(r'#', barcode_data)
        if len(divided_barcodes) > 1:
            return divided_barcodes[1]
        else:
            return divided_barcodes[0]

    def get_images(self, image_data, img_size=1200) -> list:
        images = re.split(r'\s', image_data)
        for i in range(len(images)):
            images[
                i] = f'http://sexoptovik.ru/_project/user_images/prods_res/{self.data.iloc[0]}/{self.data.iloc[0]}_{images[i]}_{img_size}.jpg'
        return images

    @staticmethod
    def get_cleaned_html(text) -> str:
        return html.unescape(re.sub(re.compile('<.*?>'), '', text))

    def get_naming(self, name_text) -> str:
        return self.get_cleaned_html(name_text).replace('"', '')

    def get_offer_id(self) -> str:
        return f'id-{self.data.iloc[0]}-{self.config.id}'

    @staticmethod
    def get_price(_type):
        mapping = {
            'old-price': "99999",
            "premium-price": "99999",
            "default-price": "99999"
        }
        return mapping.get(_type)

    def fill_total_attributes(self):
        mapping = {
            'barcode': str(self.get_barcode(self.data.iloc[14])),
            'images': self.get_images(self.data.iloc[13]),
            'name': self.get_naming(self.data.iloc[2]),
            'offer_id': self.get_offer_id(),
            'old_price': self.get_price('old-price'),
            #'premium_price': self.get_price('premium-price'),
            'price': self.get_price('default-price')
        }

        for attribute, value in mapping.items():
            self.add_to_json(param=attribute,
                             new_value=value,
                             is_attribute=False
                             )
