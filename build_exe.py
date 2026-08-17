import PyInstaller.__main__
import os
import shutil

# Remove previous builds
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

PyInstaller.__main__.run([
    'main.py',
    '--name=SynologyFileComparator',
    '--windowed',
    '--noconfirm',
    '--clean',
])

print("Construcción completada. Revisa la carpeta 'dist/'.")
