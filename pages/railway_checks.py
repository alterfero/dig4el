

import os
import streamlit as st


st.write("CWD: {}".format(os.getcwd()))
st.write("Volume mount: {}".format(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")))
st.write("Listing: {}".format(os.listdir(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"))))
