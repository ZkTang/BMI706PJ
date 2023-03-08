import pandas as pd
import numpy as np
import os
import glob
import sidetable
import altair as alt
import lifelines as lf
import streamlit as st

@st.cache_data
def load_data():
    cancer_idx = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_level_dataset_index.csv")
    cancer_nonidx = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_level_dataset_non_index.csv")
    cancer_panel = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_panel_test_level_dataset.csv")
    cancer_imaging = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/imaging_level_dataset.csv")
    cancer_manifest = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/manifest.csv")
    cancer_medonc = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/med_onc_note_level_dataset.csv")
    cancer_path = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/pathology_report_level_dataset.csv")
    cancer_patientlevel = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/patient_level_dataset.csv")
    cancer_drugs = pd.read.csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/regimen_cancer_level_dataset.csv")
    return cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs

cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs = load_data()

# Head
st.write("## Visulization of GENIE BPC NSCLC v2.0-public dataset")
st.write("## http://www.aacr.org/bpc_nsclc")

# Task 1
data_1 = cancer_drugs
df_1 = data_1.dropna(subset = ['tt_pfs_i_g_mos','pfs_i_g_status'])
df_md_1 = data_1.dropna(subset = ['tt_pfs_m_g_mos', 'pfs_m_g_status'])
alt.data_transformers.enable('default', max_rows=10000)

df_melted_1 = pd.melt(
    df_1,
    id_vars=["record_id", "regimen_drugs", 'tt_pfs_m_g_mos', 'tt_pfs_i_g_mos'],
    value_vars=["pfs_m_g_status", "pfs_i_g_status"],
    var_name="progression_type",
    value_name="progression_occurred"
)

df_melted_1["time_till_progression"] = df_melted_1.apply(lambda x: x["tt_pfs_i_g_mos"] if x["progression_type"] == "pfs_i_g_status" else x["tt_pfs_m_g_mos"], axis=1)

df_melted_1.drop(["tt_pfs_i_g_mos", "tt_pfs_m_g_mos"], axis=1, inplace=True)

df_melted_1['progression_type'] = np.where(df_melted_1['progression_type'] == 'pfs_m_g_status', 'Notes Based', 'Imaging Based')
drug_options = sorted(df_melted_1['regimen_drugs'].unique())
selection = alt.selection_single(
    fields=['regimen_drugs'],
    bind=alt.binding_select(options=drug_options,
                            name='Select Drug Regimen'),
     init={'regimen_drugs': 'Docetaxel'}
)
alt.Chart(df_melted_1).mark_bar().encode(
    x = alt.X('progression_occurred:N', axis= None),
    y = alt.Y('count():Q', axis=alt.Axis(grid=True)),
    color = alt.Color('progression_occurred:N', legend=alt.Legend(title='Progression Status')),
    column=alt.Column('progression_type:N')
).configure_view(
    stroke='transparent'
).properties(
    width=50,
    height=300,
    title='Frequency of Progression for each Drug'
).add_selection(selection).transform_filter(selection)




