import os
from dataclasses import dataclass
from src import LoadDB as dbs

import src.ExceptionService.Exceptions
from Google import Create_Service
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build




CLIENT_SECRET_FILE = '.\client_secrets.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']


@dataclass
class Config:
    shopName = str
    uid = str  # уникальное айди магазина ( в случае повторов айди на магазине )
    id = int
    driveIdExistItems = str
    urlStocks = str
    urlItems = str
    marketplace = str
    checkBrand = str


    creds=None
    DriveService = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    SpreadsheetService=None

class ConfigInitializer(Config):

    def fillConfig(self, sellerData):
        driveService = dbs.DB_loader()
        request = driveService.getInfo(
            marketplace=sellerData['marketplace'],
            id=sellerData['id'])
        self.uid = request[0][0]
        self.marketplace = request[0][1]
        self.id = request[0][2]
        self.shopName = request[0][3]
        self.driveIdExistItems = request[0][4]
        self.urlItems = request[0][7]
        self.urlStocks = request[0][8]
        self.checkBrand = request[0][9]
    def checkValid(self, sellerData):
        #тут какая то проверка на правильность параметров словаря

        if isinstance(sellerData,dict):
            if sellerData['marketplace'] is not None and sellerData['id'] is not None: return True
        return False

    def buildService(self, creds):
        self.SpreadsheetService = build('sheets', 'v4', credentials=creds)

    def importCredentials(self, scopes):
        credentials = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('C:\csv_parser_wb\credentials\Google\client_secrets.json',
                                                                 ['https://www.googleapis.com/auth/spreadsheets'])
                credentials = flow.run_local_server()
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)
        self.buildService(creds=credentials)
        return credentials

    def __init__(self, sellerData):
        self.importCredentials(scopes=SCOPES)
        if(self.checkValid(sellerData)): self.fillConfig(sellerData)
        else: raise src.ExceptionService.Exceptions.CustomError("[!] Проверьте данные продавца")
