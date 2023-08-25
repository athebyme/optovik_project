#                                                   MEGA PARSER 2004

from fileinput import close
import time
import os
import pandas as pd
import openpyxl
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
#os.startfile('"C:\Python\items_parser\items_parser\items_parser.py"','runas')
items_saved = set()
global_data = {1:['Номер карточки'],	2:['Категория товара'],	3:['Бренд'],	4:['Артикул поставщика'],	5:['Артикул цвета'],	6:['Пол'],	7:['Размер'],	8:['Рос. размер'],	9:['Штрихкод товара'],	10:['Розничная цена'],	11:['Состав'],	12:['Комплектация'],	13:['Фото'],	14:['Страна производства'],	15:['Тнвэд'],	16:['Основной цвет'],	17:['Доп. цвета'],	18:['Ключевые слова'],	19:['Описание'],	20:['Вес (г)'],	21:['Вес без упаковки (кг)'],	22:['Вес вагинального шарика'],	23:['Вес с упаковкой (кг)'],	24:['Вес средства'],	25:['Вес товара без упаковки (г)'],	26:['Вес товара с упаковкой (г)'],	27:['Вид бюстгальтера'],	28:['Вид вибратора'],	29:['Вид головного убора'],	30:['Вид замка'],	31:['Вид застежки'],	32:['Вид колготок'],	33:['Вид лубриканта'],	34:['Вид маски'],	35:['Вид мастурбатора'],	36:['Вид насадки на член'],	37:['Вид начинки'],	38:['Вид печенья'],	39:['Вид пульсатора'],	40:['Вид ролевого костюма'],	41:['Вид страпона'],	42:['Вид упаковки'],	43:['Вид фаллоимитатора'],	44:['Вид шоколада'],	45:['Вкус'],	46:['Внутренний диаметр предмета'],	47:['Возрастные ограничения'],	48:['Вставка'],	49:['Высота предмета'],	50:['Высота упаковки'],	51:['Глубина предмета'],	52:['Глубина упаковки'],	53:['Группа аромата'],	54:['Действие лубриканта'],	55:['Декоративные элементы'],	56:['Диаметр'],	57:['Диаметр (мм)'],	58:['Диаметр колеса'],	59:['Диаметр предмета'],	60:['Диаметр секс игрушки'],	61:['Длина (см)'],	62:['Длина изделия'],	63:['Длина изделия по спинке'],	64:['Длина перчаток/варежек'],	65:['Длина предмета'],	66:['Длина секс игрушки'],	67:['Количество капсул/таблеток'],	68:['Количество отделений'],	69:['Количество предметов в наборе'],	70:['Количество предметов в упаковке'],	71:['Количество предметов в упаковке (шт.)'],	72:['Количество шариков'],	73:['Коллекция'],	74:['Максимальная нагрузка'],	75:['Максимальная температура хранения'],	76:['Материал изделия'],	77:['Материал поводка'],	78:['Материал подкладки'],	79:['Материал посуды'],	80:['Место воздействия секс-игрушки'],	81:['Минимальная температура хранения'],	82:['Модель'],	83:['Модель трусов'],	84:['Назначение белья/купальника'],	85:['Назначение интимной помпы'],	86:['Наличие батареек в комплекте'],	87:['Наполнитель'],	88:['Объем'],	89:['Объем (мл)'],	90:['Объем парфюмерии'],	91:['Объем средства'],	92:['Объем товара'],	93:['Основа лубриканта'],	94:['Особенности белья'],	95:['Особенности календаря'],	96:['Особенности модели'],	97:['Особенности подушки'],	98:['Особенности посуды'],	99:['Особенности продукта'],	100:['Особенности секс игрушки'],	101:['Особенности сумки'],	102:['Параметры модели на фото (ОГ-ОТ-ОБ)'],	103:['Питание'],	104:['Пищевая ценность белки'],	105:['Пищевая ценность жиры'],	106:['Пищевая ценность углеводы'],	107:['Пол куклы'],	108:['Поступательное движение'],	109:['Противопоказания'],	110:['Рабочая длина секс игрушки'],	111:['Размер простыни'],	112:['Рисунок'],	113:['Рост куклы'],	114:['Рост модели на фото'],	115:['Ротация'],	116:['Сезон'],	117:['Содержание какао'],	118:['Состав бижутерии'],	119:['Состав эротического набора'],	120:['Срок годности'],	121:['Текстура'],	122:['Тип календаря'],	123:['Тип косметики'],	124:['Тип крепления листов'],	125:['Тип посадки'],	126:['Тип рукава'],	127:['Тип свечи'],	128:['Тип эротической посуды'],	129:['Толщина (мм)'],	130:['Транспортировка'],	131:['Упаковка'],	132:['Уход за вещами'],	133:['Фактура материала'],	134:['Фактура материала белья'],	135:['Форма выпуска'],	136:['Форма упаковки'],	137:['Формат листов'],	138:['Хрупкость'],	139:['Ширина предмета'],	140:['Ширина ремешка'],	141:['Ширина упаковки'],	142:['Энергетическая ценность калории (на 100 гр.)'] }
data_as = {}
wb_as = {}
seller_code =''
it_c = curRow  = 1
excel_file = 'excel_files/as_price_and_num_rrc.csv'
abs_path = Path(Path.cwd())
def downloadNewItems(post):
    import urllib, requests
    print('\nСкачиваю файл с новыми товарами\n')
    if(post.lower().strip() == 'асткол'): 
        path = Path(abs_path,'excel_files','as_price_and_num_rrc.csv')
        try:
            os.remove(path)
        except OSError:
            print('Закройте файл(ы) с товарами')
            return 0
    try:
        excel_file = open(path,'wb')
        try:
            excel_file.write(urllib.request.urlopen('http://www.sexoptovik.ru/mp/as_price_and_num_rrc.csv').read())
        except BaseException: 
            print('Ошибка создания файла. Используются старые данные.\n')
        excel_file.close()
    except OSError:
        print('Ошибка создания файла. Используются старые данные.\n')
        return -1
    else:
        print('Новые товары успешно загружены.\n')
        return 1
    return 0
