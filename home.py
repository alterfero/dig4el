import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

components.html("""
<div style="
  width:100%; height:90px;
  display:flex; align-items:center; justify-content:center; gap:12px;
  background:#252729; box-shadow:0 2px 8px rgba(0,0,0,.15);
">
  <span style="color:#EAEAE4; font-size:18px; font-weight:700;">
    New release 1.0.2 rolling out this week! Some UX turbulence expected.
  </span>
</div>
""", height=90)

st.markdown("## Assisted grammatical description of endangered languages")

st.markdown("""*DIG4EL (Digital Inferential Grammar for Endangered Languages) is a research software prototype designed to support the computer-assisted creation of 
            **grammar-learning material for linguists and teachers of endangered languages**. DIG4EL combines multiple 
            sources of information about a given language using **responsible** Artificial Intelligence processes. 
            DIG4EL follows the [FAIR](https://www.go-fair.org/fair-principles/) and 
            [CARE](https://www.gida-global.org/care) principles for data governance and respect of their owners.*""")


with st.popover("Notice", width='stretch'):
    st.markdown(""" 
    *Notice: DIG4EL is currently in the early production stage.*
1) **Public nature of outputs**: DIG4EL outputs may incorporate content from all data created or uploaded 
about a language. The dissemination of these outputs is beyond the control and knowledge of the DIG4EL team. 
The DIG4EL team assumes no responsibility or liability for the use, interpretation, or redistribution of 
these outputs. 
2) **Expert review requirement**: System outputs are provided for expert review and editing. All outputs are 
available in editable formats for this purpose.
3) **Limitation of liability**: The DIG4EL team disclaims any responsibility for the use, modification, 
or distribution of system outputs by third parties.
4) **Access to resource-intensive features**: Certain computationally intensive features are restricted. 
Researchers working on the description or teaching of endangered languages may request access by contacting 
the DIG4EL team.
    """)

with st.popover("Guests, Members and Caretakers", width='stretch'):
    st.markdown("""
    - You can explore DIG4EL without logging in, as a **Guest**. Guests have access only to a restricted 
    set of languages and cannot upload or augment data. However, they can generate content within 
    the restricted collection.
    - **Members** can log in to access additional features. **If you are working on a language or teaching it**, 
    contact us to become a Member!
    - Each language has designated **Caretakers**. Caretakers are Members with full upload 
    and augmentation rights for one or more languages. They can add, remove, and edit all the information 
    DIG4EL holds about the languages they manage. Contact us if you would like to become a Caretaker!
    """)

with st.popover("Getting started", width='stretch'):
    st.subheader("Getting started")
    get1, get2 = st.columns(2)
    with get1:
        st.markdown("8-minute overview video")
        st.video("https://youtu.be/K0J48jiflwE")
    with get2:
        st.markdown("""Click on **Dashboard** on the left menu to create and upload information about a language 
        or click on **Generate Grammar** to use available data to generate grammatical descriptions."
                    """)

