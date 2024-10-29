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

import streamlit as st
import pandas as pd
from libs import grambank_utils as gu, grambank_wals_utils as gwu, wals_utils as wu
if "current_wals_param_name" not in st.session_state:
    st.session_state["current_wals_param_name"] = "Order of Subject, Object and Verb"
if "current_gb_param_name" not in st.session_state:
    st.session_state["current_gb_param_name"] = "Are there definite or specific articles?"
if "wals_given_gb_df" not in st.session_state:
    st.session_state["wals_given_gb_df"] = pd.read_json("./external_data/wals_given_grambank_cpt.json")
    st.session_state["wals_given_gb_df"].index = st.session_state["wals_given_gb_df"].index.astype(str)
    st.session_state["wals_given_gb_df"].columns = st.session_state["wals_given_gb_df"].columns.astype(str)
if "gb_given_wals_df" not in st.session_state:
    st.session_state["gb_given_wals_df"] = pd.read_json("./external_data/grambank_given_wals_cpt.json")
    st.session_state["gb_given_wals_df"].index = st.session_state["gb_given_wals_df"].index.astype(str)
    st.session_state["gb_given_wals_df"].columns = st.session_state["gb_given_wals_df"].columns.astype(str)

def normalize_columns(df):
    for col in df.columns:
        col_sum = df[col].sum()
        if col_sum != 0:
            df[col] = df[col] / col_sum
    return df

st.subheader("Edit wals-grambank cross CP")

colw, colg = st.columns(2)
wals_param_name = colw.selectbox("wals param", wu.parameter_pk_by_name_filtered.keys())
if wals_param_name != st.session_state["current_wals_param_name"]:
    st.session_state["current_wals_param_name"] = wals_param_name
current_wals_param_pk = wu.parameter_pk_by_name[st.session_state["current_wals_param_name"]]
wals_de_name = colw.selectbox("wals param value", [wu.domain_element_by_pk[depk]["name"] for depk in wu.domain_elements_pk_by_parameter_pk[current_wals_param_pk]])
wals_depk = next((depk for depk in wu.domain_elements_pk_by_parameter_pk[current_wals_param_pk] if wu.domain_element_by_pk[depk]["name"] == wals_de_name), None)
colw.write("param code {}, value code {}".format(current_wals_param_pk, wals_depk))

gb_param_name = colg.selectbox("grambank param", [gu.grambank_param_value_dict[pid]["pname"] for pid in gu.grambank_param_value_dict.keys()])
if gb_param_name != st.session_state["current_gb_param_name"]:
    st.session_state["current_gb_param_name"] = gb_param_name
current_gb_pid = gu.grambank_pid_by_pname[st.session_state["current_gb_param_name"]]
gb_vname = colg.selectbox("Grambank param value", [gu.grambank_param_value_dict[current_gb_pid]["pvalues"][vid]["vname"]
                                                   for vid in gu.grambank_param_value_dict[current_gb_pid]["pvalues"]])
gb_vid = next((vid for vid in gu.grambank_param_value_dict[current_gb_pid]["pvalues"].keys()
               if gu.grambank_param_value_dict[current_gb_pid]["pvalues"][vid]["vname"] == gb_vname),None)
colg.write("param code {}, value code {}".format(current_gb_pid, gb_vid))

st.markdown("----------------------------")
col1, col2, col3 = st.columns(3)
col1.write(wals_param_name)
col2.write("given")
col3.write(gb_param_name)

fdf1 = st.session_state["wals_given_gb_df"].loc[wu.domain_elements_pk_by_parameter_pk[current_wals_param_pk]]
ffdf1 = fdf1[list(gu.grambank_param_value_dict[current_gb_pid]["pvalues"].keys())]
st.dataframe(ffdf1, use_container_width=True)
st.write("**{}** GIVEN **{}**".format(wals_de_name, gb_vname))
cole, colr = st.columns(2)
cole.metric("Current value", st.session_state["wals_given_gb_df"].at[wals_depk, gb_vid])
new_wgb_cp = colr.slider("Edit gb|w value", min_value=0.0,max_value=1.0,step=0.1,value=float(st.session_state["wals_given_gb_df"].at[wals_depk, gb_vid]))

st.markdown("-----------------------------")
col4, col5, col6 = st.columns(3)
col4.write(gb_param_name)
col5.write("given")
col6.write(wals_param_name)

# p1 given p2
# filter p1 rows
fdf2 = st.session_state["gb_given_wals_df"].loc[list(gu.grambank_param_value_dict[current_gb_pid]["pvalues"].keys())]
# filter p2 columns
ffdf2 = fdf2[wu.domain_elements_pk_by_parameter_pk[current_wals_param_pk]]

st.dataframe(ffdf2, use_container_width=True)
st.write("**{}** GIVEN **{}**".format(gb_vname, wals_de_name))
colq, colw = st.columns(2)
colq.metric("Current value", st.session_state["gb_given_wals_df"].at[gb_vid, wals_depk])
new_gbw_cp = colw.slider("Edit w|gb value", min_value=0.0,max_value=1.0,step=0.1,value=float(st.session_state["gb_given_wals_df"].at[gb_vid, wals_depk]))

if st.button("submit"):
    st.session_state["wals_given_gb_df"].at[wals_depk, gb_vid] = new_wgb_cp
    st.session_state["gb_given_wals_df"].at[gb_vid, wals_depk] = new_gbw_cp
    st.rerun()

if st.button("save"):
    normalized_wals_given_gb_df = normalize_columns(st.session_state["wals_given_gb_df"])
    normalized_wals_given_gb_df.to_json("./external_data/wals_given_grambank_cpt.json")
    normalized_gb_given_wals_df = normalize_columns(st.session_state["gb_given_wals_df"])
    normalized_gb_given_wals_df.to_json("./external_data/grambank_given_wals_cpt.json")
    st.write("CP files updated")


