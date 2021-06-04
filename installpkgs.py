import os
packages = []

#check if packages are installed
try:
  import readchar
except:
  packages.append("readchar")

#install packages
if len(packages)>0:
  print("Installing packages...")
  os.system("pip3 install "+" ".join(packages)+" --disable-pip-version-check")