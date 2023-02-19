import pathlib
from itertools import product
from pathlib import Path

import google.auth.exceptions
import main
import os
import re
import shutil
import sys
import time

class SexOptovik():
    cwd = os.getcwd()
    optovik_items = {}
    current_cats_wb = set()
    seller_code = ''
    size_img = 650
    CONST_AMOUNT_OF_XLSX_ITEMS = 10

    parsed_items =           {1: ['Номер карточки'], 2: ['Предмет'], 3: ['Цвет'],
                              4: ['Бренд'], 5: ['Пол'], 6: ['Название'],
                              7: ['Артикул товара'], 8: ['Размер'], 9: ['Рос. размер'],
                              10: ['Баркод товара'],
                              11: ['Цена'], 12: ['Состав'], 13: ['Медиафайлы'],
                              14: ['Описание'],
                              15: ['Страна производства'],
                              16: ['Особенности секс игрушки'],
                              17: ['Особенности модели'], 18: ['Материал изделия'],
                              19: ['Наличие батареек в комплекте'], 20: ['Объем'],
                              21: ['Объем (мл)'],
                              22: ['Объем средства'], 23: ['Ширина предмета'],
                              24: ['Ширина упаковки'], 25: ['Длина (см)'], 26: ["Длина упаковки"],
                              27: ['Длина секс игрушки'],
                              28: ['Рабочая длина секс игрушки'],
                              29: ['Высота предмета'], 30: ['Высота упаковки'],
                              31: ['Глубина предмета'],
                              32: ['Диаметр'],
                              33: ['Диаметр секс игрушки'], 34: ['Вид вибратора'],
                              35: ['Вес без упаковки'], 36: ['Вес(г)'],
                              37: ['Вес средства'], 38: ['Вес товара без упаковки(г)'],
                              39: ['Вес товара с упаковкой(г)'],
                              40: ['Комплектация'],
                              41: ['Количество предметов в упаковке'], 42: ['Упаковка']
                              }

    parsed_items_100_items = {1: ['Номер карточки'], 2: ['Предмет'], 3: ['Цвет'],
                              4: ['Бренд'], 5: ['Пол'], 6: ['Название'],
                              7: ['Артикул товара'], 8: ['Размер'], 9: ['Рос. размер'],
                              10: ['Баркод товара'],
                              11: ['Цена'], 12: ['Состав'], 13: ['Медиафайлы'],
                              14: ['Описание'],
                              15: ['Страна производства'],
                              16: ['Особенности секс игрушки'],
                              17: ['Особенности модели'], 18: ['Материал изделия'],
                              19: ['Наличие батареек в комплекте'], 20: ['Объем'],
                              21: ['Объем (мл)'],
                              22: ['Объем средства'], 23: ['Ширина предмета'],
                              24: ['Ширина упаковки'], 25: ['Длина (см)'], 26: ["Длина упаковки"],
                              27: ['Длина секс игрушки'],
                              28: ['Рабочая длина секс игрушки'],
                              29: ['Высота предмета'], 30: ['Высота упаковки'],
                              31: ['Глубина предмета'],
                              32: ['Диаметр'],
                              33: ['Диаметр секс игрушки'], 34: ['Вид вибратора'],
                              35: ['Вес без упаковки'], 36: ['Вес(г)'],
                              37: ['Вес средства'], 38: ['Вес товара без упаковки(г)'],
                              39: ['Вес товара с упаковкой(г)'],
                              40: ['Комплектация'],
                              41: ['Количество предметов в упаковке'], 42: ['Упаковка']
                              }

    @staticmethod
    def parse_sizes(text, type):
        eds = ['длина', 'ширина', 'высота', 'диаметр', 'глубина']
        eds_en = ['length', 'width', 'height', 'diameter', 'depth']
        if ', ' not in text or type == 'clothe':
            t = text
            data = []
            eds = ['длина', 'ширина', 'высота', 'диаметр', 'глубина', 'вес']
            indx = []
            indx_first = []
            data = []
            for x in eds:
                if t.find(x) != -1: indx.append(t.find(x))
            indx.sort()
            indx_first = indx.copy()
            if len(indx) != 0:
                if indx[0] != 0:
                    t = t[indx[0]:]
                    indx = []
                    for x in eds:
                        if t.find(x) != -1: indx.append(t.find(x))

                if len(indx) > 1:
                    for x in range(1, len(indx)):
                        data.append(t[:indx[x] - 1].strip())
                        t = t[indx[x]:]
                    data.append(t.strip())
                else:
                    if text.strip() not in data:
                        data.append(text.strip())
        else:
            _split_parametr = ', '
            data = list(map(str, text.split(_split_parametr)))
        res = {}
        ed_local_check = [',длина', ',ширина', ',высота', ',диаметр', ',глубина']
        for i in data:
            FLAG = []
            for b in ed_local_check:
                if b in i:
                    FLAG.append(True)
            if len(FLAG) > 1:
                _indx = []
                divided = []
                for j in range(len(ed_local_check)):
                    if i.find(eds[j]) != -1: _indx.append(i.find(eds[j]))
                _indx.sort()
                data.remove(i)
                t = i
                for x in range(1, len(_indx)):
                    data.append(t[:_indx[x] - 1].strip())
                    t = t[_indx[x]:]
                data.append(t.strip())
        for i in range(len(data)):
            last = data[i]
            _chr = last[len(last) - 1:]
            if _chr == ',':
                data[i] = last[:len(last) - 1]
        ed_local_check = [',длина', ',ширина', ',высота', ',диаметр', ',глубина']
        for i in data:
            FLAG = []
            for b in ed_local_check:
                if b in i:
                    FLAG.append(True)
            if len(FLAG) >= 1:
                _indx = []
                divided = []
                for j in range(len(ed_local_check)):
                    if i.find(eds[j]) != -1: _indx.append(i.find(eds[j]))
                _indx.sort()
                data.remove(i)
                t = i
                for x in range(1, len(_indx)):
                    data.append(t[:_indx[x] - 1].strip())
                    t = t[_indx[x]:]
                data.append(t.strip())
        if type == 'all':
            for item in data:
                it = item
                if ' мм' in it:
                    k = 10
                elif ' кг' in it:
                    k = 0.001
                else:
                    k = 1
                # it = it.replace(',', '.')
                # if '-' in it:
                #    it = it[it.find('-')+1:]
                if 'вес' in it and res.setdefault('weight') is None:
                    it = it.replace(',', '.')
                    w = 0
                    if text.lower().count('вес') > 1:
                        for i in data:
                            if 'вес' in i:
                                w += round(float(re.sub("[^0-9,]", "", i).replace(',', '.')) / k, 2)
                    else:
                        w = round(float(re.sub("[^0-9,]", "", it).replace(',', '.')) / k, 2)
                    res['weight'] = w

                for i in range(len(eds)):
                    if eds[i] in it and res.setdefault(eds_en[i]) is None:
                        if ' и ' in it:
                            it = it.replace(' и ', '-')
                        if it.count('(') == it.count(')') and it.count('(') > 0:
                            f_t = it.find('(')
                            if f_t > 8:
                                it = it[:f_t]
                        if 'м до ' in it:
                            it = it.replace('м до ', '-')
                        r = re.sub("[^0-9,-/]", "", it).replace(',', '.').replace('/', '-').lstrip().rstrip()
                        if r == '':
                            res[eds_en[i]] = 'универсальный (растягивается)'
                            break
                        #if r[len(r)-1:] == '.':
                        #    r = r[:len(r)-1]
                        if '-' in r:
                            r_lst = list(map(str, r.split('-')))
                            try:
                                r_lst.remove('')
                            except ValueError:
                                pass
                            av = 0
                            if '.' in r_lst: r_lst.remove('.')
                            if '' in r_lst: r_lst.remove('')
                            if ' ' in r_lst: r_lst.remove(' ')
                            for ind in range(len(r_lst)):
                                if r_lst[ind][:1] == '.':
                                    r_lst[ind] = r_lst[ind][1:]

                            # print(r_lst)
                            for j in r_lst:
                                av += float(j)
                            r = round(float(av / len(r_lst)) / k, 2)
                        else:
                            if r == '.':
                                r = 'универсальный (растягивается)'
                            elif r[len(r)-1:] == '.':
                                r = r[:len(r)-1]
                            else:
                                # print([r,data])
                                if r[:1] == '.':
                                    delete = r.count('.') - 1
                                    r = r[delete:]
                                r = round(float(r) / k, 2)
                        res[eds_en[i]] = r
                        # res.setdefault(eds_en[i],r)
                        break
            return res
        if type == 'clothe':
            SIZES = {1: 'XS', 2: 'S', 3: 'M', 4: 'L', 5: 'XL', 6: 'XXL', 7: 'XXXL', 8: '4XL'}
            SIZES_RU = {'XS': '40-42', 'S': '42-44', 'M': '44-46', 'L': '46-48', 'XL': '48-50', '1XL': '52-54',
                        'XXL': '54-56',
                        'XXXL': '56-58', '4XL': '58-60', 'XL': '50-52'}
            eds = ['об. талии', 'об. груди', 'об. бедер']
            indx_obhvats = []
            for i in eds:
                if i in text:
                    indx_obhvats.append(text.index(i))
            if len(data) != 0:
                eds = ['длина', 'ширина', 'высота', 'диаметр', 'глубина']
                eds_en = ['length', 'width', 'height', 'diameter', 'depth']
                for x in data:
                    temp = x
                    if ' мм' in temp:
                        k = 10
                    elif ' кг' in temp:
                        k = 0.001
                    else:
                        k = 1
                    for z in range(len(eds)):
                        if eds[z] in x:
                            t = re.sub("[^0-9,-]", "", x).replace(',', '.')
                            if res.setdefault(eds_en[z]) is None:
                                res[eds_en[z]] = t
                    if 'вес' in temp and res.setdefault('weight') is None:
                        it = temp.replace(',', '.')
                        w = 0
                        if text.lower().count('вес') > 1:
                            for i in data:
                                if 'вес' in i:
                                    w += round(float(re.sub("[^0-9,]", "", i)) / k, 2)
                        else:
                            w = round(float(re.sub("[^0-9,]", "", it)) / k, 2)
                        res['weight'] = w

            for k, v in SIZES_RU.items():
                if v in text:
                    res['size'] = k
                    res['size-ru'] = v
            if len(indx_obhvats) != 0 and len(indx_first) != 0:
                if indx_first[len(indx_first) - 1] > indx_obhvats[len(indx_obhvats) - 1]:
                    text = text[:indx_first[0]]
                else:
                    pass
            check = list(map(str, text.split(', ')))

            for i in check:
                if 'об. ' in i and res.setdefault('size') is None:
                    n = re.sub("[^0-9-]", "", i)
                    l = list(map(int, n.split('-')))
                    sr_arf = round((l[1] + l[0]) / 2)
                    if 'груд' in i:
                        SIZE = main.Functions.for_sizes_parse([99, 103, 107, 111, 115, 119, 123, 127])
                    if 'бедер' in i:
                        SIZE = main.Functions.for_sizes_parse([103, 107, 111, 115, 119, 123, 127, 131])
                    if 'тали' in i:
                        SIZE = main.Functions.for_sizes_parse([86, 90, 94, 98, 102, 107, 112, 117])
                    if sr_arf < SIZE['XS']:
                        res['size'] = 'XS'
                        res['size-ru'] = SIZES_RU['S']
                        return res
                    prev_sz = SIZE['XS']
                    for k, v in SIZE.items():
                        if k == 'XS': pass
                        if sr_arf < v and sr_arf > prev_sz:
                            res['size'] = k
                            res['size-ru'] = SIZES_RU[k]
                            return res
                        prev_sz = v

            t = check[0]
            if t.count('.') > 1:
                res['size'] = 'M'
                res['size-ru'] = SIZES_RU['M']
                return res
            if 'универсальный' in t:
                res['size'] = 'M'
                res['size-ru'] = SIZES_RU['M']
                return res
            if '-' in t and len(t) == 5:
                res['size-ru'] = t
                size = t.split('-')[0]
                for k, v in SIZES_RU.items():
                    if size in v:
                        res['size'] = k
                return res
            for k, v in SIZES.items():
                if (v in t or str(k) in t) and res.setdefault('size') is None:
                    res['size'] = v
                    res['size-ru'] = SIZES_RU[v]
                    return res
            return res
        if type == 'cosmetic':
            ed = ''
            if ' мл' in text:
                ed = 'мл'
            if ' г' in text:
                ed = 'г'
            volume = re.sub("[^0-9 *хx,]", "", text)
            volume = volume.replace('  ', ' *', 1).replace('(', '').replace(')', '')
            res.setdefault('volume', volume.strip())
            res.setdefault('ed', ed.strip())
            return res
        return text

    def download_from_google(self, type, path=os.getcwd()):
            success = False
            while not success:
                url_blacklist_items_wb = [
                    'https://drive.google.com/file/d/1bMMyC75qNwpHD61CfaM7gU2zT-dR012t/view?usp=sharing',
                    'blacklist_brands_wb']
                url_problem_items_wb_id = [
                    'https://drive.google.com/file/d/1dE7VrYH_CDfKFTofDzhjbc8Cp7zZ8ios/view?usp=sharing',
                    'problem_items_wb_id']
                url_wb_cats = ['https://drive.google.com/file/d/1zqL6RS35CqQaeZMMAnKHFugmImbJi4t8/view?usp=sharing',
                               'wb_cats']
                url_wb_xlsx_1277 = ['https://drive.google.com/file/d/1SVeUg1-AWWZyTgg9RGkwitOSIDT4Ixul/view?usp=sharing',
                                    'wb_1277.xlsx']
                url_wb_xlsx_1299 = ['https://docs.google.com/file/d/163cgrAFCKd01CGG1FhhT70ibF8d9F7B3/view?usp=sharing',
                                    'wb_1299.xlsx']
                url_wb_xlsx_1366 = ['https://docs.google.com/file/d/1c8eaqFkxmYOPsshXwvMP9z5HaXliS-hs/view?usp=sharing',
                                    'wb_1366.xlsx']

                download_available = [url_blacklist_items_wb, url_problem_items_wb_id, url_wb_cats, url_wb_xlsx_1277, url_wb_xlsx_1299, url_wb_xlsx_1366]

                google_ids = ['1bMMyC75qNwpHD61CfaM7gU2zT-dR012t', '1dE7VrYH_CDfKFTofDzhjbc8Cp7zZ8ios',
                              '1zqL6RS35CqQaeZMMAnKHFugmImbJi4t8']
                google_names = ['blacklist_brands_wb.txt', 'problem_items_wb_id.txt', 'wb_cats.txt']

                if self.seller_code == '1277':
                    google_ids.append('1SVeUg1-AWWZyTgg9RGkwitOSIDT4Ixul')
                    google_names.append('wb_1277.xlsx')
                elif self.seller_code == '1299':
                    google_ids.append('163cgrAFCKd01CGG1FhhT70ibF8d9F7B3')
                    google_names.append('wb_1299.xlsx')
                elif self.seller_code == '1366':
                    google_ids.append('1c8eaqFkxmYOPsshXwvMP9z5HaXliS-hs')
                    google_names.append('wb_1366.xlsx')

                path2 = Path(path, 'pool', 'SexOptovik', 'google_downloaded')
                try:
                    shutil.rmtree(path2)
                    os.rmdir(path2)
                except OSError:
                    os.mkdir(path2)
                try:
                    if type == 0:
                        main.Functions.google_driver(google_ids, google_names, './pool/SexOptovik/google_downloaded')
                    else:
                        main.Functions.google_driver([google_ids[type]], [google_names[type]],
                                                './pool/SexOptovik/google_downloaded')
                    success = True
                except google.auth.exceptions.RefreshError:
                    print('Токен устарел. Необходимо заново авторизироваться в аккаунт.')
                    if os.path.isfile('./token_drive_v3.pickle'):
                        os.remove('./token_drive_v3.pickle')
                        print('Устаревший токен успешно удален. Необходимо пройти авторищацию заново.')
                        time.sleep(3)
                    else:
                        print('Файл токена не найден в текущем местоположении. Выберите его самостоятельно')
                        path_token = main.Functions.getFolderFile(0, item=' файл токена google')
                        os.remove(path_token)

    @staticmethod
    def init_category(data, cats_wb, extra):
        CONST_COUNT_WORDS = 3
        data_lower = data.lower()
        getting_in_cat_wb = []
        #getting_in_cat_wb = []
        cats_wb = set()
        extra = extra + '. ' + data_lower
        info = list(map(lambda data: data.strip(), data_lower.lower().split('#')))
        info = list(map(lambda info: info.split('>'), info))
        with open('./pool/SexOptovik/google_downloaded/wb_cats.txt') as f:
            for i in f:
                cats_wb.add(i.rstrip().lower())
        cats_wb.remove('')

        for i in info:
            saved = []
            for j in i:
                if 'белье' not in j:
                    for n in j.split():
                        if n in cats_wb:
                            #getting_in_cat_wb.add(n)
                            getting_in_cat_wb.append(n)
                    t = list(map(lambda j: j + ' ', j.split()))
                    for p in saved:
                        t.append(p + ' ')
                    for n in range(CONST_COUNT_WORDS):
                        t.append('')
                    if 'эротик' not in t:
                        t.append('эротик ')
                    all_var = set(map(''.join, product(t, repeat=CONST_COUNT_WORDS)))
                    all_var = list(map(lambda i: i.rstrip().replace(',', ''), all_var))
                    # all_var = list(map(lambda i: i, all_var))
                    for var in all_var:
                        if var in cats_wb:
                            #getting_in_cat_wb.add(var)
                            getting_in_cat_wb.append(var)
                    saved = j.split().copy()
                else:
                    t = data_lower.lower()
                    ed = ['комплекты', 'бдсм', 'топы', 'лифы', 'бюстье', 'стрэпы', 'корсаж', ' маски', 'комбинезон', 'парик']
                    ed_cats = ['комплекты эротик', 'комплекты бдсм', 'топы эротик', 'бюстгальтеры эротик',
                               'бюстгальтеры эротик', 'стрэпы эротик', 'корсеты эротик', 'маски эротик', 'комбинезоны эротик', 'головные уборы эротик']
                    for o in range(len(ed)):
                        if ed[o] in t:
                            #getting_in_cat_wb.add(ed_cats[o])
                            getting_in_cat_wb.append(ed_cats[o])
                    if 'трусики' in t or 'трусы' in t or 'стринги' in t or 'шортики' in t or 'шорты' in t:
                        #getting_in_cat_wb.add('трусы эротик')
                        getting_in_cat_wb.append('трусы эротик')
        if 'вибро' in data_lower:
            ed = ['зажим', 'яйца', 'трус', 'пуля']
            ed_cats = ['зажимы для сосков', 'виброяйца', 'вибротрусики', 'вибропули']
            for o in range(len(ed)):
                if ed[o] in data_lower:
                    #getting_in_cat_wb.add(ed_cats[o])
                    getting_in_cat_wb.append(ed_cats[o])
        ed = ['лубрикант', 'стек ', 'смазки для секс-игрушек', 'наборы и аксессуары', 'клиторальные стимуляторы',
              'костюмы', 'бдсм товары и фетиш > аксессуары', 'ошейник', 'простынь', 'наручник', 'кольцо эрекционное',
              'стимулирующие влагалище',
              'танго', 'стреп', 'стрэп', 'чулки', 'пояс', 'мастурбатор', 'пестисы', 'пестис',
              'массажное масло', 'гель-смазка', 'смазка', 'массажная свеча', 'массажные свечи', 'насадка на пенис',
              'насадка на вибратор', 'насадка на мастурбатор', 'спрей', 'гель', 'крем', 'презерватив',
              'презервативы', 'фаллоимитатор', 'для ванны', 'скраб', 'масло', 'фаллос',
              'расширитель', 'феромонами', 'кольцо', 'маска', 'помпа', 'вакуумный', 'бальзам',
              'вибромассажер', 'батарейки', 'гель для рук', 'клиторальная', 'повязка на глаза']

        ed_cats = ['лубриканты', 'стэки эротик', 'уходовые средства эротик', 'наборы игрушек для взрослых', 'вибраторы',
                   'ролевые костюмы эротик', 'комплекты бдсм', 'ошейники эротик', 'простыни бдсм', 'наручники эротик', 'эрекционные кольца',
                   'вагинальные тренажеры', 'трусы эротик', 'стрэпы эротик', 'стрэпы эротик', 'чулки эротик',
                   'пояса эротик',
                   'мастурбаторы мужские', 'пэстис эротик', 'пэстис эротик', 'массажные средства эротик',
                   'лубриканты', 'лубриканты', 'свечи эротик', 'свечи эротик', 'насадки на член',
                   'насадки для вибраторов', 'насадки на мастурбатор', 'лубриканты', 'лубриканты',
                   'уходовые средства эротик', 'презервативы', 'презервативы', 'фаллоимитаторы',
                   'уходовые средства эротив', 'уходовые средства эротик', 'массажные средства эротик',
                   'фаллоимитаторы', 'расширители гинекологические', 'средства с феромонами',
                   'эрекционные кольца', 'маски эротик', 'вакуумные помпы эротик',
                   'вакуумно-волновые стимуляторы', 'уходовые средства эротик', 'вибраторы', 'аксессуары для игрушек эротик',
                   'уходовые средства эротик', 'электростимуляторы', 'головные уборы эротик']

        if 'насадка' in extra:
            if 'фаллоимитатора' in extra\
                    or 'страпона' in extra:
                getting_in_cat_wb.append('насадки на страпон')
            if 'мастурбатор' in extra\
                    or 'мастурбатора' in extra:
                getting_in_cat_wb.append('насадки на мастурбатор')
            if 'член' in extra\
                    or 'члена' in extra:
                getting_in_cat_wb.append('насадки на член')
        for o in range(len(ed)):
            if ed[o] in extra:
                getting_in_cat_wb.append(ed_cats[o])
        res = []
        if len(getting_in_cat_wb) > 1 and 'комплекты бдсм' in getting_in_cat_wb:
            getting_in_cat_wb.remove('комплекты бдсм')
        for i in getting_in_cat_wb:
            cat = i[:1].upper() + i[1:]
            if 'бдсм' in i:
                cat = cat.replace('бдсм', 'БДСМ')
            res.append(cat)
        if len(res) == 0:
            if 'препарат' in extra: res.append('Возбуждающие препараты')
            else: res.append('Наборы игрушек для взрослых')
        elif len(res) > 1 and 'Набор игрушек для взрослых' in res:
            res.remove('Набор игрушек для взрослых')
        return res[0], data.replace(' #', '.')

    def upload_cats(self):
        status_file = os.path.isfile('./pool/SexOptovik/google_downloaded/wb_cats.txt')
        if status_file:
            set_wb_cats = set()
            with open('./pool/SexOptovik/google_downloaded/wb_cats.txt') as f:
                for i in f:
                    set_wb_cats.add(i.lower().rstrip())
            set_wb_cats.remove('')
            return set_wb_cats
        else:
            print('Файл с категориями отсутсвует. Хотите выбрать его вручную?')
            opt = int(input('1 = да\n2 = нет'))
            if opt == 1:
                data_set_wb_cats = main.Functions.get_wb_cats(self)
            else:
                print('Далее необходимы категории. Либо загрузите из гугл диска, этапом ранее. Либо скачайте '
                      'самостоятельно и выберите.\nЗакрываю программу')
                time.sleep(5)
                sys.exit(0)

    def init_stocks(self):
        set_stocks = set()
        url = 'http://sexoptovik.ru/files/all_prod_prices__.csv'
        main.Functions.download_universal(url, path_def='./SexOptovik')
        with open(r"./SexOptovik/all_prod_prices__.csv") as f:
            f.readline()
            for lines in f:
                line = lines.split(";")
                if int(line[3]) >= 1:
                    set_stocks.add(line[0])
        return set_stocks



    def start(self):
        ALL_MEDIA = {}
        countries = ['Англия', 'США', 'Беларусь', 'Бельгия', 'Бразилия', 'Португалия', 'Германия', 'Голландия',
                     'Гонконг', 'Дания', 'Индия', 'Испания', 'Турция', 'Италия', 'Казахстан', 'Канада', 'Корея',
                     'Латвия', 'Малайзия', 'Нидерланды', 'Норвегия', 'Польша', 'Россия', 'Сенегал', 'Сингапур',
                     'Мексика', 'Тайланд', 'Тибет', 'Тибет', 'Украина', 'Франция', 'Швейцария', 'Швеция', 'Шотландия',
                     'Эстония', 'Япония', 'Китай']
        # data_set_wb_cats = Functions.get_wb_cats(self) #загрузка из выборочного файла
        amount_of_items_in_file = int(input(f'Введите число товаров в готовых файлах XLSX\n'
                                            f'По стандарту - {self.CONST_AMOUNT_OF_XLSX_ITEMS}\nВвод: '))
        self.CONST_AMOUNT_OF_XLSX_ITEMS = amount_of_items_in_file

        # загрузить файлы txt

        choose = -1
        while choose < 0 or choose > 2:
            choose = int(
                input(f'Загрузить новые данные ?\n 1 - Да\n0 - Нет\n2  -  Только обновить wb_{self.seller_code}.xslx\n'))
        if choose == 1:
            cwd = self.cwd
            path = Path(cwd, 'pool', 'SexOptovik')
            try:
                shutil.rmtree(path)
                os.rmdir(path)
            except OSError:
                os.mkdir(path)
            except FileExistsError:
                print(f'Пожалуйста, закройте файлы из папки {path}')
            except BaseException:
                print('Ошибка. Попробуйте заново')
                sys.exit(0)
            try:
                self.download_from_google(type=0)
            except google.auth.exceptions.TransportError:
                print('Проверьте соединение\nХотите выбрать файл с категориями вручную?\n1 = да\n2 = нет')
                ch = int(input())
                while ch > 2 or ch < 1:
                    ch = int(input('Введите число 1 ил 2'))
                if ch == 1:
                    print('Еще не сделал')
                    sys.exit(0)
                else:
                    sys.exit(0)
            url = 'http://www.sexoptovik.ru/files/all_prod_info.csv'
            file_path = main.Functions.download_universal(url, path_def='./SexOptovik')

            url = 'http://www.sexoptovik.ru/files/all_prod_d33_.csv'
            file_path = main.Functions.download_universal(url, path_def='./SexOptovik')
        elif choose == 2:
            try:
                path = f'./pool/SexOptovik/google_downloaded/wb_{self.seller_code}.xlsx'
                os.remove(path)
            except OSError:
                google_id = []
                google_name = []
                if self.seller_code == '1277':
                    google_id.append('1SVeUg1-AWWZyTgg9RGkwitOSIDT4Ixul')
                    google_name.append('wb_1277.xlsx')
                elif self.seller_code == '1299':
                    google_id.append('163cgrAFCKd01CGG1FhhT70ibF8d9F7B3')
                    google_name.append('wb_1299.xlsx')
                elif self.seller_code == '1366':
                    google_id.append('1c8eaqFkxmYOPsshXwvMP9z5HaXliS-hs')
                    google_name.append('wb-1366.xlsx')
                self.google_driver(google_ids=google_id, file_names=google_name,
                                   path_os_type='./pool/SexOptovik/google_downloaded')

        else:
            print('Продолжаю со старыми данными\n')
            time.sleep(1.5)
        # !!!!!!!!!!!!!!!!!!!!!!!!!!

        # !!!!!!!!!!!!!!!!!!!!!!!!!!

        PATH_GOOGLE_XLSX = f'./pool/SexOptovik/google_downloaded/wb_{self.seller_code}.xlsx'

        # !!!!!!!!!!!!!!!!!!!!!!!!!!
        checkBrand = "Lasciva Piter Anal Wisteria"
        # if self.seller_code == '1277':
        #     checkBrand = "Lasciva"
        # elif self.seller_code == '1366':
        #     checkBrand = "Piter Anal"
        # elif self.seller_code == '1299':
        #     checkBrand = "Wisteria Lasciva"
        # needed_file_data = Functions.getFolderFile(0, ' существующих товары')
        # if not needed_file_data:
        #    print('Ошибка файла. Попробуйте заново')
        #    sys.exit(0)

        print('Считаю новые товары...')
        set_of_data_artics, errors_set_data_artics, liedBrands = main.Functions.getDataXslx(self, PATH_GOOGLE_XLSX,
                                                                                            sellerCode=self.seller_code, checkBrand=checkBrand)
        #set_of_data_artics = set()
        #errors_set_data_artics = set()

        blacklist_brands = main.Functions.uploadFromFile(self,
                                                         file_path='./pool/SexOptovik/google_downloaded/blacklist_brands_wb.txt',
                                                         isSet=True)
        blacklist_brands = list(map(lambda item: item.rstrip().lower(), blacklist_brands))

        PROBLEM_ITEMS = main.Functions.uploadFromFile(self,
                                                      file_path='./pool/SexOptovik/google_downloaded/problem_items_wb_id.txt',
                                                      isSet=True)
        PROBLEM_ITEMS = list(map(lambda item: item.rstrip().lower(), PROBLEM_ITEMS))
        abs_new_items = 0
        self.current_cats_wb = self.upload_cats()

        opisanie = main.Functions.uploadFromFile(self, file_path='./SexOptovik/all_prod_d33_.csv', isSet=False)
        print(f'Ошибки: {errors_set_data_artics}')

        file_path = './SexOptovik/all_prod_info.csv'

        path_100 = f'./!parsed_items_{self.CONST_AMOUNT_OF_XLSX_ITEMS}'
        try:
            os.mkdir(path_100)
        except FileExistsError:
            pass
        path_100 += f'/{self.seller_code}'
        success = False
        while not success:
            try:
                shutil.rmtree(path_100)
                os.rmdir(path_100)
            except FileNotFoundError:
                os.mkdir(path_100)
                success = True
            except PermissionError:
                input('Пожалуйста, закройте все открытые файлы из папки на нажмите любую клавишу.\n')

        success = False
        _path = './!parsed_full'
        while not success:
            try:
                shutil.rmtree(_path)
                os.rmdir(_path)
            except FileNotFoundError:
                os.mkdir(_path)
                _path += f'/{self.seller_code}'
                os.mkdir(_path)
                success = True
            except PermissionError:
                input('Пожалуйста, закройте все открытые файлы из папки на нажмите любую клавишу.\n')
        count_items_100 = 0
        set_stocks = self.init_stocks()

        with open(file_path) as file:
            ERRORS_ITEMS_BANNED_BRANDS = set()
            for line in file:
                line = line.replace('&quot;', '')
                DATA = list(map(lambda line: line.replace('"', ''), line.split(';')))
                # отсев существующих артикулов
                if DATA[0] not in set_of_data_artics and DATA[0] in set_stocks:
                    if DATA[4].lower() not in blacklist_brands:
                        curr_row_data = {''}
                        # ---                ЗАПОЛНЕНИЕ ШАБЛОНА WB
                        articul = f'id-{DATA[0]}-{self.seller_code}'
                        if articul not in PROBLEM_ITEMS:
                            # id-18474-1277
                            model = name = description = category = extra_info = brand = country = osobennost_model = \
                                vibro = elite = sex = colour = complect = count_items = sostav = photo_str = \
                                material = batteries = opis = check = volume = ed = \
                                length_it = length_up = width_it = width_up = weight = weight_bez_up_kg = \
                                diameter_it = diameter_up = depth_it = depth_up = height_it = height_up = photo_wb = \
                                check_brand = check_photo = h = ''

                            h = opisanie[DATA[0]].replace('"', '').rstrip()
                            opis = f'{h}. '
                            model = DATA[1]  # Модель
                            name = main.Functions.cleanText(DATA[2]).replace('&amp', '')  # Название
                            if name == '':  name = list(map(''.join, opisanie[DATA[0]].split('.; ')))[1].replace('"',
                                                                                                                 '')
                            opis += f'{name}. Модель: {model}. '
                            description = DATA[6]  # Особенность секс игрушки
                            opis += f'{description}. '
                            category_init_data = self.init_category(DATA[3], self.current_cats_wb,
                                                                    extra=f'{name.lower()}')  # Категория
                            category = category_init_data[0]  # Категория
                            extra_info = category_init_data[1]  # Доп. описание (смежные категории)
                            opis += f'{extra_info}. '
                            brand = DATA[4]  # Бренд
                            country = DATA[5]  # Страна производства
                            if '-' in country:
                                country = country[:country.find('-')]
                            osobennost_model = DATA[7][:1].upper() + DATA[7][1:]  # Особенность модели
                            # + Особенность модели
                            if 'с вибрацией' in extra_info:
                                opis += 'С вибрацией. '
                            elif 'без вибрации' in extra_info:
                                opis += 'Без вибрации. '

                            if 'Элитная продукция' in extra_info:
                                opis += 'Элитная продукция. '

                            sex = DATA[8]  # Пол
                            colour = DATA[9]  # Цвет
                            if colour.strip() != '':
                                opis += 'Цвет: ' + colour + '. '
                            count_items = ''
                            if DATA[11] == '':  # Комплектация + Количество предметов в упаковке
                                complect = count_items = '1 шт.'
                            else:
                                complect = DATA[11]
                                count_items = '1 шт.'
                            if DATA[12] != '':
                                sostav = DATA[12]
                            else:
                                sostav = DATA[2]

                            opis += DATA[10]

                            photo_str = DATA[13]
                            photo_urls = list(map(lambda
                                                      photo_str: f'http://sexoptovik.ru/_project/user_images/prods_res/{DATA[0]}/{DATA[0]}_{photo_str}_{self.size_img}.jpg',
                                                  photo_str.split()))
                            material = DATA[15]  # Материал изделия
                            try:
                                material = int(material) - 3
                                material = ''
                                if material != '':
                                    checked = list(map(str, material))[0]
                                    try:
                                        checked = int(checked)
                                        material = ''
                                    except ValueError:
                                        pass
                            except ValueError:
                                if material.strip() != '':
                                    opis += 'Материал: ' + material + '. '
                            # Наличие батареек в комплекте
                            if 'не входят' in DATA[16] or DATA[16] == '':
                                opis += 'Батареек нет в комплекте. '
                            elif 'входят' in DATA[16]:
                                batteries = 'Батарейки в комплекте. '
                                opis += f'{batteries}. '
                            price = 99999  # Розничная цена

                            try:
                                b = list(map(int, DATA[16]))
                                pass
                            except ValueError:
                                opis += f'{DATA[16]}. '

                            check = DATA[2].lower() + '; ' + DATA[3].lower()
                            clothe = ['трусики' in check, 'трусы' in check, 'боди' in check, ' топ ' in check,
                                      'костюм' in check, ' лиф' in check, 'стреп' in check, 'стрэп' in check,
                                      'трус' in check
                                      ]
                            if articul == 'id-21460-1277':
                                print()
                            size_all = size_ru = volume = ''
                            if 'Белье' in description or 'БДСМ' in description or any(clothe):
                                size = self.parse_sizes(DATA[10], 'clothe')
                                size_all = size.get('size')
                                size_ru = size.get('size-ru')
                            elif 'Косметика' in description:
                                size = self.parse_sizes(DATA[10], 'cosmetic')
                                volume = size.get('volume')
                                weight = size.get('weight')  # Вес (г)
                                # if '*' in volume: volume = eval(volume)
                                try:
                                    if weight is None:
                                        weight = volume * 1.1
                                        weight_bez_up_kg = volume
                                except TypeError:
                                    pass
                                ed = size.get('ed')
                            else:

                                size = self.parse_sizes(DATA[10], 'all')

                                length_it = size.get('length')  # Длина
                                if length_it is None or length_it == '':
                                    length_it = length_up = ''
                                elif length_it == 'универсальный (растягивается)':
                                    length_it = 'универсальный (растягивается)'
                                else:
                                    length_it = float(length_it)
                                    length_up = round(length_it + length_it * 0.1)

                                weight = size.get('weight')  # Вес (г)
                                if weight is None or weight == '':
                                    weight = weight_bez_up_kg = ''
                                else:
                                    weight_bez_up_kg = int(weight) / 1000
                                width_it = size.get('width')  # Ширина предмета + ширина упаковки
                                if width_it is None or width_it == '':
                                    width_it = width_up = ''
                                elif width_it == 'универсальный (растягивается)':
                                    width_it = 'универсальный (растягивается)'
                                else:
                                    width_it = float(width_it)
                                    width_up = round(width_it + width_it * 0.1)

                                height_it = size.get('height')  # Высота предмета + высота упаковки
                                if height_it is None or height_it == '':
                                    height_it = height_up = ''
                                elif height_it == 'универсальный (растягивается)':
                                    height_it = 'универсальный (растягивается)'
                                else:
                                    height_it = float(height_it)
                                    height_up = round(height_it + height_it * 0.1)

                                diameter_it = size.get('diameter')  # Диаметр
                                if diameter_it is None or diameter_it == '':
                                    diameter_it = diameter_up = ''
                                elif diameter_it == 'универсальный (растягивается)':
                                    diameter_it ='универсальный (растягивается)'
                                else:
                                    diameter_it = float(diameter_it)
                                    diameter_up = round(diameter_it + diameter_it * 0.1)

                                depth_it = size.get('depth')  # Глубина
                                if depth_it is None or depth_it == '':
                                    depth_it = depth_up = ''
                                elif depth_it == 'универсальный (растягивается)':
                                    depth_it = 'универсальный (растягивается)'
                                else:
                                    depth_it = float(depth_it)
                                    depth_up = round(depth_it + depth_it * 0.1)
                            if len(photo_urls) != 0:
                                for z in range(len(photo_urls) - 1):
                                    photo_wb += photo_urls[z] + '; '
                                photo_wb += photo_urls[len(photo_urls) - 1]

                            #   ПРОВЕРКИ
                            PREDLOGS_RU_LANG = {'с', 'в', 'у', 'о', 'к', 'от', 'до', 'на', 'по', 'со', 'из', 'над',
                                                'под', 'при', 'про', 'без', 'ради', 'близ', 'перед', 'около', 'через',
                                                'вдоль', 'после',
                                                'кроме', 'сквозь', 'вроде', 'вследствие', 'благодаря', 'вопреки',
                                                'согласно',
                                                'навстречу', 'об', '(', ')', 'и', ',', 'за', 'c', 'для'
                                                }

                            temp = list(map(''.join, name.split()))
                            while len(name) >= 40:
                                name = name[:name.rfind(' ')]
                            temp = list(map(''.join, name.split()))
                            while temp[len(temp) - 1] in PREDLOGS_RU_LANG:
                                name = name[:name.rfind(' ')].rstrip()
                                temp = list(map(''.join, name.split(' ')))

                            if len(brand + name) + 1 <= 40:
                                name += f' {brand}'

                            if name.count('(') > name.count(')'):
                                name = name.replace('(', '')
                            elif name.count('(') < name.count(')'):
                                name = name.replace(')', '')


                            check_brand = brand.upper()
                            if check_brand != brand or '(' in brand or ')' in brand or brand == '':
                                if self.seller_code == '1277':
                                    brand = 'Lasciva'
                                elif self.seller_code == '1366':
                                    brand = 'BANANZZA'
                                elif self.seller_code == '1299':
                                    brand == 'Wisteria'
                            opis += f'Ресейллер: {brand}. '

                            if photo_wb == '':
                                for i in DATA:
                                    try:
                                        if i.strip() == '':
                                            flag = True
                                        else:
                                            flag = False
                                        check_photo = list(map(str, i.split()))
                                        for k in check_photo:
                                            if len(k) >= 1 and len(k) <= 2:
                                                flag = True
                                                break
                                        if flag:
                                            pass
                                        else:
                                            photo_wb = ''
                                            photo_urls = list(map(lambda
                                                                      check_photo: f'http://sexoptovik.ru/_project/user_images/prods_res/{DATA[0]}/{DATA[0]}_{check_photo}_{self.size_img}.jpg',
                                                                  check_photo))
                                            for z in range(len(photo_urls) - 1):
                                                photo_wb += photo_urls[z] + '; '
                                            photo_wb += photo_urls[len(photo_urls) - 1]
                                            break
                                    except ValueError:
                                        pass

                            flag = False
                            for datas in DATA:
                                for i in range(len(countries)):
                                    if countries[i] in datas:
                                        country = countries[i]
                                        flag = True
                                        break
                                if flag:
                                    break

                            #           размеры если надо
                            ed_cats = ['Костюм', 'Комплект', 'Наручники',
                                       'Трусы', 'Трусики', 'Стреп', 'Стрэп',
                                       'Чулки', 'Боди', 'Топ', 'Ошейник', 'Платья эротик']
                            for hj in range(len(ed_cats)):
                                if ed_cats[hj] in category and size_ru == '':
                                    size_ru, size_all = '44-46', 'M'

                            opis = opis.replace('. .', '. ').replace(';', '.').replace('..', '. ')
                            if opis[0] == '.':
                                opis = opis[1:]
                            check_size_it = [weight, length_it, width_it, height_it, depth_it]
                            check_size_up = [weight_bez_up_kg, length_up, width_up, height_up, depth_up]
                            check_size_v = [300, 20, 10, 15, 18]
                            for i in range(len(check_size_it)):
                                if check_size_it[i] == '':
                                    check_size_it[i] = check_size_v[i]
                                if check_size_up[i] == '':
                                    check_size_up[i] = round(check_size_v[i] + check_size_v[i] * 0.1)
                            weight, weight_bez_up_kg = weight, weight_bez_up_kg
                            try:
                                length_it, length_up = check_size_it[1], check_size_up[1]
                            except ValueError:
                                length_up = 22
                            try:
                                width_it, width_up = check_size_it[2], check_size_up[2]
                            except ValueError:
                                width_up = 12
                            try:
                                height_it, height_up = check_size_it[3], check_size_up[3]
                            except height_up:
                                height_up = 17
                            try:
                                depth_it, depth_up = check_size_it[4], check_size_up[4]
                            except ValueError:
                                depth_up = 20
                            #if category == 'Презервативы':
                            #    continue

                            if country == 'Англия' or country == 'Соединенное королевство':
                                country = 'Великобритания'
                            if sex == 'для женщин':
                                sex = 'Женский'
                            elif sex == 'для мужчин':
                                sex = 'Мужской'
                            else:
                                sex = 'Женский'

                            vibr_type = ''
                            if elite != '' and vibro != '':
                                vibr_type = elite + '. ' + vibro
                            elif elite != '':
                                vibr_type = elite
                            elif vibro != '':
                                vibr_type = vibro

                            isChanged = False
                            while len(complect) > 100:
                                ind = complect.rfind(',')
                                complect = complect[:ind]
                                isChanged = True
                            if(len(complect) + 6 <= 100 and isChanged):
                                complect +=" и др."


                            abs_new_items += 1

                            current_articul_wb_pattern = {2: category, 3: '', 4: brand, 5: sex, 6: name,
                                                          7: articul, 8: size_all, 9: size_ru,
                                                          10: '',
                                                          11: price, 12: sostav, 13: photo_wb, 14: opis, 15: country,
                                                          16: osobennost_model, 17: osobennost_model, 18: material,
                                                          19: batteries, 20: volume, 21: volume,
                                                          22: f'{volume} {ed}',
                                                          23: width_it, 24: width_up, 25: length_up, 26: length_up,
                                                          27: length_it,
                                                          28: length_it, 29: height_it, 30: height_up,
                                                          31: depth_it, 32: diameter_up, 33: diameter_it,
                                                          34: vibr_type, 35: weight_bez_up_kg, 36: weight,
                                                          37: weight, 38: weight_bez_up_kg, 39: weight, 40: complect,
                                                          41: count_items, 42: 'Непрозрачная анонимная упаковка'
                                                          }

                            count_items_100 += 1




                            for k, v in current_articul_wb_pattern.items():
                                self.parsed_items[k].append(v)
                                self.parsed_items_100_items[k].append(v)
                            if count_items_100 % self.CONST_AMOUNT_OF_XLSX_ITEMS == 0:
                                for kz in range(1, self.CONST_AMOUNT_OF_XLSX_ITEMS + 1):
                                    self.parsed_items_100_items[1].append(kz)
                                main.Functions.save_data(self, self.parsed_items_100_items, seller_code=self.seller_code,
                                                         path=path_100,
                                                         original_name=f'{count_items_100 - self.CONST_AMOUNT_OF_XLSX_ITEMS - 1}-{count_items_100}')
                                self.parsed_items_100_items.clear()
                                self.parsed_items_100_items = {1: ['Номер карточки'], 2: ['Предмет'], 3: ['Цвет'],
                                                               4: ['Бренд'], 5: ['Пол'], 6: ['Название'],
                                                               7: ['Артикул товара'], 8: ['Размер'], 9: ['Рос. размер'],
                                                               10: ['Баркод товара'],
                                                               11: ['Цена'], 12: ['Состав'], 13: ['Медиафайлы'],
                                                               14: ['Описание'],
                                                               15: ['Страна производства'],
                                                               16: ['Особенности секс игрушки'],
                                                               17: ['Особенности модели'], 18: ['Материал изделия'],
                                                               19: ['Наличие батареек в комплекте'], 20: ['Объем'],
                                                               21: ['Объем (мл)'],
                                                               22: ['Объем средства'], 23: ['Ширина предмета'],
                                                               24: ['Ширина упаковки'], 25: ['Длина (см)'], 26: ["Длина упаковки"],
                                                               27: ['Длина секс игрушки'],
                                                               28: ['Рабочая длина секс игрушки'],
                                                               29: ['Высота предмета'], 30: ['Высота упаковки'],
                                                               31: ['Глубина предмета'],
                                                               32: ['Диаметр'],
                                                               33: ['Диаметр секс игрушки'], 34: ['Вид вибратора'],
                                                               35: ['Вес без упаковки'], 36: ['Вес(г)'],
                                                               37: ['Вес средства'], 38: ['Вес товара без упаковки(г)'],
                                                               39: ['Вес товара с упаковкой(г)'],
                                                               40: ['Комплектация'],
                                                               41: ['Количество предметов в упаковке'], 42: ['Упаковка']
                                                               }

                            ALL_MEDIA.setdefault(articul, photo_urls)
                            print(f'{abs_new_items}, ---     > {current_articul_wb_pattern}')
                    else:
                        ERRORS_ITEMS_BANNED_BRANDS.add(DATA[0])
            for i in range(1, len(self.parsed_items[2])):
                self.parsed_items[1].append(i)
            for i in range(1, len(self.parsed_items_100_items[2])):
                self.parsed_items_100_items[1].append(i)
            main.Functions.save_data(self, self.parsed_items, seller_code=self.seller_code,
                                     path=f'./!parsed_full/{self.seller_code}', _print=False, _full=True)
            main.Functions.save_data(self, self.parsed_items_100_items, seller_code=self.seller_code, path=path_100,
                                     original_name=f'{count_items_100}-END')
            # COUNT_ITEMS_ALLPRODINFO = abs_new_items
            # K = 10 ** 10
            # while K >= 0:
            #    #K = COUNT_ITEMS_ALLPRODINFO - len(SET_BARCODES)
            #    print(f'Необходимо дозагрузить еще {K} штрихкодов')
            #    BARCODES_PATH = Functions.getFolderFile(0,
            #                                            ' файл со штрихкодами.\nФайл должен находиться не на диске C:/ ')
            #    barcodes = Functions.uploadBarcodes(BARCODES_PATH).copy()
            #    if not barcodes:
            #        print('Ошибка. Пожалуйста, выберите необходимый файл с WildBerries')

            print(f'Новых товаров найдено:   {abs_new_items}\nЗапрещенных брендов: {len(ERRORS_ITEMS_BANNED_BRANDS)}')

        input('Обработка товаров с сайта Sex Optovik завершена.')

        # -------------------------------------------------------------------

    def __init__(self, seller_code, preview='SexOptovik'):
        self.checkBrand = None
        self.preview = preview
        main.Functions.showText('Sex Optovik')
        self.seller_code = str(seller_code)

        # print(f'\n--------------------------------------------'
        #      f'\nSexOptovik\n\ncwd:  {self.cwd}')

        res = self.start
        # if not(res):
        #    print('Чтобы начать заново нажмите Enter\nЧтобы выйти нажмите Escape')

        # p 'Доделать !!!!'