savedData = Path(abs_path,'SavedData','SavedData.txt')
def cleanData():
    global savedData
    if(savedData.exists()):
        os.remove(savedData)
    else:
        with open(savedData,'w') as f:
            print('\nФайл информации об актуальных артикулах пересоздан\n')
def saveData(prefix_code):
    cleanData()
    global global_data
    if(prefix_code =='as'):
        try:
            data = global_data.get(1)[1:]
            global savedData
            N = len(data)
            with open (savedData,'w') as f:
                f.write(str(N)+'\n')
                for i in range(N):
                    f.write(str(data[i][:4])+'\n')
            return True
        except BaseException:
            return False
def openSavedData():
    global savedData,items_saved
    items_saved.clear()
    with open(savedData,'r') as f:
        N = int(f.readline())
        for i in range(N):
            items_saved.add(f.readline()[:2])
def delsymb(s):
    s = s.replace('"','')
    s = s.replace("'",'')
    s = s.replace('°','')
    s = s.replace("\\",'')
    s = s.replace('&#39D','')
    s = s.replace('&trade','')
    s = s.replace('–','')
    s = s.replace('’','')
    s = s.replace('&reg','')
    s = s.replace('&quot','')
    s = s.replace('&nbsp','')
    s = s.replace('&raquo','')
    s = s.replace('&laquo','')
    s = s.replace('&ndash','')
    s = s.replace('&bul','')
    s = s.replace('&mdash','')
    s = s.replace('…','.')
    s = s.replace('x000D','')
    s = s.replace('¶','')
    s = s.replace('«','"')
    s = s.replace('»','"')
    s = s.replace('®','')
    s = s.replace('`','"')
    s = s.replace('_','')
    s = s.replace('”','"')
    s = s.replace('“','"')
    s = s.replace('™','')
    s = s.replace('=','-')
    s = s.replace('obj','')
    s = s.replace('—','-')
    s = s.replace('•','')
    s = s.replace('–','-')
    #s = s.replace(' ','')
    return s
