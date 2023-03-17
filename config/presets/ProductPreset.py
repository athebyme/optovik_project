from dataclasses import dataclass


@dataclass
class Product:
    local_number: int  # №
    product_name: str  # Название товара
    content: str  # Состав*
    pack_height: int  # Высота упаковки, мм*
    main_photo: str  # Ссылка на главное фото*
    max_temp: int  #Максимальная температура
    pack_count: int  # Единиц в одном товаре*
    pack_width: int  # Ширина упаковки, мм*
    pack_length: int  # Длина упаковки, мм*
    NDS: int  # НДС, %*
    effect: str
    alternative_name: str #
    model_name: str  # Название модели (для объединения в одну карточку)*
    brand: str  # Бренд*
    danger_class: str #Класс опасности товара*
    price: int  # Цена, руб.*
    min_temp: int #Минимальная температура
    pack_weight: int  # Вес в упаковке, г*
    commercial_type: str  # Коммерческий тип*
    article_number: str #Артикул*
    volume: int #Объем, мл*
    expire_date: int #Срок годности в днях
    type: str  # Тип* <= 4 types
    extra_photo: list  # Ссылки на дополнительные фото
    color: str  # Цвет товара
    color_name: str  # Название цвета
    aroma_adult: str #Аромат 18+
    aroma_classification: str #Классификация аромата
    warranty: int  # Гарантия на товар, мес.
    manufacturer_country: str #Страна-изготовитель
    sex: str #Пол
    consistent: str #Основа состава
    annotation: str  # Аннотация
    keywords: str  # Ключевые слова
    only_adult: str #Признак 18+
    texture: str #Текстура
    material: str #Материал
    method_of_use: str #Способ применения
    purpose: str  # Назначение товара 18+
    age_bound: str  # Возрастные ограничения
    sizes_mm: str  # Размеры, мм
    count_packs: int  # Количество заводских упаковок
    size_eu: str  # Размер БДСМ-атрибутики
    vibration: str  # Вибрация
    bundle: str  # Состав комплекта
    barcode: str  # Штрихкод (Серийный номер / EAN)
    product_weight: int  # Вес товара, г
    weight: int #Вес, г
    length: int #Длина, см
    model: str #Название модели для шаблона наименования
    working_length: int #Длина рабочей части, мм
    width: int #Ширина/диаметр, мм
    perfume_type: str #Вид парфюмерии (служебный)
    # Состав комплекта