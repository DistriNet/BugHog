import os

from bci import cli

PROFILE_STORAGE_FOLDER = '/app/browser/profiles'
PROFILE_EXECUTION_FOLDER = '/tmp/profiles'


def prepare_chromium_profile(profile_name: str = None) -> str:
    # Create new execution profile folder
    profile_execution_path = os.path.join(PROFILE_EXECUTION_FOLDER, 'new_profile')
    profile_execution_path = __create_folder(profile_execution_path)

    # Copy profile from storage to execution folder if profile_name is given
    if profile_name:
        if not os.path.exists(os.path.join(PROFILE_STORAGE_FOLDER, 'chromium', profile_name)):
            raise Exception(f'Profile \'{profile_name}\' does not exist')
        profile_storage_path = os.path.join(PROFILE_STORAGE_FOLDER, profile_name, 'Default')
        cli.execute(f'cp -r {profile_storage_path} {profile_execution_path}')
    return profile_execution_path


def prepare_firefox_profile(profile_name: str = None) -> str:
    # Create new execution profile folder
    profile_execution_path = os.path.join(PROFILE_EXECUTION_FOLDER, 'new_profile')
    profile_execution_path = __create_folder(profile_execution_path)

    # Copy profile from storage to execution folder if profile_name is given
    if profile_name is None:
        if not os.path.exists(os.path.join(PROFILE_STORAGE_FOLDER, 'firefox', profile_name)):
            raise Exception(f'Profile \'{profile_name}\' does not exist')
        profile_storage_path = os.path.join(PROFILE_STORAGE_FOLDER, profile_name)
        cli.execute(f'cp -r {profile_storage_path} {profile_execution_path}')
    return profile_execution_path


def remove_profile_execution_folder(profile_path: str):
    assert profile_path.startswith(PROFILE_EXECUTION_FOLDER)
    cli.execute(f'rm -rf {profile_path}')


def __create_folder(folder_path: str) -> str:
    if os.path.exists(folder_path):
        folder_path = __increment_until_original(folder_path)
    os.makedirs(folder_path)
    return folder_path


def __increment_until_original(path: str):
    if not os.path.exists(path):
        return path
    i = 0
    while True:
        new_path = path + str(i)
        if not os.path.exists(new_path):
            return new_path
        i += 1
