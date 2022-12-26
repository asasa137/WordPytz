import os


if "__file__" in vars():
    dirsrc = os.path.dirname(os.path.realpath(__file__))
else:
    dirsrc = os.getcwd()

dirout = f"{dirsrc}/../out"
if not (os.path.isdir(dirout)):
    os.makedirs(dirout)

dircfg = f"{dirsrc}/../cfg"
if not (os.path.isdir(dircfg)):
    os.makedirs(dircfg)
