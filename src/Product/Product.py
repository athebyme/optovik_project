class Product:
    def __init__(self, **kwargs):
        self.attributes = {}    # Создаем новый словарь для каждого экземпляра
        for key, value in kwargs.items():
            self.attributes[key] = value
        self.checkValues()
        #setattr(self.attributes, key, value)

    def clone(self, **attributes):
        attrs = {**self.__dict__, **attributes}
        return Product(**attrs)


    def checkValues(self):
        def checkImages(images):
            if isinstance(images, list):
                for i in range(len(images)):
                    if isinstance(images[i], dict):
                        images[i] = images[i]['file_name']

        def checkAttributes(attributes):
            for i in range(len(attributes)):
                newValue = attributes[i]['attribute_id']
                del attributes[i]['attribute_id']
                attributes[i]['id'] = newValue

                if attributes[i]['id'] == 4383 and len(attributes[i]['values'])>0 and isinstance(attributes[i]['values'][0]['value'], str) and \
                        self.attributes['category_id'] == 17031663:
                    attributes[i]['values'][0]['value'] = str(attributes[i]['values'][0]['value'])

        for k,v in self.ozon_to_default.items():
            if self.attributes.get(k) is None:
                self.attributes[k] = v
        del self.attributes['last_id']
        #del self.attributes['id']

        checkImages(self.attributes['images'])
        checkAttributes(self.attributes['attributes'])




    def clear(self):
        t = ['attributes',
             'barcode',
             'category_id',
             'color_image',
             'complex_attributes',
             'currency_code',
             'depth',
             'dimension_unit',
             'geo_names',
             'height',
             'images',
             'primary_image',
             'service_type',
             'images360',
             'name',
             'offer_id',
             'old_price',
             'pdf_list',
             'premium_price',
             'price',
             'vat',
             'weight',
             'weight_unit',
             'width']



    def changeBarcode(self, newBarcode):
        self.attributes['barcode'] = newBarcode

    def changeParam(self, param, newValue):
        self.attributes[param] = newValue

    @staticmethod
    def create_product(attribute_dict):
        return Product(**attribute_dict)