from dataclasses import dataclass

@dataclass

class MainData():
    provider: str
    seller_code: str
    excelFiles_path: str
    imgsFiles_path: str
    barcodeFile_path: str
class Data:
    def __init__(self,parentF_path):
        self.parentF_path = parentF_path
    def a(self):
        return f'путь - {self.parentF_path}'

if __name__ == "__main__":
    data = MainData("E:/123/forcedchunks.dat")
    print(data.a())