with st.popover("References", width='stretch'):

    st.markdown("**Acknowledgement**")
    st.markdown("We want to express here our profound gratitude to all community members from all over the world who generously shared their time, knowledge, languages, and insights, to make this work possible. ")

    st.divider()

    st.markdown("""
    **How to Cite DIG4EL:** 

    To cite DIG4EL in your research, please reference the software and the original paper:
    - Software: 
    CHRISTIAN, S. (2025). DIG4EL (v1.0.1). Zenodo. https://doi.org/10.5281/zenodo.16944459
    - Paper:
    Sebastien Christian,
    Enhancing grammatical documentation for endangered languages with graph-based meaning representation and Loopy Belief Propagation,
    Natural Language Processing Journal,
    Volume 12,
    2025,
    100164,
    ISSN 2949-7191,
    https://doi.org/10.1016/j.nlp.2025.100164.
    (https://www.sciencedirect.com/science/article/pii/S2949719125000408)

    """)

    st.divider()

    st.markdown("**World Atlas of Language Structures**")
    st.markdown(
        "Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology.")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")

    st.divider()

    st.markdown("**Grambank**")
    st.markdown("""
    Skirgård, Hedvig, Hannah J. Haynie, Harald Hammarström, Damián E. Blasi, Jeremy Collins, Jay Latarche, Jakob Lesage, Tobias Weber, Alena Witzlack-Makarevich, Michael Dunn, Ger Reesink, Ruth Singer, Claire Bowern, Patience Epps, Jane Hill, Outi Vesakoski, Noor Karolin Abbas, Sunny Ananth, Daniel Auer, Nancy A. Bakker, Giulia Barbos, Anina Bolls, Robert D. Borges, Mitchell Browen, Lennart Chevallier, Swintha Danielsen, Sinoël Dohlen, Luise Dorenbusch, Ella Dorn, Marie Duhamel, Farah El Haj Ali, John Elliott, Giada Falcone, Anna-Maria Fehn, Jana Fischer, Yustinus Ghanggo Ate, Hannah Gibson, Hans-Philipp Göbel, Jemima A. Goodall, Victoria Gruner, Andrew Harvey, Rebekah Hayes, Leonard Heer, Roberto E. Herrera Miranda, Nataliia Hübler, Biu H. Huntington-Rainey, Guglielmo Inglese, Jessica K. Ivani, Marilen Johns, Erika Just, Ivan Kapitonov, Eri Kashima, Carolina Kipf, Janina V. Klingenberg, Nikita König, Aikaterina Koti, Richard G. A. Kowalik, Olga Krasnoukhova, Kate Lynn Lindsey, Nora L. M. Lindvall, Mandy Lorenzen, Hannah Lutzenberger, Alexandra Marley, Tânia R. A. Martins, Celia Mata German, Suzanne van der Meer, Jaime Montoya, Michael Müller, Saliha Muradoglu, HunterGatherer, David Nash, Kelsey Neely, Johanna Nickel, Miina Norvik, Bruno Olsson, Cheryl Akinyi Oluoch, David Osgarby, Jesse Peacock, India O.C. Pearey, Naomi Peck, Jana Peter, Stephanie Petit, Sören Pieper, Mariana Poblete, Daniel Prestipino, Linda Raabe, Amna Raja, Janis Reimringer, Sydney C. Rey, Julia Rizaew, Eloisa Ruppert, Kim K. Salmon, Jill Sammet, Rhiannon Schembri, Lars Schlabbach, Frederick W. P. Schmidt, Dineke Schokkin, Jeff Siegel, Amalia Skilton, Hilário de Sousa, Kristin Sverredal, Daniel Valle, Javier Vera, Judith Voß, Daniel Wikalier Smith, Tim Witte, Henry Wu, Stephanie Yam, Jingting Ye 葉婧婷, Maisie Yong, Tessa Yuditha, Roberto Zariquiey, Robert Forkel, Nicholas Evans, Stephen C. Levinson, Martin Haspelmath, Simon J. Greenhill, Quentin D. Atkinson & Russell D. Gray (2023). Grambank v1.0 (v1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7740140
    """)

    st.divider()

    st.markdown("**Conversational Questionnaires**")
    st.markdown("François, A. 2019. A proposal for conversational questionnaires In Lahaussois A., Vuillermet M.Methodological Tools for Linguistic Description and Typology, 16, , pp.155-196, 2019, Language Documentation & Conservation Special Publications, 978-0-9973295-5-1. ffhal-02061237f. https://hal.science/hal-02061237/document")
    st.link_button("Read the paper online", "https://hal.science/hal-02061237/document")

    st.divider()

    st.markdown("**Didactic grammars of endangered languages**")
    st.markdown("Vernaudon J. 2013. L’enseignement des langues kanak en Nouvelle-Calédonie. Hermès. n° 65. , [ p.]. 10.4267/2042/51507 or Vernaudon, Jacques. (2018). Les métalangues du tahitien à l'école, https://www.researchgate.net/publication/333261526_Les_metalangues_du_tahitien_a_l'ecole")

st.markdown("For any enquiry, contact sebastien.christian@upf.pf")
st.markdown("----------------------------------------------------")
st.markdown("""
DIG4EL prototype 
Version 1.0.3

Copyright © 2025 Sebastien Christian,
Licensed under GNU Affero General Public License v3.0.

If you use this software in your research, please cite:
- Christian S. (2025). DIG4EL (Version 1.0.1) DOI: 10.5281/zenodo.16944459
- WALS, instructions at https://wals.info/
- Grambank, instructions at https://github.com/grambank/grambank/wiki/Citing-grambank

Source code: https://github.com/alterfero/dig4el
""")
st.divider()

st.markdown("""DIG4EL is a research effort supported by the [CNRS](https://www.cnrs.fr/en) as part 
of the [Heliceo](https://www.cnrs.fr/en/ri2-project/heliceo) project, 
managed by the [Maison des Sciences de l'Homme du Pacifique](https://recherche.upf.pf/en/laboratoire/maison-des-sciences-de-lhomme-du-pacifique/)
 in the [University of French Polynesia](https://www.upf.pf/en).
""")

st.image("./pics/logos.png")



with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Source dashboard", icon=":material/search:")
    st.sidebar.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")
    st.page_link("pages/DIG4EL_processes_menu.py", label="Processes", icon=":material/manufacturing:")



