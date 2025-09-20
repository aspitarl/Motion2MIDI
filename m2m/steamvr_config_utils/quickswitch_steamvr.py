# https://github.com/username223/SteamVRNoHeadset
import shutil
import sys
import os
import argparse

from pathdefs import config_folders_path, fp_steamvr_settings, fp_null_driver

choices = [f for f in os.listdir(config_folders_path) if os.path.isdir(os.path.join(config_folders_path,f))]

parser = argparse.ArgumentParser()
parser.add_argument("option", type=str, default='normal', choices=choices, 
    help="Which controller")


option = parser.parse_args().option

print("Switching to option: {}".format(option))

#Run normal_nopower to keep base stations on then switch to no_hmd...not working
# option = 'normal_nopower' #Can't gt to work. Seems have to switch power settins in steamvr and nohmd cannot wake base stations.

config_folder = os.path.join(config_folders_path, option)

shutil.copy(os.path.join(config_folder, 'steamvr.vrsettings'), fp_steamvr_settings)
shutil.copy(os.path.join(config_folder, 'default.vrsettings'), fp_null_driver)