import re

class Sizes:
    def __init__(self):
        self.sizes = {}

    def initWeight(self, text):
        weight_pattern = re.compile(r'вес.*?[\s\.:]+([\d\.,]+)\s*(?:г|кг|lbs)', flags=re.IGNORECASE)
        weight2_pattern = re.compile(r"\d+\s*г\s*\*\s*\d+\s*шт", flags=re.IGNORECASE)
        weight_unit_pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*(г|кг)\b")

        matches = weight_pattern.findall(text) + weight2_pattern.findall(text) + weight_unit_pattern.findall(text)

        for match in matches:
            if isinstance(match, tuple):
                value, unit = match
                value = value.replace('.', ',')
                if unit == 'кг':
                    value *= 1000
                elif unit == 'lbs':
                    value *= 453.592
                self.sizes['вес'] = float(value)
            else:
                self.sizes['вес'] = float(match.replace(',', '.'))

        print(self.sizes['вес'])
