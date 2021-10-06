from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import datetime
import os
import os.path
import time
import datetime
from dateutil import tz
from os import path
import logging

dest = r"F:\THAPPAR 2020\SEMESTER 5\UCS531 Cloud Computing\Lab\SyncFolder"
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

gauth = GoogleAuth()

gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

logging.basicConfig(filename='history.log', format='%(asctime)s :: %(message)s' , datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.ERROR)

drive = GoogleDrive(gauth)


def fileUpdate(dest, fileName, file_list):
    for file in file_list:
        #         print(file)
        if file[0] == fileName:
            new_file = drive.CreateFile({'title': file[0], 'id': file[2]})
            file_content = new_file.GetContentString()
            localFile = open(os.path.join(dest, fileName), 'r')
            file_content = localFile.read()
            new_file.SetContentString(file_content)
            new_file.Upload()

            logFile = open("history.log", "a")
            time = datetime.datetime.now()
            string = "{}  - Backup Successfull {}\{}\n".format(time, dest, fileName)
            logFile.write(string)
            logFile.close()

            logging.info('File Name - {} - updated on Drive.'.format(file[0]))
    print("File Updated on Drive")


def fileUpload(dest, fileName, foldId):
    f = drive.CreateFile({'parents': [{'id': foldId}], 'title': fileName})
    f.SetContentFile(os.path.join(dest, fileName))
    f.Upload()

    print("Updating Log File")
    logFile = open("history.log", "a")
    time = datetime.datetime.now()
    string = "{}  - Backup Successfull {}\{}\n".format(time, dest, fileName)
    logFile.write(string)
    logFile.close()

    logging.info('File Name - {} - uploaded on Drive.'.format(fileName))
    print("New File Uploaded on Drive")
    f = None


def toUploadFile(dest, LocalFile, fileName, fileMetaData, foldId):
    #     print("To Upload inside ------- ", dest)
    if LocalFile not in fileName:
        print(LocalFile)
        print("File Not present on drive - Uploading")
        fileUpload(dest, LocalFile, foldId)
    else:
        print(LocalFile)
        print("File already present on drive - Checking Modifications")

        local = time.ctime(os.path.getmtime(os.path.join(dest, LocalFile)))
        localModified = datetime.datetime.strptime(local, "%a %b %d %H:%M:%S %Y")
        print("Last modified on Local: %s" % localModified)
        localModified = os.path.getmtime(os.path.join(dest, LocalFile))
        # print("Last modified on Local: %s" % localModified)

        cloud = fileMetaData[fileName.index(LocalFile)][1]
        cloud = cloud[:-5]
        driveModified = datetime.datetime.strptime(cloud, "%Y-%m-%dT%H:%M:%S")

        onlineTime = driveModified.replace(tzinfo=from_zone)
        onlineTime = onlineTime.astimezone(to_zone)
        onlineTime = onlineTime.strftime("%Y-%m-%d %H:%M:%S")
        print("Last Modified on drive: %s" % onlineTime)
        onlineTime = time.mktime(time.strptime(onlineTime, "%Y-%m-%d %H:%M:%S"))
        # print("Last Modified on drive: %s" %onlineTime)

        if localModified > onlineTime:
            print("Modification Observed, Uploading On Drive")
            fileUpdate(dest, LocalFile, fileMetaData)
        else:
            print("File is Already Up to date")


def toCreateFolder(dest, fName, pId):
    folder = drive.CreateFile({'title': fName, 'mimeType' : 'application/vnd.google-apps.folder' ,'parents':[{'id':pId}]})
    folder.Upload()


def mainImplementation(destination, folderId):
    #     print("Inside ------- ", destination)
    fileMetaData = []
    fileName = []

    request_template = "'{x}' in parents and trashed=false"
    file_list = drive.ListFile({'q': request_template.format(x=folderId)}).GetList()

    for file in file_list:
        fileMetaData.append([file['title'], file['modifiedDate'], file['id'], file['mimeType']])

    for i in fileMetaData:
        fileName.append(i[0])

    for z in os.scandir(destination):
        if z.is_dir():
            print("Folder : %s" % z)
            temp1 = z.name
            path = "{}\{}".format(destination, temp1)
            tempid = ''
            for a in file_list:
                if a['title'] == temp1:
                    tempid = a['id']

            if tempid == '':
                toCreateFolder(destination, temp1, folderId)
            else:
                mainImplementation(path, tempid)

        else:
            print("File : %s" % z)
            toUploadFile(destination, z.name, fileName, fileMetaData, folderId)
        print('---------------------------------------')


def main():
    print("File Uploading Procedure Initiated: ")
    fileDrive = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    folderId = ''
    for f in fileDrive:
        if f['title'] == 'Sync Folder':
            #             print(f['id'])
            folderId = f['id']

    mainImplementation(dest, folderId)
    print('File Uploading Script Completed')

if __name__ == "__main__":
    main()