def parseSymbs(s,breathe):
    arrS = list(map(''.join,s))
    while '<' in arrS:
        curD = arrS.index('<')
        for chars in range(curD,len(arrS)):
            if(arrS[chars]=='>'):
                arrS[chars]=''
                break
            arrS[chars]=''
    s = ''.join(arrS)
    s = delsymb(breathe) + '. ' + delsymb(s)
    a = len(s)
    if(a)>1000:
        while a>=1000:
            ax = s.rfind('.')
            s = s[:ax]
            a = len(s)
        #temp1 = list(map(''.join,s))
        #a = len(temp1)
        #while (a >1000) or temp1[a-1]!='.':
        #    temp1[a-1] = ''
        #    a-=1
        #s = ''.join(temp1)
        s+='.'
    return s
def Osob(data,inf):
    if(int(data)!=0):
        x = int(inf)
        if(x == 24): return 'Количество скоростей вибрации: ' + data +'. '
        if(x == 25): return 'Количество режимов вибрации: ' + data +'.'
    else:
        return ''
def getDiam(data):
    try:
       a = int(data[:len(data)-3])
    except BaseException: return ''
    if(data == 0): return ''
    return data
def getWeight(data,ed):
    if(int(data[:len(data)-3])==0): 
        if(ed=='g'): return data
        if(ed=='kg'): return str(int(data[:len(data)-3])//1000)
    return data
def getGHW(data,needed):
    try:
        a = int(data[:len(data)-3])
        if(a==0): return ''
        elif(a!=0) and(needed): return a//10
    except BaseException: 
        #if(needed) :return 10
        #else: return ''
        return ''
    return ''
def getArticulWB(code,post):
    if(post=='as'): return code +'Z1C1L'+ data_as.get(1)
def _replaceArtic(model):
    return data_as.get(3).replace(model+' / ','',1)
def downloadIMGS(URL,extraPhsSTR,articul_it):
    import os, pathlib, urllib.request, shutil, time
    from pathlib import Path
    err = False
    a = URL
    path = Path(abs_path,'IMGS_AS',articul_it)
    extraPhsLIST = list(map(str,extraPhsSTR.split(',')))
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    path = Path(str(path)+'\\photo')
    os.mkdir(path)
    out = open(Path(str(path) + '\\'+articul_it+'_1'+'.jpg'),'wb')
    try:
        out.write(urllib.request.urlopen(a).read())
    except BaseException: 
        time.sleep(1)
        err = True
    out.close()
    if(len(extraPhsLIST)>0):
        if(extraPhsLIST[0]!=''):
            if(err): xc = 1
            else: xc = 0
            for i in range(len(extraPhsLIST)):
                try:
                    resource = urllib.request.urlopen(str(a[:a.rfind('/img')]+extraPhsLIST[i]))
                    p = Path(str(path) + '\\'+articul_it+'_'+str(i+2-xc)+'.jpg')
                    out = open(p, 'wb')
                    out.write(resource.read())
                    out.close()
                except BaseException:
                    continue
        return a
    else:
        return ''
def getCountry(Country):
    Countries = {"США":"Соединенные Штаты", "Англия":"Соединенное Королевство","Великобритания":"Соединенное Королевство","N": "Китай","Корея":"Корея, Республика ","КНДР":"Демократическая республика Корея","CHN":"Китай","Ю.Корея":"Корея, Республика","Республика Беларусь":"Беларусь"}
    if(Country.count(',')>0): Country = Country[:Country.find(',')]
    if(Countries.setdefault(Country)!=None):
        return Countries.get(Country)
    else:
        return Country
def getUkrash(breathe):
    if('фалос' in breathe): return 'Фаллоимитаторы'
    if('лассо' in breathe): return 'Плетки эротик'
    if('на соски' in breathe): return 'Зажимы для сосков'
    if('чокер' in breathe): return 'Чокеры эротик'
    if('парик' in breathe): return 'Сувениры эротик'
    if('портупея' in breathe): return 'Топы эротик'
    if('каре' in breathe): return 'Сувениры эроти'

def newsCats(breathe,cats_ex,cats):
    b = breathe.lower()
    for i in cats_ex.keys():
        if(i in b): return cats_ex.get(i)
    for i in cats.keys():
        if(i in b): return cats.get(i)

def odejda(data):
    t = data.lower()
    if('боди'in t)or('футболк' in t): return 'Боди эротик'
    if('трус' in t): return 'Трусы эротик'
    if('комплект'in t): return 'Комплекты игрушек для взрослых'
    if('ремень' in t): return 'Комплекты БДСМ'
    else: return 'Комплекты игрушек для взрослых'
    return data
def nasadki(breathe):
    if('на фаллос' in breathe): return 'Насадки на член'
    if('насадки без вибрации' in breathe): return 'Насадки на член'
    if('насадка на пенис' in breathe): return 'Насадки на член'
    if('насадка' in breathe): return 'Насадки на страпон'
def getSexPrisp(breathe):
    if('качели' in breathe): return 'Секс качели'
    if('кресл' in breathe): return 'Секс кресла'
    if('фиксац' in breathe): return 'Фиксаторы эротик'
    if('набор' in breathe): return 'Наборы игрушек для взрослых'
    if('простын' in breathe): return 'Простыни БДСМ'
    if('пилон'in breathe): return 'Комплекты БДСМ'
def getCatWb(data,breathe,opis):
    extra_inf = breathe.lower()
    data = data.lower()
    cats ={}
    cats_ex = {}
    newCat_data = newsCats(extra_inf,cats_ex,cats)
    
    if(data.count(',')>1):
        extraData = data[data.find(',')+1:]
        extraData = data[data.find(',')+1:]
    else:
        extraData = data[data.rfind(',')+1:]
    if(data.count(',')>0): data = data[:data.find(',')]
    cats_ex = {'набор':'Наборы игрушек для взрослых','анальн шарик':'Анальные шарики','плаг':'Анальные пробки','анал плаг':'Анальные пробки', 'анальные бусы':'Анальные бусы','анальная пробка':'Анальные пробки','анальн фаллоимитатор': 'Фаллоимитаторы','анальные расширители': 'Расширители гинекологические','анальны вибромассажер':'Анальные бусы','анальный душ':'Фаллоимитаторы','массажер простат':'Массажеры простаты','эрекционн кольц':'Эрекционные кольца','вагинальн шарик':'Вагинальные шарики','анальн пробк':'Анальные пробки','мастурбатор':'Мастурбаторы мужские','зажим для сосков':'Зажимы для сосков','зажим на соски':'Зажимы для сосков','браслет':'Браслеты эротик','кляп':'Кляпы эротик','многохвостн плет':'Плетки эротик','пояс верност':'Пояса верности','ошейник':'Ошейники эротик','расширител влагальщн':'Расширители гинекологические','сбру':'Боди эротик','наручники':'Наручники эротик','маск':'Маски эротик','стэк':'Стэки эротик','фиксаци':'Фиксаторы эротик','чокер':'Чокеры эротик','шлепалк':'Шлепалки эротик','вибропул':'Вибропули','свеч':'Свечи эротик','свеча':'Свечи эротик','массажн':'Массажные средства эротик','очищающ средств для игрушек':'Средства для очистки секс-игрушек','парфюмерия':'Ароматизаторы эротик','насадк':nasadki(extra_inf),'шарик':'Анальные шарики','виброяйцо':'Виброяйца','вакуумны стимулятор':'Вакуумно-волновые стимуляторы','вакуумные':'Вакуумные помпы эротик','плать':'Платья эротик','трус':'Трусы эротик','чулки':'Чулки эротик'}
    cats = {"фаллоимитатор":"Фаллоимитаторы", "лубрикант":"Лубриканты","стимулятор клитора":"Вагинальные тренажеры","бдсм": "Комплекты БДСМ","вагин":"Мастурбаторы мужские","вибромассажер":"Вибраторы","игрушки из стекла":"Наборы игрушек для взрослых","интимная косметика":"Уходовые средства эротик",'комплекты белья':'Комплеты эротик',"куклы":"Секс куклы","менструальные чаши":"Спринцовки эротик","насадки и кольца":"Эрекционные кольцо","новинки":newCat_data,"помпы":"Гидропомпы эротик","продукция с  феромонами":"Концентраты феромонов","секс-машин":"Секс машины","секс-приспособления":getSexPrisp(extra_inf),"скоро в продаже":newCat_data,"стимуляторы итора":"Вибраторы","страпон":"Страпоны","украшения":getUkrash(extra_inf),"электростимулятор":"Электростимуляторы","эльмято":newCat_data,"эротическое елье":"Комплекты БДСМ","промо": newCat_data,"анальные стимуляторы":"Вибраторы","игрушка из стекла":"Сувениры эротик","наборы секс-игрушек":"Наборы игрушек для взрослых","плаг":"Анальные пробки",'стимулятор клитор':'Вибраторы'}
    if(True):
        for i in cats_ex.keys():
            if(i in extra_inf): return cats_ex.get(i)
    for i in cats.keys():
        if(i in data): return cats.get(i)
    if(data==''): return newsCats(extra_inf,cats_ex,cats)
    if(data=='эротическое белье'): return odejda(opis)
    if('тренажеры кегеля' in data): return newsCats(breathe,cats_ex,cats)
    return data
def getSex(data):
    if(data.count('мужской')!=0):
        return 'Мужской'
    if(data.count('женский')!=0):
        return 'Женский'
    return ''
def getWeight(data,ed):
    try:
        ndata = int(data[:data.rfind('.')])
    except BaseException: 
        return ''
    ndata = int(data[:data.rfind('.')])
    if(ed == 'kg'):
        if(ndata!=0): return str(ndata//1000)
        else: return '0.3'
    else:
        if(ndata!=0): return str(ndata)
        else: return '300'
def getColour(data):
    s = data
    if('_' in data): s = s.replace('_',',')
    if('/' in data): s =s.replace('/',',')
    return s

def createDf(wb_data):
    x = wb_data
    locDf = {}
    global global_data
    for i in range(1,143):
        locAr = []
        if(x.setdefault(i)!=None):
            global_data[i].append(x.get(i))
        else:
            global_data[i].append('')
        #locDf.setdefault(i,locAr)
    #return locDf
    return global_data

def dir_work(isSave):
    cwd = os.getcwd()
    if(isSave):
        path_excel_wb = cwd
        os.chdir(path_excel_wb)
        return os.listdir('../..'), path_excel_wb
    else: 
        path_excel_wb = Path(abs_path, '!put_wb_here')
        os.chdir(path_excel_wb)
        return os.listdir('../..')
def wcurex(wb_data):
    from pathlib import Path
    dw = dir_work(True)
    file = dw[0][0]
    path = dw[1]
    xl = pd.ExcelFile(file)
    x = pd.DataFrame(wb_data)
    try:
        x.to_excel(Path(path,file))
    except BaseException:
        a = input('Закройте файл, нажмите Enter')
        x.to_excel(Path(path,file))

def start(wb_data):
    file = dir_work(False)[0]
    df = createDf(wb_data)
    #wcurex(df)

def _switch(cat_num,s):
    print('Ввожу категории для -- ', cat_num,' -- товара',end='')
    #for i in range(s.count(';')):
        #s = item[i:]
errors = 0
#shrihs = Path(abs_path,'excel_files','shtrihs','Список штрихкодов.csv')
data_shtrih =[]
def getShrihs():
    print('Получаю список штрихкодов\n')
    try:
        root = tk.Tk()
        root.withdraw()
        shtrihs_path = filedialog.askopenfilename()
        with open(shtrihs_path, encoding="utf8") as f:
            a = f.readline()
            lst = list(f.readlines())
            global data_shtrih
            data_shtrih = lst.copy()
        print('Штрихкоды успешно загружены.')
        time.sleep(1.5)
        return True
    except OSError:
        print('Ошибка при поиске файла.')
        return False
    
def fill_items():
    it = Ls = 1
    with open (excel_file) as f:
        global errors
        wb_as = {}
        s = list(f.readlines())
        lS = len(s)
        del s[0]
        for item in s:
            data_as.clear()
            wb_as.clear()
            info = item
            L = info.count(';')
            if(L!=49): 
                errors+=1
                print('Найдена ошибка! Продолжаю дальше')
                continue
            for cats in range(1,L+1):
                r = info.find(';')
                ex_info = info[:r]
                info = info[r+1:]
                data_as.setdefault(cats,ex_info)
            locShtr = data_shtrih[it-1]
            locShtr = locShtr[:len(locShtr)-1]
            text_op = parseSymbs(data_as.get(13),data_as.get(18))
            wb_as = {1:s.index(item)+1, 2:getCatWb(data_as.get(16),data_as.get(18),text_op),3:data_as.get(29),5:getArticulWB(seller_code,'as'),6:getSex(data_as.get(13)),7:'',8:'',9:locShtr,10:99999,11:data_as.get(9),12:'1 шт.',13:downloadIMGS(data_as.get(7),data_as.get(41),locShtr),14:getCountry(data_as.get(11)),15:'',16:getColour(data_as.get(34)).lower(),17:'',18:data_as.get(18).replace('"','').replace("'",''),19:text_op,20:getWeight(data_as.get(44),'g'),21:getWeight(data_as.get(39),'kg'),25:getWeight(data_as.get(44),'g'),28:data_as.get(10),46:getDiam(data_as.get(22)),47:'18+',49:getGHW(data_as.get(45),True),50:getGHW(data_as.get(45),True),51:getGHW(data_as.get(47),True),52:getGHW(data_as.get(47),True),56:getDiam(data_as.get(22)),61:getDiam(data_as.get(21)),65:getDiam(data_as.get(20)),66:getDiam(data_as.get(21)),71:1,73:data_as.get(12),76:data_as.get(9),88:data_as.get(48),89:data_as.get(48),93:data_as.get(9),96:Osob(data_as.get(24),24) + Osob(data_as.get(25),25),110:getGHW(data_as.get(21),False),131:"Непрозрачная анонимная упаковка",141:getGHW(data_as.get(46),True)}
            start(wb_as)
            it+=1 
            print('выполняю шаг: ',it,' из --> ',lS)
        global global_data
        nums = ['Номер карточки']
        for i in range(1,len(global_data.get(4))):
            nums.append(i)
        global_data[0] = nums.copy()
        print('\nСохраняю готовую таблицу\n')
        wcurex(global_data)
        return lS
def main():
    import time, sys
    global seller_code
    postavshik = input('Введите поставщика: ')
    seller_code = input('Введите код продавца: ')
    #saveData()
    input('ДЛЯ ДЕБАГА')
    input('ДЛЯ ДЕБАГА')

    downlit = downloadNewItems(postavshik)
    if(downlit==0)or(downlit==-1): 
        time.sleep(2)
        try: 
            print('Пробую скачать заново\n')
            a = input('\nЗакройте файл и нажмите Enter\n')
            downlit = downloadNewItems(postavshik)
            t = downloadNewItems(postavshik)
            if(downlit==0)or(downlit==-1):
                print('Ошибка. Попробуйте запустить приложение заново.')
                time.sleep(2)
                sys.exit(0)
        except OSError:
            print('Ошибка. Попробуйте перезапустить приложение.')
            sys.exit(1)
    input('ДЛЯ ДЕБАГА')
    input('ДЛЯ ДЕБАГА')
    if not(getShrihs()): 
        time.sleep(3)
        sys.exit()
    good = fill_items()
    global errors
    print('Готово! Удачно загруженные файлы: :',good, '\\ Ошибок: ', errors)
    print('\nОбновляю актуальную информацию по артикулам\n')
    time.sleep(1)
    if(saveData(postavshik)):
        print('\nУспешно !\n')
    else:
        print('\nНе удалось обновить информацию об актуальных товарах.\n')


# старт
if __name__ == "__main__":
    main()