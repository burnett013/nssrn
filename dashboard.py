import streamlit as st
import pandas as pd
import requests
import altair as alt

# Config
API_URL = "http://localhost:8001"

# UT Tyler Brand Colors
UT_ORANGE = "#BF5700"  # PMS 159
UT_BLUE = "#003F87"    # PMS 294

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
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
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
def get_satisfaction_v2(state=None, breakdown_by_gender=False):
    params = {}
    if state:
        params['state'] = state
    if breakdown_by_gender:
        params['breakdown_by_gender'] = True
    resp = requests.get(f"{API_URL}/satisfaction", params=params)
    return pd.DataFrame(resp.json())

@st.cache_data
def get_telehealth(state=None):
    params = {}
    if state:
        params['state'] = state
    resp = requests.get(f"{API_URL}/telehealth", params=params)
    return pd.DataFrame(resp.json())

@st.cache_data
def get_telehealth_by_nurse_type(state=None):
    params = {}
    if state:
        params['state'] = state
    try:
        resp = requests.get(f"{API_URL}/telehealth/by_nurse_type", params=params)
        if resp.status_code == 200:
            data = resp.json()
            if data:  # Check if data is not empty
                return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch telehealth by nurse type: {e}")
    return pd.DataFrame()  # Return empty DataFrame

@st.cache_data
def get_telehealth_by_gender(state=None):
    params = {}
    if state:
        params['state'] = state
    try:
        resp = requests.get(f"{API_URL}/telehealth/by_gender", params=params)
        if resp.status_code == 200:
            data = resp.json()
            if data:  # Check if data is not empty
                return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch telehealth by gender: {e}")
    return pd.DataFrame()  # Return empty DataFrame

@st.cache_data
def get_satisfaction_by_state():
    try:
        resp = requests.get(f"{API_URL}/satisfaction/by_state")
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch satisfaction by state: {e}")
    return pd.DataFrame()

@st.cache_data
def get_satisfaction_by_rural_urban(state=None):
    params = {}
    if state:
        params['state'] = state
    try:
        resp = requests.get(f"{API_URL}/satisfaction/by_rural_urban", params=params)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch satisfaction by rural/urban: {e}")
    return pd.DataFrame()

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
NURSE_TYPE_MAP = {1.0: "Nurse Practitioner (NP)", 2.0: "Registered Nurse (RN)"}
RURAL_MAP = {1.0: "Rural", 2.0: "Urban"}

EMPSIT_MAP = {
    1.0: "Employment Agency",
    2.0: "Organization/Facility",
    3.0: "Self-Employed"
}

AGE_MAP = {
    1.0: "<=29",
    2.0: "30-34",
    3.0: "35-39",
    4.0: "40-44",
    5.0: "45-49",
    6.0: "50-54",
    7.0: "55-59",
    8.0: "60-64",
    9.0: "65-69",
    10.0: "70-74",
    11.0: ">= 75"
}

