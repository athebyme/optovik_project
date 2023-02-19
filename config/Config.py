from dataclasses import dataclass

@dataclass
class Config:
    shopName = ''
    uniqueId = ''   #уникальное айди магазина ( в случае повторов айди на магазине )
    sellerId = 1
    urlExistItems = ''
    urlStocks = ''
    urlItems = ''
