import pandas as pd
import streamlit as st
import plotly.express as px
import plost
from pathlib import Path



#page setup
dashboard_page= st.Page(
    page="dashboard.py",
    title="Dashboard", 
    icon="🏠",
    default=True    
)

mypatients_page= st.Page(
    page="mypatients.py",
    title="My Patients",
    icon="🗂"
)

#navigation setup
pg=st.navigation(pages=[dashboard_page, mypatients_page])

#running navigation
pg.run()

