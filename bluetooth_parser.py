#-----------------------------------------------------------------------------
extractionPath = input("Enter full path of extraction (Example: C:\\Users\\...\\extraction.zip): ")
searchMacVendor = input("Enable macvendor api (y/n): ")
if searchMacVendor != "":
    searchMacVendor = searchMacVendor.lower()
    if searchMacVendor == "y":
        searchMacVendor = True
    if searchMacVendor == "n":
        searchMacVendor = False


# Manually enable/disable (True/False) if you want to use Macvendor api for paired devices.
# Requires PHP installed. In some cases it can take some time to process (1 device request per sec.)
# Press enter while inside the prompt to apply this manually
if searchMacVendor == "":
    searchMacVendor = True

# Enter path here if you want to do it manually.
# Example path: C:\\Users\\ADMIN\\Downloads\\extraction.zip
if extractionPath == "":
    extractionPath = "C:\\Users\\ADMIN\\Downloads\\Cellebrite CTF23 Felix iPhone 8 EXTRAHERING.zip"

#-----------------------------------------------------------------------------


import zipfile, biplist, subprocess, time, sys, sqlite3, shutil, os
from datetime import datetime, timezone
sys.set_int_max_str_digits(10000)

def macVendor(mac):
    php_script_path = r"./api/macvendor.php"
    command = ['php', php_script_path, mac]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    time.sleep(1)
    return(output)

def timeConvert():
    time_value = value.get('LastSeenTime')
    last_seen_time = datetime.fromtimestamp(time_value, timezone.utc)
    formatted_last_seen_time = last_seen_time.strftime('%Y-%m-%d %H:%M:%S UTC')
    return(formatted_last_seen_time)


def sqlConnect():
    sqliteConnection = sqlite3.connect(sqliteDatabase)
    sqliteCursor = sqliteConnection.cursor()
    sqliteCursor.execute(sqliteQuery)
    sqliteResult = sqliteCursor.fetchall()
    for column in sqliteCursor.description:
        column_names.append(column[0])
    sqliteConnection.close()
    return(sqliteResult)


openedZipfile = zipfile.ZipFile(extractionPath, "r")

sqlPath1 = []
sqlPath2 = []

for filename in openedZipfile.namelist():
    if "com.apple.MobileBluetooth.devices.plist" in filename:
        print(f'File found at: {filename}\n')
        plistPath = filename
    if "com.apple.MobileBluetooth.ledevices.paired" in filename:
        print(f"File found at: {filename}\n")
        sqlPath1.append(filename)
    if "com.apple.MobileBluetooth.ledevices.other.db" in filename:
        print(f"File found at: {filename}\n")
        sqlPath2.append(filename)

sqlPath1.sort()
sqlPath2.sort()

plist_data = openedZipfile.read(plistPath)
plist = biplist.readPlistFromString(plist_data)

summaryList = []
for key, value in plist.items():
    if 'Name' in value:
        summaryList.append(f'Namn: {plist[key]["Name"]}')
    else:
        summaryList.append("Namn: None")
    summaryList.append(f'\nMAC-ADDRESS: {key}\n')
    if 'LastSeenTime' in value:
        summaryList.append(f"Last disconnected: {timeConvert()}\n")
    if searchMacVendor == True:
        summaryList.append(f'{macVendor(key)}\n')
    summaryList.append("\n")

detailedList = []
for key, value in plist.items():
    detailedList.append(f'{key}\n\n')
    for sub_key, sub_value in value.items():
        if isinstance(sub_value, bytes):
            sub_value = int.from_bytes(sub_value)
        if sub_key == "LastSeenTime":
            detailedList.append(f"{sub_key}: {timeConvert()}\n")
        else:
            detailedList.append(f"{sub_key}: {sub_value}\n")
    detailedList.append("----------------------------------------------------\n\n")

with zipfile.ZipFile(extractionPath, 'r') as localFile:
    for items in sqlPath1:
        localFile.extract(items, ".\\tmp")

