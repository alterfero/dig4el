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
from libs import utils as u, grambank_utils as gu
import os
import json
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Transcriptions_explorer.py", label="Explore transcriptions", icon=":material/search:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

def create_difference_dataframe(languages, use_value=False, all_different=False):
    """
    Creates a DataFrame that presents differences between languages.
    Retains only the parameters that are identical across the languages but with different values.

    Parameters:
    - languages: list of tuples (language_name, lang_dict)
    - use_value: if True, use 'value' instead of 'vid' in the DataFrame

    Returns:
    - A pandas DataFrame showing differing parameters across languages.
    """
    # Collect the set of parameter IDs in each language
    parameter_ids_per_language = [set(lang_dict.keys()) for (lang_name, lang_dict) in languages]

    # Find the set of parameter IDs common to all languages
    common_parameter_ids = set.intersection(*parameter_ids_per_language)

    # For each common parameter ID, check if the 'vid's differ across languages
    differing_parameters = []
    for pid in common_parameter_ids:
        vids = [lang_dict[pid]['vid'] for (lang_name, lang_dict) in languages]
        if all_different and len(set(vids)) == len(vids):
            differing_parameters.append(pid)
        elif len(set(vids)) > 1:
            differing_parameters.append(pid)


    # Build the DataFrame
    data = {}
    for (lang_name, lang_dict) in languages:
        data[lang_name] = {}
        for pid in differing_parameters:
            param_name = lang_dict[pid]['parameter']
            data[lang_name][param_name] = gu.grambank_vname_by_vid.get(lang_dict[pid]['value'], "")

    df = pd.DataFrame(data)
    return df


st.header("Exploration of Grambank data")
with st.popover("Credits"):
    st.markdown(
        """
        #### Paper
        Skirgård, Hedvig, Hannah J. Haynie, Damián E. Blasi, Harald Hammarström, Jeremy Collins, Jay J. Latarche, Jakob Lesage, Tobias Weber, Alena Witzlack-Makarevich, Sam Passmore, Angela Chira, Luke Maurits, Russell Dinnage, Michael Dunn, Ger Reesink, Ruth Singer, Claire Bowern, Patience Epps, Jane Hill, Outi Vesakoski, Martine Robbeets, Noor Karolin Abbas, Daniel Auer, Nancy A. Bakker, Giulia Barbos, Robert D. Borges, Swintha Danielsen, Luise Dorenbusch, Ella Dorn, John Elliott, Giada Falcone, Jana Fischer, Yustinus Ghanggo Ate, Hannah Gibson, Hans-Philipp Göbel, Jemima A. Goodall, Victoria Gruner, Andrew Harvey, Rebekah Hayes, Leonard Heer, Roberto E. Herrera Miranda, Nataliia Hübler, Biu Huntington-Rainey, Jessica K. Ivani, Marilen Johns, Erika Just, Eri Kashima, Carolina Kipf, Janina V. Klingenberg, Nikita König, Aikaterina Koti, Richard G. A. Kowalik, Olga Krasnoukhova, Nora L.M. Lindvall, Mandy Lorenzen, Hannah Lutzenberger, Tônia R.A. Martins, Celia Mata German, Suzanne van der Meer, Jaime Montoya Samamé, Michael Müller, Saliha Muradoglu, Kelsey Neely, Johanna Nickel, Miina Norvik, Cheryl Akinyi Oluoch, Jesse Peacock, India O.C. Pearey, Naomi Peck, Stephanie Petit, Sören Pieper, Mariana Poblete, Daniel Prestipino, Linda Raabe, Amna Raja, Janis Reimringer, Sydney C. Rey, Julia Rizaew, Eloisa Ruppert, Kim K. Salmon, Jill Sammet, Rhiannon Schembri, Lars Schlabbach, Frederick W.P. Schmidt, Amalia Skilton, Wikaliler Daniel Smith, Hilário de Sousa, Kristin Sverredal, Daniel Valle, Javier Vera, Judith Voß, Tim Witte, Henry Wu, Stephanie Yam, Jingting Ye 葉婧婷, Maisie Yong, Tessa Yuditha, Roberto Zariquiey, Robert Forkel, Nicholas Evans, Stephen C. Levinson, Martin Haspelmath, Simon J. Greenhill, Quentin D. Atkinson & Russell D. Gray (2023) Grambank reveals global patterns in the structural diversity of the world’s languages. Science Advances 9. doi:10.1126/sciadv.adg6
        
        #### Dataset
        Skirgård, Hedvig, Hannah J. Haynie, Harald Hammarström, Damián E. Blasi, Jeremy Collins, Jay Latarche, Jakob Lesage, Tobias Weber, Alena Witzlack-Makarevich, Michael Dunn, Ger Reesink, Ruth Singer, Claire Bowern, Patience Epps, Jane Hill, Outi Vesakoski, Noor Karolin Abbas, Sunny Ananth, Daniel Auer, Nancy A. Bakker, Giulia Barbos, Anina Bolls, Robert D. Borges, Mitchell Browen, Lennart Chevallier, Swintha Danielsen, Sinoël Dohlen, Luise Dorenbusch, Ella Dorn, Marie Duhamel, Farah El Haj Ali, John Elliott, Giada Falcone, Anna-Maria Fehn, Jana Fischer, Yustinus Ghanggo Ate, Hannah Gibson, Hans-Philipp Göbel, Jemima A. Goodall, Victoria Gruner, Andrew Harvey, Rebekah Hayes, Leonard Heer, Roberto E. Herrera Miranda, Nataliia Hübler, Biu H. Huntington-Rainey, Guglielmo Inglese, Jessica K. Ivani, Marilen Johns, Erika Just, Ivan Kapitonov, Eri Kashima, Carolina Kipf, Janina V. Klingenberg, Nikita König, Aikaterina Koti, Richard G. A. Kowalik, Olga Krasnoukhova, Kate Lynn Lindsey, Nora L. M. Lindvall, Mandy Lorenzen, Hannah Lutzenberger, Alexandra Marley, Tânia R. A. Martins, Celia Mata German, Suzanne van der Meer, Jaime Montoya, Michael Müller, Saliha Muradoglu, HunterGatherer, David Nash, Kelsey Neely, Johanna Nickel, Miina Norvik, Bruno Olsson, Cheryl Akinyi Oluoch, David Osgarby, Jesse Peacock, India O.C. Pearey, Naomi Peck, Jana Peter, Stephanie Petit, Sören Pieper, Mariana Poblete, Daniel Prestipino, Linda Raabe, Amna Raja, Janis Reimringer, Sydney C. Rey, Julia Rizaew, Eloisa Ruppert, Kim K. Salmon, Jill Sammet, Rhiannon Schembri, Lars Schlabbach, Frederick W. P. Schmidt, Dineke Schokkin, Jeff Siegel, Amalia Skilton, Hilário de Sousa, Kristin Sverredal, Daniel Valle, Javier Vera, Judith Voß, Daniel Wikalier Smith, Tim Witte, Henry Wu, Stephanie Yam, Jingting Ye 葉婧婷, Maisie Yong, Tessa Yuditha, Roberto Zariquiey, Robert Forkel, Nicholas Evans, Stephen C. Levinson, Martin Haspelmath, Simon J. Greenhill, Quentin D. Atkinson & Russell D. Gray (2023). Grambank v1.0 (v1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7740140
        """
    )

