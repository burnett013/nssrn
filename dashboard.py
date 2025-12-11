import streamlit as st
import pandas as pd
import requests
import altair as alt

# Config
API_URL = "http://localhost:8005"

st.set_page_config(page_title="Nursing Workforce Dashboard", layout="wide")

st.title("Nursing Workforce 2022 Dashboard")
st.markdown("Insights from the 2022 National Sample Survey of Registered Nurses.")

# Data Fetching
@st.cache_data
def get_filter_options():
    try:
        resp = requests.get(f"{API_URL}/filter_options")
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {"states": [], "work_settings": []}

@st.cache_data
def get_burnout(state=None):
    params = {}
    if state:
        params['state'] = state
    resp = requests.get(f"{API_URL}/burnout", params=params)
    return pd.DataFrame(resp.json())

@st.cache_data
def get_earnings(state=None, grouping="PN_EMPSIT"):
    params = {'grouping': grouping}
    if state:
        params['state'] = state
    resp = requests.get(f"{API_URL}/earnings", params=params)
    return pd.DataFrame(resp.json())

@st.cache_data
def get_satisfaction(state=None):
    params = {}
    if state:
        params['state'] = state
    resp = requests.get(f"{API_URL}/satisfaction", params=params)
    return pd.DataFrame(resp.json())

@st.cache_data
def get_telehealth(state=None):
    params = {}
    if state:
        params['state'] = state
    resp = requests.get(f"{API_URL}/telehealth", params=params)
    return pd.DataFrame(resp.json())

# Mappings
BURNOUT_MAP = {1.0: "Yes", 2.0: "No"}
SATISFACTION_MAP = {
    1.0: "Extremely Satisfied", 
    2.0: "Moderately Satisfied", 
    3.0: "Moderately Dissatisfied", 
    4.0: "Extremely Dissatisfied"
}
TELEHEALTH_MAP = {1.0: "Yes", 2.0: "No"}
SEX_MAP = {1.0: "Male", 2.0: "Female"}

# Sidebar
options = get_filter_options()
state_filter = st.sidebar.selectbox("Filter by State", ["All"] + options['states'])
selected_state = None if state_filter == "All" else state_filter

# Layout
tab1, tab2, tab3 = st.tabs(["Burnout & Satisfaction", "Education & Earnings", "Telehealth"])

with tab1:
    st.header("Burnout Levels")
    df_burnout = get_burnout(selected_state)
    
    if not df_burnout.empty:
        # Map labels
        df_burnout['label'] = df_burnout['category'].map(BURNOUT_MAP).fillna(df_burnout['category'].astype(str))
        
        chart = alt.Chart(df_burnout).mark_bar().encode(
            x=alt.X('label:O', title='Burnout Level', sort=["Yes", "No"]),
            y=alt.Y('percentage:Q', title='Percentage (%)'),
            color=alt.Color('label:N', legend=alt.Legend(title="Burnout")),
            tooltip=['label', 'percentage', 'weighted_count']
        ).properties(title="Burnout Distribution")
        
        st.altair_chart(chart, use_container_width=True)
        st.write("Distribution of Burnout responses (weighted).")
    else:
        st.info("No data available.")

    st.divider()
    
    st.header("Job Satisfaction")
    df_sat = get_satisfaction(selected_state)
    
    if not df_sat.empty:
        df_sat['label'] = df_sat['category'].map(SATISFACTION_MAP).fillna(df_sat['category'].astype(str))
        site_sort = ["Extremely Satisfied", "Moderately Satisfied", "Moderately Dissatisfied", "Extremely Dissatisfied"]
        
        chart_sat = alt.Chart(df_sat).mark_bar().encode(
            x=alt.X('label:O', title='Satisfaction Level', sort=site_sort),
            y=alt.Y('percentage:Q', title='Percentage (%)'),
            color=alt.Color('label:N', legend=alt.Legend(title="Satisfaction"), sort=site_sort),
            tooltip=['label', 'percentage', 'weighted_count']
        ).properties(title="Job Satisfaction Distribution")
        
        st.altair_chart(chart_sat, use_container_width=True)
    else:
        st.info("No data available.")

with tab2:
    st.header("Earnings Analysis")
    grouping = st.radio("Group By", ["Work Setting (PN_EMPSIT)", "Age Group (AGE_GP_PUF)", "Degree (HIGHEDU_PUF)", "Gender (SEX)"], horizontal=True)
    
    group_map = {
        "Work Setting (PN_EMPSIT)": "PN_EMPSIT",
        "Age Group (AGE_GP_PUF)": "AGE_GP_PUF", 
        "Degree (HIGHEDU_PUF)": "HIGHEDU_PUF",
        "Gender (SEX)": "SEX"
    }
    
    df_earn = get_earnings(selected_state, group_map[grouping])
    
    if not df_earn.empty:
        # Apply Gender Map if selected
        if group_map[grouping] == "SEX":
            df_earn['label'] = df_earn['group_name'].map(SEX_MAP).fillna(df_earn['group_name'].astype(str))
            y_encoding = alt.Y('label:O', sort='-x', title="Gender")
            color_encoding = alt.Color('label:N', legend=None)
        else:
            y_encoding = alt.Y('group_name:O', sort='-x', title=grouping)
            color_encoding = alt.Color('avg_earnings:Q', scale=alt.Scale(scheme='greens'))

        chart = alt.Chart(df_earn).mark_bar().encode(
            x=alt.X('avg_earnings:Q', title='Average Earnings ($)'),
            y=y_encoding,
            color=color_encoding,
            tooltip=['group_name', 'avg_earnings', 'population_size']
        ).properties(title=f"Average Earnings by {grouping}")
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available.")

with tab3:
    st.header("Telehealth Adoption")
    df_tel = get_telehealth(selected_state)
    
    if not df_tel.empty:
        df_tel['label'] = df_tel['category'].map(TELEHEALTH_MAP).fillna(df_tel['category'].astype(str))
        
        chart = alt.Chart(df_tel).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="percentage", type="quantitative"),
            color=alt.Color(field="label", type="nominal", legend=alt.Legend(title="Used Telehealth?")),
            tooltip=['label', 'percentage', 'weighted_count']
        ).properties(title="Telehealth Usage")
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available.")
