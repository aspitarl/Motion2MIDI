import shutil
import sys
import os
import argparse

from pathdefs import config_folders_path, fp_steamvr_settings, fp_null_driver

parser = argparse.ArgumentParser()
parser.add_argument("new_name", type=str,  help="New config name")

new_name = parser.parse_args().new_name

config_folder = os.path.join(config_folders_path, new_name)

if not os.path.exists(config_folder): os.makedirs(config_folder)

shutil.copy(fp_steamvr_settings, os.path.join(config_folder, 'steamvr.vrsettings'))
shutil.copy(fp_null_driver, os.path.join(config_folder, 'default.vrsettings'))
