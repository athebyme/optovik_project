from dataclasses import dataclass
from Google import Create_Service

CLIENT_SECRET_FILE = '.\client_secrets.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']


@dataclass
class Config:
    shopName = str
    uniqueId = str  # уникальное айди магазина ( в случае повторов айди на магазине )
    sellerId = int
    urlExistItems = str
    urlStocks = str
    urlItems = str

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