EDU_MAP = {
    1.0: "Diploma",
    2.0: "Associate",
    3.0: "Bachelor",
    4.0: "Master/Post-Master",
    5.0: "Doctorate"
}

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
        df_burnout['pct_fmt'] = df_burnout['percentage'].apply(lambda x: f"{x:.1f}%")
        
        chart = alt.Chart(df_burnout).mark_bar().encode(
            x=alt.X('label:O', title='Burnout Level', sort=["Yes", "No"]),
            y=alt.Y('percentage:Q', title='Percentage (%)'),
            color=alt.Color('label:N', legend=alt.Legend(title="Burnout"), scale=alt.Scale(range=[UT_ORANGE, UT_BLUE])),
            tooltip=['label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
        ).properties(title="Burnout Distribution")
        
        st.altair_chart(chart, use_container_width=True)
        st.write("Distribution of Burnout responses (weighted).")
    else:
        st.info("No data available.")

    st.divider()
    
    st.header("Job Satisfaction")
    
    # Toggle for gender breakdown
    show_gender = st.checkbox("Breakdown by Gender", value=False)
    
    df_sat = get_satisfaction_v2(selected_state, breakdown_by_gender=show_gender)
    
    if not df_sat.empty:
        df_sat['label'] = df_sat['category'].map(SATISFACTION_MAP).fillna(df_sat['category'].astype(str))
        df_sat['pct_fmt'] = df_sat['percentage'].apply(lambda x: f"{x:.1f}%")
        site_sort = ["Extremely Satisfied", "Moderately Satisfied", "Moderately Dissatisfied", "Extremely Dissatisfied"]
        
        if show_gender:
            # Map Gender
            df_sat['gender_label'] = df_sat['gender'].map(SEX_MAP).fillna(df_sat['gender'].astype(str))
            
            # Use xOffset for true clustered bar chart
            chart_sat = alt.Chart(df_sat).mark_bar().encode(
                x=alt.X('label:O', title='Satisfaction Level', sort=site_sort),
                xOffset='gender_label:N', # Clusters bars by gender within each X category
                y=alt.Y('percentage:Q', title='Percentage (%)'),
                color=alt.Color('gender_label:N', legend=alt.Legend(title="Gender"), scale=alt.Scale(range=[UT_ORANGE, UT_BLUE])),
                tooltip=['label', 'gender_label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
            ).properties(title="Job Satisfaction by Gender")
            
        else:
            chart_sat = alt.Chart(df_sat).mark_bar().encode(
                x=alt.X('label:O', title='Satisfaction Level', sort=site_sort),
                y=alt.Y('percentage:Q', title='Percentage (%)'),
                color=alt.Color('label:N', legend=alt.Legend(title="Satisfaction"), sort=site_sort, scale=alt.Scale(range=[UT_ORANGE, '#E87722', UT_BLUE, '#005EB8'])),
                tooltip=['label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
            ).properties(title="Job Satisfaction Distribution")
        
        st.altair_chart(chart_sat, use_container_width=True)
    else:
        st.info("No data available.")
    
    st.divider()
    
    # Adaptive Visualization - State Map or Rural/Urban Breakdown
    if selected_state is None:  # "All" states selected
        st.subheader("Satisfaction by State - US Map")
        st.write("Geographic distribution of extreme satisfaction levels across the United States")
        
        df_state_sat = get_satisfaction_by_state()
        
        if not df_state_sat.empty:
            # State abbreviation to FIPS code mapping
            state_fips = {
                'AL': 1, 'AK': 2, 'AZ': 4, 'AR': 5, 'CA': 6, 'CO': 8, 'CT': 9, 'DE': 10, 'FL': 12, 'GA': 13,
                'HI': 15, 'ID': 16, 'IL': 17, 'IN': 18, 'IA': 19, 'KS': 20, 'KY': 21, 'LA': 22, 'ME': 23, 'MD': 24,
                'MA': 25, 'MI': 26, 'MN': 27, 'MS': 28, 'MO': 29, 'MT': 30, 'NE': 31, 'NV': 32, 'NH': 33, 'NJ': 34,
                'NM': 35, 'NY': 36, 'NC': 37, 'ND': 38, 'OH': 39, 'OK': 40, 'OR': 41, 'PA': 42, 'RI': 44, 'SC': 45,
                'SD': 46, 'TN': 47, 'TX': 48, 'UT': 49, 'VT': 50, 'VA': 51, 'WA': 53, 'WV': 54, 'WI': 55, 'WY': 56,
                'DC': 11
            }
            
            # State abbreviation to full name mapping
            state_names = {
                'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 
                'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
                'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 
                'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
                'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 
                'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 
                'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
                'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 
                'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
                'DC': 'District of Columbia'
            }
            
            # Filter out invalid state codes
            df_state_sat = df_state_sat[df_state_sat['state'].isin(state_fips.keys())].copy()
            
            # Filter for Extremely Satisfied (1) and Extremely Dissatisfied (4)
            df_extreme = df_state_sat[df_state_sat['satisfaction_level'].isin([1.0, 4.0])].copy()
            
            # Prepare data for two separate maps
            df_extremely_satisfied = df_extreme[df_extreme['satisfaction_level'] == 1.0][['state', 'percentage']].copy()
            df_extremely_dissatisfied = df_extreme[df_extreme['satisfaction_level'] == 4.0][['state', 'percentage']].copy()
            
            # Add FIPS codes to dataframes
            df_extremely_satisfied['id'] = df_extremely_satisfied['state'].map(state_fips)
            df_extremely_dissatisfied['id'] = df_extremely_dissatisfied['state'].map(state_fips)
            
            # Load US states geography
            us_states = alt.topo_feature('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json', 'states')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Extremely Satisfied**")
                if not df_extremely_satisfied.empty:
                    map_satisfied = alt.Chart(us_states).mark_geoshape(stroke='white', strokeWidth=0.5).encode(
                        color=alt.Color('percentage:Q', 
                                        scale=alt.Scale(scheme='oranges', domain=[0, df_extremely_satisfied['percentage'].max()]),
                                        legend=alt.Legend(title='% Extremely Satisfied', format='.1f')),
                        tooltip=[alt.Tooltip('state:N', title='State'), 
                                 alt.Tooltip('percentage:Q', title='Percentage', format='.1f')]
                    ).transform_lookup(
                        lookup='id',
                        from_=alt.LookupData(df_extremely_satisfied, key='id', fields=['state', 'percentage'])
                    ).project(
                        type='albersUsa'
                    ).properties(
                        width=400,
                        height=300
                    )
                    st.altair_chart(map_satisfied, use_container_width=True)
                else:
                    st.info("No data available")
            
            with col2:
                st.write("**Extremely Dissatisfied**")
                if not df_extremely_dissatisfied.empty:
                    map_dissatisfied = alt.Chart(us_states).mark_geoshape(stroke='white', strokeWidth=0.5).encode(
                        color=alt.Color('percentage:Q', 
                                        scale=alt.Scale(scheme='blues', domain=[0, df_extremely_dissatisfied['percentage'].max()]),
                                        legend=alt.Legend(title='% Extremely Dissatisfied', format='.1f')),
                        tooltip=[alt.Tooltip('state:N', title='State'), 
                                 alt.Tooltip('percentage:Q', title='Percentage', format='.1f')]
                    ).transform_lookup(
                        lookup='id',
                        from_=alt.LookupData(df_extremely_dissatisfied, key='id', fields=['state', 'percentage'])
                    ).project(
                        type='albersUsa'
                    ).properties(
                        width=400,
                        height=300
                    )
                    st.altair_chart(map_dissatisfied, use_container_width=True)
                else:
                    st.info("No data available")
            
            # KPI Cards - Top States
            st.divider()
            kpi_col1, kpi_col2 = st.columns(2)
            
            with kpi_col1:
                if not df_extremely_satisfied.empty:
                    top_satisfied = df_extremely_satisfied.loc[df_extremely_satisfied['percentage'].idxmax()]
                    state_abbr = top_satisfied['state']
                    state_full_name = state_names.get(state_abbr, state_abbr)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {UT_ORANGE}15 0%, {UT_ORANGE}05 100%); 
                                border-left: 4px solid {UT_ORANGE}; 
                                padding: 20px; 
                                border-radius: 8px;
                                margin: 10px 0;">
                        <h4 style="margin: 0; color: {UT_ORANGE};">🏆 Most Satisfied State</h4>
                        <h2 style="margin: 10px 0; color: {UT_ORANGE};">{state_full_name}</h2>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{top_satisfied['percentage']:.1f}% Extremely Satisfied</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with kpi_col2:
                if not df_extremely_dissatisfied.empty:
                    top_dissatisfied = df_extremely_dissatisfied.loc[df_extremely_dissatisfied['percentage'].idxmax()]
                    state_abbr = top_dissatisfied['state']
                    state_full_name = state_names.get(state_abbr, state_abbr)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {UT_BLUE}15 0%, {UT_BLUE}05 100%); 
                                border-left: 4px solid {UT_BLUE}; 
                                padding: 20px; 
                                border-radius: 8px;
                                margin: 10px 0;">
                        <h4 style="margin: 0; color: {UT_BLUE};">⚠️ Most Dissatisfied State</h4>
                        <h2 style="margin: 10px 0; color: {UT_BLUE};">{state_full_name}</h2>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{top_dissatisfied['percentage']:.1f}% Extremely Dissatisfied</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No state-level satisfaction data available.")
    
    else:  # Specific state selected - Show Rural vs Urban breakdown
        st.subheader(f"Satisfaction in {selected_state} - Rural vs Urban")
        st.write(f"Comparing extreme satisfaction levels between rural and urban nurses in {selected_state}")
        
        df_rural_sat = get_satisfaction_by_rural_urban(selected_state)
        
        if not df_rural_sat.empty:
            # Filter for Extremely Satisfied (1) and Extremely Dissatisfied (4)
            df_extreme = df_rural_sat[df_rural_sat['satisfaction_level'].isin([1.0, 4.0])].copy()
            
            # Map area types
            df_extreme['area_label'] = df_extreme['area_type'].map(RURAL_MAP).fillna(df_extreme['area_type'].astype(str))
            df_extreme['satisfaction_label'] = df_extreme['satisfaction_level'].map(SATISFACTION_MAP)
            df_extreme['pct_fmt'] = df_extreme['percentage'].apply(lambda x: f"{x:.1f}%")
            
            # Prepare data for charts
            df_extremely_satisfied = df_extreme[df_extreme['satisfaction_level'] == 1.0].copy()
            df_extremely_dissatisfied = df_extreme[df_extreme['satisfaction_level'] == 4.0].copy()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Extremely Satisfied**")
                if not df_extremely_satisfied.empty:
                    chart = alt.Chart(df_extremely_satisfied).mark_bar().encode(
                        x=alt.X('area_label:O', title='Area Type'),
                        y=alt.Y('percentage:Q', title='Percentage (%)'),
                        color=alt.Color('area_label:N', legend=None, scale=alt.Scale(range=[UT_ORANGE, '#E87722'])),
                        tooltip=['area_label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
                    ).properties(title="Extremely Satisfied by Area", height=300)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No data available")
            
            with col2:
                st.write("**Extremely Dissatisfied**")
                if not df_extremely_dissatisfied.empty:
                    chart = alt.Chart(df_extremely_dissatisfied).mark_bar().encode(
                        x=alt.X('area_label:O', title='Area Type'),
                        y=alt.Y('percentage:Q', title='Percentage (%)'),
                        color=alt.Color('area_label:N', legend=None, scale=alt.Scale(range=[UT_BLUE, '#005EB8'])),
                        tooltip=['area_label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
                    ).properties(title="Extremely Dissatisfied by Area", height=300)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No data available")
            
            # KPI Cards - Rural vs Urban comparison
            st.divider()
            
            # Check how many unique area types we have
            unique_areas_satisfied = df_extremely_satisfied['area_label'].nunique() if not df_extremely_satisfied.empty else 0
            unique_areas_dissatisfied = df_extremely_dissatisfied['area_label'].nunique() if not df_extremely_dissatisfied.empty else 0
            
            kpi_col1, kpi_col2 = st.columns(2)
            
            with kpi_col1:
                if not df_extremely_satisfied.empty and len(df_extremely_satisfied) > 0:
                    top_area = df_extremely_satisfied.loc[df_extremely_satisfied['percentage'].idxmax()]
                    area_name = top_area['area_label']
                    weighted_count = top_area['weighted_count']
                    
                    # Determine title based on data availability
                    if unique_areas_satisfied == 1:
                        title = f"📊 Satisfaction Data - {area_name} Only"
                        subtitle = f"{area_name}"
                    else:
                        title = "🏆 Higher Satisfaction Area"
                        subtitle = f"{area_name}"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {UT_ORANGE}15 0%, {UT_ORANGE}05 100%); 
                                border-left: 4px solid {UT_ORANGE}; 
                                padding: 20px; 
                                border-radius: 8px;
                                margin: 10px 0;">
                        <h4 style="margin: 0; color: {UT_ORANGE};">{title}</h4>
                        <h2 style="margin: 10px 0; color: {UT_ORANGE};">{subtitle}</h2>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{top_area['percentage']:.1f}% Extremely Satisfied</p>
                        <p style="font-size: 14px; margin: 5px 0 0 0; opacity: 0.8;">Based on {weighted_count:,.0f} weighted responses</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No satisfaction data available")
            
            with kpi_col2:
                if not df_extremely_dissatisfied.empty and len(df_extremely_dissatisfied) > 0:
                    top_area = df_extremely_dissatisfied.loc[df_extremely_dissatisfied['percentage'].idxmax()]
                    area_name = top_area['area_label']
                    weighted_count = top_area['weighted_count']
                    
                    # Determine title based on data availability
                    if unique_areas_dissatisfied == 1:
                        title = f"📊 Dissatisfaction Data - {area_name} Only"
                        subtitle = f"{area_name}"
                    else:
                        title = "⚠️ Higher Dissatisfaction Area"
                        subtitle = f"{area_name}"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {UT_BLUE}15 0%, {UT_BLUE}05 100%); 
                                border-left: 4px solid {UT_BLUE}; 
                                padding: 20px; 
                                border-radius: 8px;
                                margin: 10px 0;">
                        <h4 style="margin: 0; color: {UT_BLUE};">{title}</h4>
                        <h2 style="margin: 10px 0; color: {UT_BLUE};">{subtitle}</h2>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{top_area['percentage']:.1f}% Extremely Dissatisfied</p>
                        <p style="font-size: 14px; margin: 5px 0 0 0; opacity: 0.8;">Based on {weighted_count:,.0f} weighted responses</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No dissatisfaction data available")
        else:
            st.info(f"No rural/urban satisfaction data available for {selected_state}.")

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
        elif group_map[grouping] == "PN_EMPSIT":
            df_earn['label'] = df_earn['group_name'].map(EMPSIT_MAP).fillna(df_earn['group_name'].astype(str))
            y_encoding = alt.Y('label:O', sort='-x', title="Work Setting")
            color_encoding = alt.Color('label:N', legend=None)
        elif group_map[grouping] == "AGE_GP_PUF":
            df_earn['label'] = df_earn['group_name'].map(AGE_MAP).fillna(df_earn['group_name'].astype(str))
            # Sort age groups numerically by the code if possible, but map is robust
            # Since keys are floats 1.0, 2.0... we can just use the mapped string. 
            # To keep logical order, we might need to sort by the original group_name
            y_encoding = alt.Y('label:O', sort=alt.EncodingSortField(field="group_name", order="ascending"), title="Age Group")
            color_encoding = alt.Color('label:N', legend=None)
        elif group_map[grouping] == "HIGHEDU_PUF":
            df_earn['label'] = df_earn['group_name'].map(EDU_MAP).fillna(df_earn['group_name'].astype(str))
            y_encoding = alt.Y('label:O', sort=alt.EncodingSortField(field="group_name", order="ascending"), title="Degree")
            color_encoding = alt.Color('label:N', legend=None)
        else:
            y_encoding = alt.Y('group_name:O', sort='-x', title=grouping)
            color_encoding = alt.Color('avg_earnings:Q', scale=alt.Scale(scheme='greens'))

        chart = alt.Chart(df_earn).mark_bar().encode(
            x=alt.X('avg_earnings:Q', title='Average Earnings ($)'),
            y=y_encoding,
            color=alt.value(UT_ORANGE) if 'avg_earnings' not in str(color_encoding) else color_encoding,
            tooltip=['label', alt.Tooltip('avg_earnings', format=',.0f', title='Average Earnings'), alt.Tooltip('population_size', format=',.0f', title='Population Size')]
        ).properties(title=f"Average Earnings by {grouping}")
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available.")

with tab3:
    st.header("Telehealth Adoption")
    df_tel = get_telehealth(selected_state)
    
    if not df_tel.empty:
        df_tel['label'] = df_tel['category'].map(TELEHEALTH_MAP).fillna(df_tel['category'].astype(str))
        df_tel['pct_fmt'] = df_tel['percentage'].apply(lambda x: f"{x:.1f}%")
        
        chart = alt.Chart(df_tel).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="percentage", type="quantitative"),
            color=alt.Color(field="label", type="nominal", legend=alt.Legend(title="Used Telehealth?"), scale=alt.Scale(range=[UT_ORANGE, UT_BLUE])),
            tooltip=['label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
        ).properties(title="Telehealth Usage")
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available.")
    
    st.divider()
    
    # Breakdown by Nurse Type
    st.subheader("Telehealth Users by Nurse Type")
    st.write("Among nurses who use telehealth, breakdown by RN vs NP")
    
    df_nurse_type = get_telehealth_by_nurse_type(selected_state)
    
    if not df_nurse_type.empty:
        df_nurse_type['label'] = df_nurse_type['nurse_type'].map(NURSE_TYPE_MAP).fillna(df_nurse_type['nurse_type'].astype(str))
        df_nurse_type['pct_fmt'] = df_nurse_type['percentage'].apply(lambda x: f"{x:.1f}%")
        
        chart_nurse = alt.Chart(df_nurse_type).mark_bar().encode(
            x=alt.X('label:O', title='Nurse Type'),
            y=alt.Y('percentage:Q', title='Percentage (%)'),
            color=alt.Color('label:N', legend=None, scale=alt.Scale(range=[UT_ORANGE, UT_BLUE])),
            tooltip=['label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
        ).properties(title="Telehealth Users by Nurse Type")
        
        st.altair_chart(chart_nurse, use_container_width=True)
    else:
        st.info("No data available.")
    
    st.divider()
    
    # Breakdown by Gender
    st.subheader("Telehealth Users by Gender")
    st.write("Among nurses who use telehealth, breakdown by gender")
    
    df_gender = get_telehealth_by_gender(selected_state)
    
    if not df_gender.empty:
        df_gender['label'] = df_gender['gender'].map(SEX_MAP).fillna(df_gender['gender'].astype(str))
        df_gender['pct_fmt'] = df_gender['percentage'].apply(lambda x: f"{x:.1f}%")
        
        chart_gender = alt.Chart(df_gender).mark_bar().encode(
            x=alt.X('label:O', title='Gender'),
            y=alt.Y('percentage:Q', title='Percentage (%)'),
            color=alt.Color('label:N', legend=None, scale=alt.Scale(range=[UT_ORANGE, UT_BLUE])),
            tooltip=['label', alt.Tooltip('pct_fmt', title='Percentage'), alt.Tooltip('weighted_count', format=',.0f', title='Weighted Count')]
        ).properties(title="Telehealth Users by Gender")
        
        st.altair_chart(chart_gender, use_container_width=True)
    else:
        st.info("No data available.")

# Footer
st.divider()
from datetime import datetime
import base64
import os

current_year = datetime.now().year
deployment_date = "12-12-2025 14:37"

# Load and encode Texas flag
flag_path = os.path.join(os.path.dirname(__file__), "texas_flag.png")
with open(flag_path, "rb") as f:
    flag_data = base64.b64encode(f.read()).decode()

footer_html = f"""
<div style="text-align: center; color: #666; font-size: 16px; margin-top: 2rem;">
    <p>© {current_year} | Andy Burnett | Made In Texas <img src="data:image/png;base64,{flag_data}" style="height: 16px; vertical-align: middle; margin-left: 4px;"><br>
    <span style="font-size: 14px; opacity: 0.5;">v1.0 | Deployed: {deployment_date}</span></p>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
