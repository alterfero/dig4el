import streamlit as st

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.header("DIG4EL")
st.markdown("### Digital Inferential Grammars for Endangered Languages")

st.markdown("DIG4EL is a work-in-progress software designed to support the computer-assisted creation of grammatical learning material"
            "for endangered languages. The method combines")
st.markdown("- The thoretical framework of Radical Construction Grammar (Croft, 2001).")
st.markdown("- Efficient and engaging field data collection methods with Conversational Questionnaires (François, 2019).")
st.markdown("- Original natural language processing (NLP) algorithms leveraging Abstract Meaning Representations, Bayesian networks and Markov Random Fields.")
st.markdown("- The use of accumulated linguistic knowledge from over 2,500 of the world's languages, thanks to the World Atlas of Language Structures (Dryer & Haspelmath,2013)")
with st.popover("References", use_container_width=True):
    st.markdown("**Radical Construction Grammar**")
    st.markdown("Croft W. (2001). Radical Construction Grammar. Oxford University Press.")
    st.markdown("**World Atlas of Language Structures**")
    st.markdown(
        "Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology.")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")
    st.link_button("Visit WALS", "https://wals.info/")
    st.markdown("**Conversational Questionnaires**")
    st.markdown("François, A.A proposal for conversational questionnaires(2019) In Lahaussois A., Vuillermet M.Methodological Tools for Linguistic Description and Typology, 16, , pp.155-196, 2019, Language Documentation & Conservation Special Publications, 978-0-9973295-5-1. ffhal-02061237f. https://hal.science / hal - 02061237 / document")
    st.link_button("Read the paper online", "https://hal.science/hal-02061237/document")
    st.markdown("**Algorithms and development**")
    st.markdown("DIG4EL is the fruit of the collaboration of Christian Sebastien, PhD student at the University of French Polynesia, "
                "François Alexandre, Research Director at the French National Center for Scientific Research, and Vernaudon Jacques, "
                "senior lecturer of Linguistics at the University of French Polynesia.")
st.markdown("The interface allows to perform operations and access features as they are made available. ")

st.markdown("Contact: sebastien.christian@doctorant.upf.pf")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base Features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

    st.write("**Advanced features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")


# create a list of all available CQs - list all the json files in the CQs folder

# with st.expander("Available Conversational Questionnaires"):
#     # for each CQ, show how may recordings are available
#     for cq in cq_json_list:
#         # determine if there is a folder with the same name as the CQ in ./recordings
#         if cq[:-5] in listdir(recordings_folder):
#             st.write("- Conversational Questionnaire **{}** has recordings:".format(cq[:-5]))
#             available_languages = listdir(recordings_folder + "/" + cq[:-5])
#             if ".DS_Store" in available_languages:
#                 available_languages.remove(".DS_Store")
#             if available_languages is not None:
#                 for language in available_languages:
#                     # determine how many recordings are available for each language
#                     recordings = listdir(join(recordings_folder, cq[:-5], language))
#                     if ".DS_Store" in recordings:
#                         recordings.remove(".DS_Store")
#                     st.write("{} recording(s) in {}".format(len(recordings), language))
#         else:
#             st.write("- {} does not have recordings yet".format(cq[:-5]))
#
# with st.expander("Statistics on concept graph"):
#     n_nodes = len(concepts_kson.keys())
#     n_leaves = len(graphs_utils.get_all_leaves(concepts_kson))
#     st.write("{} nodes, among which {} leaves".format(n_nodes, n_leaves))
#
#
