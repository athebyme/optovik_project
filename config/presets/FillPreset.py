from config.presets.ProductPreset import Product


class FillPreset(Product):
    PresetClass = Product

    def create(self, **kwargs):
        product_instance = self.PresetClass(**kwargs)
        # Дополнительные действия с product_instance, если нужно
        return product_instance
