import PyInstaller.__main__
import os
import shutil

# Remove previous builds safely
try:
    if os.path.exists("build"):
        shutil.rmtree("build", ignore_errors=True)
    if os.path.exists("dist"):
        for item in os.listdir("dist"):
            item_path = os.path.join("dist", item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except Exception:
                pass
except Exception:
    pass

PyInstaller.__main__.run([
    'main.py',
    '--name=AD ASTRA',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
])

print("Construcción completada. Revisa la carpeta 'dist/'.")
