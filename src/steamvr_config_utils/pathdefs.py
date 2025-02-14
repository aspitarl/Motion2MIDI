
import os

config_folders_path = r'VR Config Shortcuts'
config_folders_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_folders_path)

# steam_base_dir = r'C:\Program Files (x86)\Steam'
steam_base_dir = '/home/lee/.steam/steam'

fp_steamvr_settings = os.path.join(steam_base_dir, 'config', 'steamvr.vrsettings')
fp_null_driver = os.path.join(steam_base_dir, 'steamapps', 'common', 'SteamVR', 'drivers', 'null', 'resources', 'settings', 'default.vrsettings')

# steamvr_settings_out = r'C:\Program Files (x86)\Steam\config\steamvr.vrsettings'
# null_driver_out = r'C:\Program Files (x86)\Steam\steamapps\common\SteamVR\drivers\null\resources\settings\default.vrsettings'