import streamlit as st

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)



with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home2.py", label="Home", icon=":material/home:")

    st.page_link("pages/dashboard.py", label="Dashboard", icon=":material/contract_edit:")

st.markdown("# DIG4EL")
st.markdown("#### Quickly create grammar lessons for endangered languages"
            " by combining ")

colq, colw, cole, colr = st.columns(4)
colq.markdown("#### Conversational Questionnaires translations")
colq.markdown("entered with the built-in interface.")
colw.markdown("#### Descriptive Documents")
colw.markdown("written in a mainstream language")
colw.markdown("as research papers, descriptions, dictionaries...")
cole.markdown("#### Sentences translated from a mainstream language.")
colr.markdown("#### Monolingual texts in your language.")

st.page_link("pages/dashboard.py", label="Click on Dashboard in the sidebar to get started", icon=":material/contract_edit:", use_container_width=True)

st.divider()
st.header("About")
st.markdown("DIG4EL is a research software prototype designed to support the computer-assisted creation of grammatical second-language learning material"
            "for endangered languages.")
st.markdown("The method combines")
st.markdown("- The theoretical framework of **Radical Construction Grammar** (Croft, 2001).")
st.markdown("- An efficient and engaging method for data collection in the field, namely **Conversational Questionnaires** (François, 2019).")
st.markdown("- The use of accumulated linguistic knowledge from over 2,500 of the world's languages, thanks to the **World Atlas of Language Structures** (Dryer & Haspelmath,2013) and **Grambank** (Skirgård et al., 2023)")
st.markdown("- The craft of **teaching the grammar of threatened and endangered languages**  (Vernaudon, 2018).")
st.markdown("- Original natural language processing (NLP) algorithms leveraging **Graph-based Meaning Representations** and **Bayesian networks**. (Christian, 2025)")

