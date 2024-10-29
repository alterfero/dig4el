# Digital Inferential Grammar for Endangered Languages
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

DIG4EL is a research prototype software designed to produce grammatical descriptions of endangered languages through automated observations and inferences. 
Observations are derived from Conversational Questionnaires, as well as prior data and probabilities from Grambank and WALS 
from the Max Planck Institute. DIG4EL implements a method that is being developed as part the doctoral research of Sebastien CHRISTIAN 
at the University of French Polynesia, expected to be completed in late 2026. An official public release of the software is anticipated around that time. 
Until then, this software is available primarily for testing and review purposes and will sustain major changes as the method evolves and
feddback is received.

## Academic usage

This software is intended for academic and research purposes. If you use this software in your research, please cite:

```bibtex
@software{CHRISTIAN_software_2024,
  author = {Sebastien CHRISTIAN},
  title = {DIG4EL},
  year = {2024},
  url = {https://github.com/username/repository},
  version = {1.0.0}
}
```

## Status and support

This is a research prototype provided "as is". While we welcome contributions and feedback, please note:

This is not production-ready software
Support is provided on a best-effort basis
For questions about the research, please refer to the publications or contact sebastien.christian@doctorant.upf.pf

## Installation

The current version of DIG4EL is pure Python with the Streamlit library used to build user interface. 
To run it locally, just download the code, create a virtual environment (recommended) with Python 3.9 or above and install all the libraries
from requirements.txt 
```
python -m venv myenv
source myenv/bin/activate  # On Linux/Mac
# or
myenv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

Then execute `streamlit run home.py`
A local browser window will open to run the software locally. 


## License

This program is free software: you can redistribute it and/or modify it under the terms of the 
GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, 
or any later version.

This program is distributed in the hope that it will be useful for academic and research purposes, 
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. 
If not, see <https://www.gnu.org/licenses/>.

This project also includes data from the World Atlas of Language Structures and from Grambank, which must be properly 
cited in any use of this software along with the software itself. You can either copy-paste the citations included 
in the pages of DIG4EL, or check https://wals.info/ and https://grambank.clld.org/ and follow citations instructions.

## Contacts

Sebastien CHRISTIAN: sebastien.christian@doctorant.upf.pf

## Acknowledgment

Many thanks to those who have supported this research effort: Jacques Vernaudon and Alexandre François 
for their invaluable contributions in conceptualization, supervision, review, and editing, as well as for providing resources in Tahitian and Mwotlap. 
I am deeply grateful to Marie Teikitohe for her contributions in Marquesan, Takurua Parent in Rapa, Albert Hugues in Mangareva, 
and Herenui Vanaa and Nati Pita in Paumotu, for sharing resources in their languages. 
I would also like to extend special thanks to Mary Walworth, Nick Thieberger, and Vanessa Raffin for their valuable advice 
and feedback on the features (and bugs) of the software. Lastly, I express my profound gratitude to all community members 
not specifically mentioned here who generously shared their time, knowledge, languages, and insights, making this work possible.