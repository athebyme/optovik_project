import os
from dataclasses import dataclass


@dataclass()
class rePattern:
    ExtractParams: list[str]

    def loadConfigs(self):
        current_dir = os.path.dirname(__file__)
        filename = os.path.join(current_dir, '../dataText/rePatternExtract.txt')
        self.ExtractParams = self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as file:
            return [line.strip() for line in file.readlines()]
    def __init__(self):
        self.loadConfigs()