with st.expander("Language monography"):
    with st.popover("i"):
        st.markdown("Select a language to see information available about it in Grambank.")
    selected_language_name = st.selectbox("select a language", list(gu.grambank_language_by_lid[lid]["name"] for lid in gu.grambank_language_by_lid.keys()))
    selected_language_id = next((lid for lid in gu.grambank_language_by_lid if gu.grambank_language_by_lid[lid]["name"] == selected_language_name), None)
    language_info = gu.grambank_language_by_lid.get(selected_language_id, None)
    if language_info:
        st.write("Macro area: {}".format(language_info["macroarea"]))
        st.write("Family: {}".format(language_info["family"]))
        st.write("Glottocode: {}".format(language_info["glottocode"]))

    # retrieving language_pk
    result_dict = gu.get_grambank_language_data_by_id_or_name(selected_language_id)
    st.write("{} parameters with a value for {}.".format(len(result_dict), selected_language_name))
    display_dict = {}
    for pid, info in result_dict.items():
        display_dict[info["parameter"]] = gu.grambank_param_value_dict[pid]["pvalues"][info["value"]]["vname"]
    result_df = pd.DataFrame(display_dict, index=["value"]).T
    st.dataframe(result_df)

with st.expander("Language Diff"):
    with st.popover("i"):
        st.markdown("See differences between two languages")
    selected_languages = st.multiselect("select languages to compare", list(gu.grambank_language_by_lid[lid]["name"] for lid in gu.grambank_language_by_lid.keys()))
    language_and_data_list = []
    if len(selected_languages) > 1:
        for language in selected_languages:
            result_dict = gu.get_grambank_language_data_by_id_or_name(language_id=None, language_name=language)
            language_and_data_list.append((language, result_dict))
        ddf = create_difference_dataframe(language_and_data_list)
        st.write(ddf)

with st.expander("Browse Grambank parameters and values"):
    pname_list = list(gu.grambank_pid_by_pname)
    selected_pname = st.selectbox("Choose a parameter", pname_list)
    if selected_pname != "":
        vname_count = []
        vids = list(gu.grambank_param_value_dict[gu.grambank_pid_by_pname[selected_pname]]["pvalues"].keys())
        for vid in vids:
            vname_count.append({"value": gu.grambank_vname_by_vid[vid], "count": len(gu.grambank_language_id_by_vid[vid])})
        vname_count_df = pd.DataFrame(vname_count)
        st.dataframe(vname_count_df)