import json
from os import listdir, mkdir
from os.path import isfile, join

cq_folder = "./questionnaires"
rec_folder = "./recordings"

def get_all_recordings_filenames_for_language(language):
    recordings_filenames = []
    cq_folder_list = [f for f in listdir(rec_folder)]
    if ".DS_Store" in cq_folder_list:
        cq_folder_list.remove(".DS_Store")
    for cq_folder in cq_folder_list:
        languages = [l for l in listdir(join(rec_folder, cq_folder))]
        if ".DS_Store" in languages:
            languages.remove(".DS_Store")
        if language in languages:
            local_recordings = [r for r in listdir(join(rec_folder, cq_folder, language))]
            if ".DS_Store" in local_recordings:
                local_recordings.remove(".DS_Store")
            recordings_filenames.append({"recording_filenames": local_recordings, "cq_folder": cq_folder})
            print(recordings_filenames)
    return recordings_filenames
