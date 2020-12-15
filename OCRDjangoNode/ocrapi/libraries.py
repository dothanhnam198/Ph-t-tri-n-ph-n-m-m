import os
import io

def showFile(file):
    f = open(file, 'rb')
    contents = f.read()
    print(contents)

def copyFile(file):
    os.popen('cp '+file+' '+(os.path.basename(os.path.normpath(file))))