with st.popover("References", use_container_width=True):
    st.markdown("**Enhancing grammatical documentation for endangered languages with graph-based meaning representation and Loopy Belief Propagation**")
    st.markdown("Christian S. (2025). Natural Language Processing Journal.")
    st.markdown("[https://doi.org/10.1016/j.nlp.2025.100164](https://doi.org/10.1016/j.nlp.2025.100164)")
    st.markdown("**Radical Construction Grammar**")
    st.markdown("Croft W. 2001. Radical Construction Grammar. Oxford University Press.")
    st.markdown("**World Atlas of Language Structures**")
    st.markdown(
        "Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology.")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")
    st.link_button("Visit WALS", "https://wals.info/")
    st.markdown("**Grambank**")
    st.markdown("""
    Skirgård, Hedvig, Hannah J. Haynie, Harald Hammarström, Damián E. Blasi, Jeremy Collins, Jay Latarche, Jakob Lesage, Tobias Weber, Alena Witzlack-Makarevich, Michael Dunn, Ger Reesink, Ruth Singer, Claire Bowern, Patience Epps, Jane Hill, Outi Vesakoski, Noor Karolin Abbas, Sunny Ananth, Daniel Auer, Nancy A. Bakker, Giulia Barbos, Anina Bolls, Robert D. Borges, Mitchell Browen, Lennart Chevallier, Swintha Danielsen, Sinoël Dohlen, Luise Dorenbusch, Ella Dorn, Marie Duhamel, Farah El Haj Ali, John Elliott, Giada Falcone, Anna-Maria Fehn, Jana Fischer, Yustinus Ghanggo Ate, Hannah Gibson, Hans-Philipp Göbel, Jemima A. Goodall, Victoria Gruner, Andrew Harvey, Rebekah Hayes, Leonard Heer, Roberto E. Herrera Miranda, Nataliia Hübler, Biu H. Huntington-Rainey, Guglielmo Inglese, Jessica K. Ivani, Marilen Johns, Erika Just, Ivan Kapitonov, Eri Kashima, Carolina Kipf, Janina V. Klingenberg, Nikita König, Aikaterina Koti, Richard G. A. Kowalik, Olga Krasnoukhova, Kate Lynn Lindsey, Nora L. M. Lindvall, Mandy Lorenzen, Hannah Lutzenberger, Alexandra Marley, Tânia R. A. Martins, Celia Mata German, Suzanne van der Meer, Jaime Montoya, Michael Müller, Saliha Muradoglu, HunterGatherer, David Nash, Kelsey Neely, Johanna Nickel, Miina Norvik, Bruno Olsson, Cheryl Akinyi Oluoch, David Osgarby, Jesse Peacock, India O.C. Pearey, Naomi Peck, Jana Peter, Stephanie Petit, Sören Pieper, Mariana Poblete, Daniel Prestipino, Linda Raabe, Amna Raja, Janis Reimringer, Sydney C. Rey, Julia Rizaew, Eloisa Ruppert, Kim K. Salmon, Jill Sammet, Rhiannon Schembri, Lars Schlabbach, Frederick W. P. Schmidt, Dineke Schokkin, Jeff Siegel, Amalia Skilton, Hilário de Sousa, Kristin Sverredal, Daniel Valle, Javier Vera, Judith Voß, Daniel Wikalier Smith, Tim Witte, Henry Wu, Stephanie Yam, Jingting Ye 葉婧婷, Maisie Yong, Tessa Yuditha, Roberto Zariquiey, Robert Forkel, Nicholas Evans, Stephen C. Levinson, Martin Haspelmath, Simon J. Greenhill, Quentin D. Atkinson & Russell D. Gray (2023). Grambank v1.0 (v1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7740140
    """)
    st.link_button("Visit Grambank", "https://grambank.clld.org/")
    st.markdown("**Conversational Questionnaires**")
    st.markdown("François, A. 2019. A proposal for conversational questionnaires In Lahaussois A., Vuillermet M.Methodological Tools for Linguistic Description and Typology, 16, , pp.155-196, 2019, Language Documentation & Conservation Special Publications, 978-0-9973295-5-1. ffhal-02061237f. https://hal.science / hal - 02061237 / document")
    st.link_button("Read the paper online", "https://hal.science/hal-02061237/document")
    st.markdown("**Didactic grammars of endangered languages**")
    st.markdown("Vernaudon J. 2013. L’enseignement des langues kanak en Nouvelle-Calédonie. Hermès. n° 65. , [ p.]. 10.4267/2042/51507 or Vernaudon, Jacques. (2018). Les métalangues du tahitien à l'école, https://www.researchgate.net/publication/333261526_Les_metalangues_du_tahitien_a_l'ecole")
    st.markdown("**Algorithms and development**")
    st.markdown("Christian Sebastien, PhD student at the University of French Polynesia.")
    st.markdown("**Acknowledgement**")
    st.markdown("Many thanks to those who are supporting this research effort: Jacques Vernaudon and Alexandre François for their invaluable contributions in conceptualization, supervision, review, and editing, as well as for providing resources in Tahitian and Mwotlap. I am deeply grateful to Marie Teikitohe for her contributions in Marquesan, Takurua Parent in Rapa, Albert Hugues in Mangareva, and Herenui Vanaa and Nati Pita in Paumotu, for sharing resources in their languages. I would also like to extend special thanks to Mary Walworth, Nick Thieberger, and Vanessa Raffin for their valuable advice and feedback on the features (and bugs) of the software. Lastly, I express my profound gratitude to all community members not specifically mentioned here who generously shared their time, knowledge, languages, and insights, making this work possible.")
    st.markdown("""
    **how to Cite:** 
    
    To cite DIG4EL in your research, please use:
    
    CHRISTIAN, S. (2024). DIG4EL (v0.2.0). Zenodo. https://doi.org/10.5281/zenodo.14009843
    """)
st.markdown("For any enquiry, contact sebastien.christian@doctorant.upf.pf")
st.markdown("----------------------------------------------------")
st.markdown("""
DIG4EL prototype 
Version 0.2.0

Copyright © 2024 Sebastien Christian,
Licensed under GNU Affero General Public License v3.0.

If you use this software in your research, please cite:
- Christian S. (2024). DIG4EL (Version 0.2.0) DOI: 10.5281/zenodo.1400983
- WALS, instructions at https://wals.info/
- Grambank, instructions at https://github.com/grambank/grambank/wiki/Citing-grambank

Source code: https://github.com/alterfero/dig4el
""")
st.markdown("------------------------------------------------------")




