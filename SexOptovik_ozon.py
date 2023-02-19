import datetime
import os
import sys
import time

import pandas as pd

import main
import google.auth
import httplib2
from Google import Create_Service


class SexOptovik_ozon(main.Functions):
    sellerCode = ''
    service = None
    shop = ''
    def createGoogleDriveAPI(self):
        CLIENT_SECRET_FILE = '.\client_secrets.json'
        API_NAME = 'drive'
        API_VERSION = 'v3'
        SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    def __init__(self, sellerCode, abs_path, provider):
        super().__init__(abs_path, sellerCode, provider)
        self.sellerCode = sellerCode
        self.createGoogleDriveAPI()
        #self.downloadGoogleFolder()
        self.startParsing()

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

    def startParsing(self, columnsExcel=None):

        if columnsExcel is None:
            columnsExcel = {}
        exists_goods = {'1168A': {'shop': 'Amare', 'id': '1LOrCyNl9n6WxeL-yumr0E7PCdXN3pT6G'},
                        '1366B': {'shop': 'BANANZZA', 'id': '15OXYq0aRQVJPlH7eQ2eSs0y_R8jOSM7r'},
                        '1269L': {'shop': 'Lasciva', 'id': '1UBFQquHyn6v5zmzce6CjAqpmTWuwkqNJ'},
                        '1168S': {'shop': 'SomniumFace', 'id': '1DtVPArbA1LKircZBrVR2ky8xSOxeEBSs'},
                        '1292W': {'shop': 'Wisteria', 'id': '1QeL6_RNYXYzUGFP4lzhX2dQpRJH2g1Ae'}
                        }
        success = False
        if self.sellerCode == '1168':
            while not success:
                try:
                    choosen = int(input('\nКакой из магазинов вы желаете выбрать ?:\n0: Amare\n1:Somnium Face\n:'))
                    if choosen < 2 and choosen >= 0:
                        success = True
                    else:
                        print('\n[!] Выберите число 0 или 1')
                except ValueError:
                    print('\n[!] Вы ввели не число !')
                except Exception as ex:
                    print('\n[!]Произошла непредвиденная ошибка')
                    sys.exit(1)
            main.Functions.google_driver(google_ids=[exists_goods[self.sellerCode + 'A']['id']],
                                         file_names=[exists_goods[self.sellerCode + 'A']['shop'] + '_OZ.csv'],
                                         path_os_type='./pool/SexOptovik/google_downloaded',
                                         service=self.service) if choosen == 0 else \
                main.Functions.google_driver(google_ids=[exists_goods[self.sellerCode + 'S']['id']],
                                             file_names=[exists_goods[self.sellerCode + 'S']['shop'] + "_OZ.csv"],
                                             path_os_type='./pool/SexOptovik/google_downloaded',
                                             service=self.service)

            if choosen == 0: self.shop = exists_goods[self.sellerCode+'A']['shop']
            else:    self.shop = exists_goods[self.sellerCode+'S']['shop']
        else:
            main.Functions.google_driver(google_ids=[exists_goods[self.sellerCode]['id']],
                                         file_names=[exists_goods[self.sellerCode]['shop'] + '_OZ.csv'],
                                         path_os_type='./pool/SexOptovik/google_downloaded',
                                         service=self.service)
            self.shop = exists_goods[self.sellerCode]['shop']
        print('Считаю новые товары...')
        PATH_GOOGLE_XLSX = f'./pool/SexOptovik/google_downloaded/{exists_goods[self.sellerCode+self.shop[:1]]["shop"]}_OZ.csv'
        checkBrand = "Lasciva Piter Anal Wisteria Somnium Face"

        goods, errors, lieBrands = main.Functions.getDataCsv(self,
                                  path=f"C:\csv_parser_wb\pool\SexOptovik\google_downloaded\{self.shop}_OZ.csv",
                                  sellerCode='1168',
                                  checkBrand='',
                                  marketplace='oz')
        df = pd.DataFrame({'OK': goods, 'ERRORS': errors, 'LIE': lieBrands})
        print(df)
        opisanie = main.Functions.uploadFromFile(self, file_path='./SexOptovik/all_prod_d33_.csv', isSet=False)
        

    def initColumns(self):
        paths = [f for f in os.listdir("./pool/SexOptovik/Ozon") if f.endswith(".xlsx")]
        if len(paths) == 0:
            print(
                '[!] Проверьте файлы в папке шаблонов Ozon. Данных не найдено !\nВы можете попробовать заново загрузить файлы')
            sys.exit(1)
        else:
            data = str(datetime.datetime.now())
            data = data[:data.find(" ")]
            for i in range(len(paths)):
                success = False
                while not success:
                    try:
                        if data in paths[i]:
                            paths[i] = paths[i].replace("~${0} ".format(data), "")
                        a = self.parseExcelOzon(path="./pool/SexOptovik/Ozon/{0}".format(paths[i]))
                        print('{0} / name: {1}                  / cols: {2} >> {3}'.format(i + 1, paths[i][
                                                                                                  paths[i].find(
                                                                                                      " ") + 1:],
                                                                                           len(a), a))
                        success = True
                    except PermissionError:
                        input("[!] Закройте файл {0} и нажмите Enter".format(paths[i][paths[i].find(" ") + 1:]))
                    except Exception as ex:
                        print("[!] Произошла непредвиденная ошибка.\nПодробнее: {0} при обработке {1} файла".format(ex,
                                                                                                                    paths[
                                                                                                                        i]))
                        sys.exit(1)

    def downloadGoogleFolder(self, folderId='1COxI8zZlgQgLN_XLmOvARZ6Oc1KDQTC-'):

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
