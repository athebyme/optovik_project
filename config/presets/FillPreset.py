from config.presets.ProductPreset import Product


class FillPreset:
    PresetClass = None

    def __init__(self):
        self.PresetClass = Product

    def create(self, **kwargs):
        return self.PresetClass(**kwargs)

