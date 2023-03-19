import datetime
import os
import sys
import time
import Levenshtein

import pandas as pd

import main
import google.auth
import httplib2

from config.Config import Config


class SexOptovik_ozon(main.Functions):
    sellerCode = Config.sellerId
    service = Config.service
    shop = Config.shopName

    def __init__(self, abs_path, sellerCode, provider):
        super().__init__(abs_path=abs_path, sellerCode=sellerCode, provider=provider)
        self.start()

    def printer(self, text):
        return print(text)

    def parseExcelOzon(self, path=""):
        xlsx_file = pd.read_excel(open(path, 'rb'), sheet_name='Шаблон для поставщика')
        params = {}
        for row in xlsx_file.itertuples():
            index = 0
            for cell in row:
                index += 1
                try:
                    cell += ""
                except TypeError:
                    continue
                params[index] = {'name': cell, 'required': True if '*' in cell else False}
            return params

    def start(self):
        from config.presets.FillPreset import FillPreset
        from config.Config import Config
        from config.presets.AnyData import AnyData
        A = AnyData()
        print(self.getCloset(word='духи', s=A.tnvd))

        preset = FillPreset()
        # preset_instance = preset.create(content='',
        #                                 pack_height=30,
        #                                 main_photo='',
        #                                 max_temp=0,
        #                                 pack_count=1,
        #                                 pack_width=15,
        #                                 pack_length=10,
        #                                 NDS=0,
        #                                 effect='Без эффекта',
        #                                 alternative_name='',
        #                                 model_name='',
        #                                 brand=Config.shopName,
        #                                 danger_class='Не опасен',
        #                                 cost=99999,
        #                                 min_temp=0,
        #                                 pack_weight=300,
        #                                 commercial_type='',
        #                                 article_number='',
        #                                 volume=0,
        #                                 expire_date=365,
        #                                 type=''
        #                                 )
        #print(preset_instance)
        #self.getStockList()
        #self.downloadGoogleFolder(folderId='1COxI8zZlgQgLN_XLmOvARZ6Oc1KDQTC-')
        pathCategories = self.getCategoryFilesPaths()

        reqParams = set()
        for i in pathCategories:
            par = self.allFilesFunction(path=fr"./pool/SexOptovik/Ozon/{i}")
            for k, v in par.items():
                reqParams.add(v['name'])
        print(reqParams)

    def getStockList(self, columnsExcel=None):

        if columnsExcel is None:
            columnsExcel = {}

        main.Functions.google_driver(google_ids=[Config.urlExistItems],
                                     file_names=[f"{Config.shopName}_OZ.csv"],
                                     path_os_type='./pool/SexOptovik/google_downloaded',
                                     service=Config.service)
        print('Считаю новые товары...')
        PATH_GOOGLE_XLSX = f'./pool/SexOptovik/google_downloaded/{Config.shopName}_OZ.csv'
        checkBrand = "Lasciva Piter Anal Wisteria Somnium Face"

        goods, errors, lieBrands = main.Functions.getDataCsv(self,
                                                             path=fr"C:\csv_parser_wb\pool\SexOptovik\google_downloaded\{Config.shopName}_OZ.csv",
                                                             sellerCode='1168',
                                                             checkBrand='',
                                                             marketplace='oz')

        df = pd.DataFrame({'OK': len(goods), 'ERRORS': len(errors), 'LIE': len(lieBrands)}, index=['>>'])
        self.printer(df)
        self.printer(f"\n\n{pd.DataFrame({'errors': list(errors)})}")
        opisanie = main.Functions.uploadFromFile(self, file_path='./SexOptovik/all_prod_d33_.csv', isSet=False)

    def getCategoryFilesPaths(self):
        paths = [f for f in os.listdir("./pool/SexOptovik/Ozon") if f.endswith(".xlsx")]
        if len(paths) == 0:
            print(
                '[!] Проверьте файлы в папке шаблонов Ozon. Данных не найдено !\nВы можете попробовать заново загрузить файлы')
            sys.exit(1)
        return paths

    def test(self, path: str):
        data = str(datetime.datetime.now())
        data = data[:data.find(" ")]
        if data in path:
            path = path.replace("~${0} ".format(data), "")
        a = self.parseExcelOzon(path="./pool/SexOptovik/Ozon/{0}".format(path))
        return a

    def allFilesFunction(self, path):
        success = False
        params = None
        while not success:
            try:
                params = self.parseExcelOzon(path=path)
                print(params)
                success = True
            except PermissionError:
                input("[!] Закройте файл {0} и нажмите Enter".format(path[path.find(" ") + 1:]))
            except Exception as ex:
                print("[!] Произошла непредвиденная ошибка.\nПодробнее: {0} при обработке {1} файла".format(ex,
                                                                                                            path))
                sys.exit(1)
        return params

    def downloadGoogleFolder(self, folderId):

        if not os.path.exists(r'./pool/SexOptovik/Ozon'):
            os.mkdir('./pool/SexOptovik/Ozon')

        _COUNT_TRIES_BEFORE_EXIT = 2
        success = False
        _try = 1
        while not success:
            try:
                page_token = None
                response = self.service.files().list(q=f"'{folderId}' in parents",
                                                     spaces='drive',
                                                     fields='nextPageToken, files(id, name)',
                                                     pageToken=page_token).execute()

                # query = f"parents = '{folderId}'"
                # response = service.files().list(q=query).execute()
                files = response.get('files')
                if not files:
                    print('На диске нет папок.')
                else:
                    df = pd.DataFrame(files)
                    print("Найдено: \n{0}".format(df))
                    time.sleep(1.5)
                    file_names = [x['name'] for x in files]
                    files_ids = [x['id'] for x in files]
                    main.Functions.google_driver(google_ids=files_ids,
                                                 file_names=file_names,
                                                 path_os_type='./pool/SexOptovik/Ozon', service=self.service)
                success = True
            except OSError as ex:
                input(f'Ошибка! {ex}.\nПроверьте соединение и нажмите любую клавишу.')
                if _try > _COUNT_TRIES_BEFORE_EXIT:
                    _try += 1
                else:
                    print(f'Это уже {_try} попытка. \n'
                          f'Попробуйте проверить данные и перезапустить программу)')
                    sys.exit(0)
            except httplib2.error.ServerNotFoundError:
                input('Проверьте соединение и нажмите любую клавишу')
            except google.auth.exceptions.RefreshError:
                print('Токен устарел. Необходимо произвести замену токена.')
                if os.path.isfile('./token_drive_v3.pickle'):
                    os.remove('./token_drive_v3.pickle')
                    print('Устаревший токен успешно удален. Необходимо пройти авторизацию заново.')
                    time.sleep(3)
                else:
                    print('Файл токена не найден в текущем местоположении. Выберите его самостоятельно')
                    path_token = main.Functions.getFolderFile(0, item=' файл токена google')
                    os.remove(path_token)
            time.sleep(1.5)
        return

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

    def matchType(self, name, s=None):
        if not isinstance(name, str) or not isinstance(s, set) or not s:
            return None
        # Инициализируем переменные для хранения лучшего совпадения и минимального расстояния
        best_match = None
        min_distance = float("inf")
        # Перебираем все значения из set
        for value in s:
            # Вычисляем расстояние Левенштейна между name и value с помощью модуля python-Levenshtein
            distance = Levenshtein.distance(name, value)
            # Если расстояние меньше минимального, обновляем лучшее совпадение и минимальное расстояние
            if distance < min_distance:
                best_match = value
                min_distance = distance
        # Возвращаем лучшее совпадение
        return best_match

    @measure_time
    def getCloset(self, word, s=None):
        if not isinstance(word, str) or not isinstance(s, set) or not s:
            return None
        # Фильтруем слова из s с расстоянием Левенштейна <= 4
        result = set(filter(lambda item: word.lower() in item.lower(), s))
        print(result)
        # Возвращаем лучшее совпадение из result
        return self.matchType(name=word, s=result)
