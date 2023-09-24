# Коммерческий проект парсеров товаров

![Project Logo](images/logo.jpg)

---

## Описание

Этот проект представляет собой систему парсинга товаров с различных онлайн-магазинов. В настоящее время поддерживаются следующие площадки:

1. **Wildberries** (файлы `SexOptovik_wb` и `main.py`)

2. **Ozon** (в ветке `ozon-dev`)

Проект основан на использовании Google Drive API для загрузки обновленной информации и управления конфигурацией.

---

## Особенности

1. **Улучшенная оптимизация работы с таблицами**:

   - Оптимизация скорости выполнения операций на 2-3 раза.
   - Сокращение объема просматриваемых данных до 10-100 раз.

2. **Система распознавания категорий**:

   - Точность распознавания составляет ~95-98%.
   - В оставшихся случаях товар попадает в близкую (похожую) категорию.

3. **Распознавание размеров**:

   - Разработана система распознавания размеров предметов/одежды.
   - Возможность отладки изначально поврежденной информации.

4. **Множество технологий и решений**:

   - Использование Google Spreadsheet для хранения базы данных продавцов и товаров.
   - Автообновляемая база данных товаров, их описаний и цен.
   - Автогенерация API запросов для получения данных с Ozon.
   - Удобная привязка к магазину через API.
   - Применение KNN алгоритма для определения совпадения характеристик товаров.
   - Наработки по NLP и определению цвета по фотографии.

---

## Установка и Запуск

1. Клонируйте репозиторий:

   ```bash
   git clone [https://github.com/athebyme/project](https://github.com/athebyme/optovik_project).git

Установите необходимые зависимости:

bash
Copy code
pip install -r requirements.txt
Следуйте инструкциям в соответствующих директориях (SexOptovik_wb и ozon-dev) для запуска парсеров.



__Автор__
Брюхов Антон (athebyme/emybehta)
__Контакты__
Если у вас есть вопросы или предложения, пожалуйста, свяжитесь с нами:

Email: ab@athebyme.ru
