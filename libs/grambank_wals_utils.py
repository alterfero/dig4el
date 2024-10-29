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

from libs import utils as u, wals_utils as wu, grambank_utils as gu
import pandas as pd, json

# GLOBAL VARIBALES
try:
    prefix = "./"
    grambank_given_wals_cpt = pd.read_json(prefix + "external_data/grambank_given_wals_cpt.json")
    grambank_given_wals_cpt.index = grambank_given_wals_cpt.index.astype(str)
    grambank_given_wals_cpt.columns = grambank_given_wals_cpt.columns.astype(str)
    wals_given_grambank_cpt = pd.read_json(prefix + "external_data/wals_given_grambank_cpt.json")
    wals_given_grambank_cpt.index = wals_given_grambank_cpt.index.astype(str)
    wals_given_grambank_cpt.columns = wals_given_grambank_cpt.columns.astype(str)
except FileNotFoundError:
    prefix = "../"
    grambank_given_wals_cpt = pd.read_json(prefix + "external_data/grambank_given_wals_cpt.json")
    grambank_given_wals_cpt.index = grambank_given_wals_cpt.index.astype(str)
    grambank_given_wals_cpt.columns = grambank_given_wals_cpt.columns.astype(str)
    wals_given_grambank_cpt = pd.read_json(prefix + "external_data/wals_given_grambank_cpt.json")
    wals_given_grambank_cpt.index = wals_given_grambank_cpt.index.astype(str)
    wals_given_grambank_cpt.columns = wals_given_grambank_cpt.columns.astype(str)

# FUNCTIONS

def compute_grambank_given_wals_cp(pid, ppk):
    # pid given ppk
    # pid rows, ppk columns

    if ppk in wu.parameter_name_by_pk and pid in gu.grambank_param_value_dict:

        ppk_list = wu.domain_elements_pk_by_parameter_pk[ppk]
        pid_list = list(gu.grambank_param_value_dict[pid]["pvalues"].keys())

        # Grambank GIVEN WALS DF
        # keep only ppk_list on lines (primary)
        filtered_cpt_p2_given_p1 = grambank_given_wals_cpt.loc[pid_list]
        # keep only pid_list on columns (secondary)
        filtered_cpt_p2_given_p1 = filtered_cpt_p2_given_p1[ppk_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p2_given_p1_normalized = filtered_cpt_p2_given_p1.apply(u.normalize_column, axis=0)

        if filtered_cpt_p2_given_p1.max().max() != 0:
            return filtered_cpt_p2_given_p1_normalized
        else:
            return None
    else:
        # not grambank pids
        return None

def compute_wals_given_grambank_cp(ppk, pid):

    if ppk in wu.parameter_name_by_pk and pid in gu.grambank_param_value_dict:

        ppk_list = list(wu.domain_elements_pk_by_parameter_pk[ppk])
        pid_list = list(gu.grambank_param_value_dict[pid]["pvalues"].keys())

        # WALS GIVEN Grambank DF
        # keep only p1 on lines (primary)
        filtered_cpt_p2_given_p1 = wals_given_grambank_cpt.loc[ppk_list]
        # keep only p2 on columns (secondary)
        filtered_cpt_p2_given_p1 = filtered_cpt_p2_given_p1[pid_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p2_given_p1_normalized = filtered_cpt_p2_given_p1.apply(u.normalize_column, axis=0)
        if filtered_cpt_p2_given_p1.max().max() != 0:
            return filtered_cpt_p2_given_p1_normalized
        else:
            return None
    else:
        # not grambank pids
        return None

def get_pvalue_name_from_value_code(code):
    if code[:2] == "GB":
        return gu.grambank_vname_by_vid[code]
    else:
        return wu.get_careful_name_of_de_pk(code)

def build_wals_given_grambank_cpt_df():
    wals_cpt = wu.cpt
    grambank_cpt = gu.cpt
    wals_given_grambank_cpt = pd.DataFrame(float(0), index=wals_cpt.index, columns=grambank_cpt.columns)
    wals_given_grambank_cpt.to_json("../external_data/wals_given_grambank_cpt.json")
def build_grambank_given_wals_cpt_df():
    wals_cpt = wu.cpt
    grambank_cpt = gu.cpt
    grambank_given_wals_cpt = pd.DataFrame(float(0), index=grambank_cpt.index, columns=wals_cpt.columns)
    grambank_given_wals_cpt.to_json("../external_data/grambank_given_wals_cpt.json")