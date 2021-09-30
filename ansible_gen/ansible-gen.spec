# -*- mode: python -*-
block_cipher = None

# <<< START ADDED PART
import os
from PyInstaller.utils.hooks import get_package_paths, remove_prefix, PY_IGNORE_EXTENSIONS
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE, TOC

FILE_TYPE = ['.py','.html']

def collect_pkg_data(package, include_py_files=False, subdir=None):
    # Accept only strings as packages.
    if type(package) is not str:
        raise ValueError
    pkg_base, pkg_dir = get_package_paths(package)
    # Walk through all file in the given package, looking for data files.
    data_toc = TOC()
    for dir_path, dir_names, files in os.walk(pkg_dir):
                for f in files:
                    extension = os.path.splitext(f)[1]
                    if extension in FILE_TYPE:
                        source_file = os.path.join(dir_path, f)
                        dest_folder = remove_prefix(dir_path, os.path.dirname(pkg_base) + os.sep)
                        dest_file = os.path.join(dest_folder, f)
                        data_toc.append((dest_file, source_file, 'DATA'))

    return data_toc

pkg_data = collect_pkg_data('ansible_gen')
# <<< END ADDED PART 

a = Analysis(['ansible-gen.py'],
             pathex=[str(get_package_paths('ansible_gen')[0])],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
		  pkg_data,
          name='ansible-gen',
          debug=False,
          strip=False,
          upx=True,
          console=True )