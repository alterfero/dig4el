# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
