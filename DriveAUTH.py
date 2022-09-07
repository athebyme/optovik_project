from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()

def create(file_name = 'test',file_content = 'Hello World!'):
    try:
        drive = GoogleDrive(gauth)

        print(my_file)
    except Exception as ex:
        return  'Got some troubles, check code please!'
def main():
    print(create())

if __name__ == '__main__':
    main()