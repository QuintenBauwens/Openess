# -*- mode: python ; coding: utf-8 -*-

"""
analysis    :     This is the main part of the script where you assign the main script that causes to run the program
pathex      :     Specifies additional paths for PyInstaller to search for modules, scripts and libraries that are not found in the standar python path.

datas       :     Crucial for including non-python files that are needed for running the program.
                  It takes a list of tupples that contains two elements, where the first element is the path to the resource in your source directory
                  and the second element is the location where the resource should be placed.

                  For example, ('src/gui', 'gui') means that PyInstaller will include all files from your local src/gui directory 
                  and place them in a gui directory within the bundled application.
hiddenimports :   PyInstaller automatically detects most Python imports, but sometimes, especially with dynamic imports or imports done inside functions, it might miss some.
                  The hiddenimports list allows you to explicitly specify additional Python modules that should be included in the bundle.
                  This ensures that all parts of your application are correctly packaged, even if PyInstaller can't automatically detect them.
"""

import os
import pkgutil

# method to dynamically reference all the modules in the 'apps' package
def find_package_modules(package_name):
   package_path = os.path.join('src', package_name.replace(".", os.sep))
   return [f'{package_name}.{name}' for _, name, _ in pkgutil.iter_modules([package_path])]

block_cipher = None

a = Analysis(['src\\main.py'], # type: ignore
            pathex=['C:\\Users\\QBAUWENS\\Documents\\Openess', 'C:\\Users\\QBAUWENS\\Documents\\Openess\\src'],
            binaries=[],
            datas=[
                  ('src/gui', 'gui'),
                  ('src/gui/apps', 'gui/apps'),
                  ('src/utils', 'utils'),
                  ('src/core', 'core'),
                  ('resources', 'resources')
               ],
            hiddenimports= find_package_modules('gui.apps') + [
                  'gui',
                  'gui.main',
                  'core',
                  'core.file',
                  'core.nodes',
                  'utils',
                  'utils.tabUI',
                  'utils.tooltipUI'
               ],
            hookspath=[],
            hooksconfig={},
            runtime_hooks=[],
            excludes=[],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False)

# Remove unused modules
a.binaries = [x for x in a.binaries if not x[0].startswith("scipy")]

pyz = PYZ(a.pure, a.zipped_data, # type: ignore
         cipher=block_cipher)

exe = EXE(pyz, # type: ignore
         a.scripts,
         a.binaries,
         a.zipfiles,
         a.datas,
         [],
         name='TIA_Openness_Demo',
         debug=False,
         bootloader_ignore_signals=False,
         strip=False,
         upx=True,
         upx_exclude=[],
         runtime_tmpdir=None,
         console=True,
         disable_windowed_traceback=False,
         target_arch=None,
         codesign_identity=None,
         entitlements_file=None,
         icon='resources\\img\\tia.ico')