tmpFolder = ".\\tmp"
sqliteDatabase = tmpFolder+"\\"+sqlPath1[0]

sqliteQuery = "SELECT Uuid, Name, Address, LastSeenTime, LastConnectionTime  FROM PairedDevices;"

sqliteResult1Formated = []
column_names= []
for item in sqlConnect():
    new_item = (
        f"{column_names[0]}: {item[0]}\n"
        f"{column_names[1]}: {'None' if len(item[1]) < 1 else item[1]}\n"
        f"{column_names[2]}: {item[2]}\n"
        f"{column_names[3]}: {item[3]}\n"
        f"{column_names[4]}: {item[4]}\n"
     )
    sqliteResult1Formated.append(new_item)


with zipfile.ZipFile(extractionPath, 'r') as localFile:
    for items in sqlPath2:
        localFile.extract(items, ".\\tmp")

sqliteDatabase = tmpFolder+"\\"+sqlPath2[0]

sqliteQuery = "SELECT Uuid, Name, Address, LastSeenTime, LastConnectionTime  FROM OtherDevices;"

sqliteResult2Formated = []

column_names.clear()

for item in sqlConnect():
    new_item = (
        f"{column_names[0]}: {item[0]}\n"
        f"{column_names[1]}: {'None' if len(item[1]) < 1 else item[1]}\n"
        f"{column_names[2]}: {item[2]}\n"
        f"{column_names[3]}: {item[3]}\n"
        f"{column_names[4]}: {item[4]}\n"
     )
    sqliteResult2Formated.append(new_item)


from yattag import Doc

doc, tag, text = Doc().tagtext()

doc.asis('<!DOCTYPE html')

with tag('html'):
    with tag('head'):
        with tag('title'):
            text('Bluetooth parser')
    with tag('body'):
        with tag('h2'):
            text("Source:")
            doc._append("<br/>")
            text(extractionPath)
        with tag('h1'):
            text('Summary:')
        with tag('h2'):
            text(f"Paired devices: {len(plist.items())}\n")
            doc._append("<br/>")
            text(f"Paired low devices: {len(sqliteResult1Formated)}\n")
            doc._append("<br/>")
            text(f"Recognized devices: {len(sqliteResult2Formated)}\n")
            doc._append("<br/>""<br/>")
            text(f"Total devices: {len(plist.items())+len(sqliteResult1Formated)+len(sqliteResult2Formated)}")
            doc._append("<br/>""<br/>")
        with tag('h2'):
            text(f"Paired Devices ({len(plist.items())}) :")
        with tag('pre'):
            for item in summaryList:
                text(item)
        with tag('h2'):
            text('Detailed:')
        if len(plistPath) > 1:
            with tag('p'):
                text(plistPath)
        with tag('pre'):
            for item in detailedList:
                text(item)
        with tag('h2'):
            text(f"Paired low devices ({len(sqliteResult1Formated)}) :")
        if len(sqliteResult1Formated) > 1:
            with tag('p'):
                for name in sqlPath1:
                    text(name)
                    doc._append("<br/>")
        with tag('pre'):
            for i, item in enumerate(sqliteResult1Formated):
                text(f"{i+1}.\n")
                text(f"{item}\n")
        with tag('h2'):
            text(f"Recognized devices ({len(sqliteResult2Formated)}) :")
        if len(sqliteResult2Formated) > 1:
            with tag('p'):
                for name in sqlPath2:
                    text(name)
                    doc._append("<br/>")
        with tag('pre'):
            for i, item in enumerate(sqliteResult2Formated):
                text(f"{i+1}.\n")
                text(f"{item}\n")

result = doc.getvalue()

with open('bluetooth_parser.html', 'w') as file:
    file.writelines(result)
    print(f"Detailed HTML file generated successfully at: {os.getcwd()}\\bluetooth_parser.html\n")

input('Press ENTER to exit')

if os.path.isdir(tmpFolder):
    shutil.rmtree(tmpFolder)