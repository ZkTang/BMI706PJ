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
    cancer_idx = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_level_dataset_index.csv")
    cancer_nonidx = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_level_dataset_non_index.csv")
    cancer_panel = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/cancer_panel_test_level_dataset.csv")
    cancer_imaging = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/imaging_level_dataset.csv")
    cancer_manifest = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/manifest.csv")
    cancer_medonc = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/med_onc_note_level_dataset.csv")
    cancer_path = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/pathology_report_level_dataset.csv")
    cancer_patientlevel = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/patient_level_dataset.csv")
    cancer_drugs = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/regimen_cancer_level_dataset.csv")
    mut =
    return cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs

cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs = load_data()

# Head
st.write("## Visulization of GENIE BPC NSCLC v2.0-public dataset")

# Task 1.1
st.write("# Part 1: Comparing oncologist-assessed progression vs imaging-assessed progression for different drugs")
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
df_melted_1 = df_melted_1[df_melted_1["progression_occurred"] == 1]
df_melted_1['progression_type'] = np.where(df_melted_1['progression_type'] == 'pfs_m_g_status', 'Notes Based', 'Imaging Based')
df_melted_1 = df_melted_1[~df_melted_1['regimen_drugs'].str.contains('Investigational Drug')]
all_drug_list = df_melted_1['regimen_drugs'].tolist()
drug_list = []
for item in all_drug_list:
    d_list = item.split(", ")
    drug_list += d_list
drug_list = sorted(list(set(drug_list)))
drugs_multiselect_1 = st.multiselect('Treatments_1', drug_list, default=['Nivolumab'])
drugs_multiselect_2 = st.multiselect('Treatments_2', drug_list, default=['Afatinib Dimaleate'])
drugs_multiselect_3 = st.multiselect('Treatments_3', drug_list, default=['Osimertinib'])

text_1 = ", ".join(sorted(list(drugs_multiselect_1)))
text_2 = ", ".join(sorted(list(drugs_multiselect_2)))
text_3 = ", ".join(sorted(list(drugs_multiselect_3)))

drug_allselect = list(set(drugs_multiselect_1 + drugs_multiselect_2 + drugs_multiselect_3))

text_all = [text_1,text_2,text_3]
count_all = [len(df_melted_1[df_melted_1["regimen_drugs"] == item]['record_id'].to_list()) for item in text_all]

names = locals()
for t in range(1,4):
    if count_all[t-1] == 0:
        #print(r'There is no record for set of' + str(names['text_' + str(t)]))
        st.write(r'There is no record for set' + str(names['text_' + str(t)]))

text_st = [text_all[i] for i in range(len(text_all)) if count_all[i] != 0]

subset_1 = df_melted_1[df_melted_1["regimen_drugs"].isin(text_st)]

drug_options = sorted(df_melted_1['regimen_drugs'].unique())
# selection = alt.selection_single(
#     fields=['regimen_drugs'],
#     bind=alt.binding_select(options=drug_options,
#                             name='Select Drug Regimen'),
#      init={'regimen_drugs': 'Docetaxel'}
# )

survival_dict_nb = {}
survival_dict_ib = {}
df_melted_1_nb = df_melted_1[df_melted_1["progression_type"] == 'Notes Based']
df_melted_1_ib = df_melted_1[df_melted_1["progression_type"] == 'Imaging Based']
for treatment in text_st:
    temp_years = df_melted_1_nb[df_melted_1_nb["regimen_drugs"] == treatment]
    temp_year_list = temp_years['time_till_progression'].tolist()
    survival_dict_nb[treatment] = temp_year_list
survival_df_nb = pd.DataFrame(columns=['Drugs', 'Time_to_progression'])
lo = 0
for name in text_st:
    for it in survival_dict_nb[name]:
        survival_df_nb.loc[lo] = [name,it]
        lo += 1


for treatment in text_st:
    temp_years = df_melted_1_ib[df_melted_1_ib["regimen_drugs"] == treatment]
    temp_year_list = temp_years['time_till_progression'].tolist()
    survival_dict_ib[treatment] = temp_year_list
survival_df_ib = pd.DataFrame(columns=['Drugs', 'Time_to_progression'])
lo = 0
for name in text_st:
    for it in survival_dict_ib[name]:
        survival_df_ib.loc[lo] = [name,it]
        lo += 1

chart_nb = alt.Chart(survival_df_nb).mark_bar(
    opacity=0.3,
    binSpacing=0
).encode(
    alt.X('Time_to_progression:Q', bin=alt.Bin(maxbins=100)),
    alt.Y('count()', stack=None),
    alt.Color('Drugs:N', legend=alt.Legend(title='Treatment'))
).properties(
     width=700,
     height=300,
     title='Time to Progression for each Drug for patients diagnosed by clinicians')

chart_ib = alt.Chart(survival_df_ib).mark_bar(
    opacity=0.3,
    binSpacing=0
).encode(
    alt.X('Time_to_progression:Q', bin=alt.Bin(maxbins=100)),
    alt.Y('count()', stack=None),
    alt.Color('Drugs:N', legend=alt.Legend(title='Treatment'))
).properties(
     width=700,
     height=300,
     title='Time to Progression for each Drug for patients diagnosed by Image')

# )
# chart_0 = alt.Chart.from_dict(survival_df).mark_bar().encode(
#     x = alt.X('progression_occurred:N', axis= None),
#     y = alt.Y('count():Q', axis=alt.Axis(grid=True)),
#     color = alt.Color('regimen_drugs:N', legend=alt.Legend(title='Progression Status')),
#     column=alt.Column('progression_type:N')
# ).configure_view(
#     stroke='transparent'
# ).properties(
#     width=50,
#     height=300,
#     title='Frequency of Progression for each Drug'
# )
chart_1 = chart_nb & chart_ib
st.altair_chart(chart_1)

# Task 1.2

# create a Kaplan-Meier curves for each drug
kmf_dict = {}
df_1 = df_1[~df_1['regimen_drugs'].str.contains('Investigational Drug')]
for drug in df_1['regimen_drugs'].unique():
    kmf_dict[drug] = lf.KaplanMeierFitter()
    mask = df_1['regimen_drugs'] == drug
    kmf_dict[drug].fit(df_1['tt_pfs_i_g_mos'][mask], df_1['pfs_i_g_status'][mask], label=drug)

# create a dataframe with the survival probabilities
survival_df = pd.DataFrame()
for drug, kmf in kmf_dict.items():
    survival_prob = kmf.survival_function_
    survival_prob.columns = ['survival_prob']
    survival_prob['drug'] = drug
    survival_prob['time'] = survival_prob.index
    survival_df = pd.concat([survival_df, survival_prob], axis=0)

# create the Altair plot with a dropdown menu
selection = alt.selection_single(
    fields=['drug'],
    bind=alt.binding_select(options=sorted(list(kmf_dict.keys()))),
    name='Select',
    init = {'drug': 'Docetaxel'}
)
survival_df = survival_df[survival_df['drug'].isin(text_st)]

alt_chart_12 = alt.Chart(survival_df).mark_line().encode(
    x='time:Q',
    y='survival_prob:Q',
    color='drug:N'
).properties(
     width=700,
     height=300,
     title='K-M curve for each Treatment')

# # create a Kaplan-Meier curves for each drug
# kmf_dict = {}
# for drug in df_md_1['regimen_drugs'].unique():
#     kmf_dict[drug] = lf.KaplanMeierFitter()
#     mask = df_md_1['regimen_drugs'] == drug
#     kmf_dict[drug].fit(df_md_1['tt_pfs_m_g_mos'][mask], df_md_1['pfs_m_g_status'][mask], label=drug)
#
# # create a dataframe with the survival probabilities
# survival_df = pd.DataFrame()
# for drug, kmf in kmf_dict.items():
#     survival_prob = kmf.survival_function_
#     survival_prob.columns = ['survival_prob']
#     survival_prob['drug'] = drug
#     survival_prob['time'] = survival_prob.index
#     survival_df = pd.concat([survival_df, survival_prob], axis=0)
#
# # create the Altair plot with a dropdown menu
# selection = alt.selection_single(
#     fields=['drug'],
#     bind=alt.binding_select(options=sorted(list(kmf_dict.keys()))),
#     name='Select',
#     init = {'drug': 'Docetaxel'}
# )
#
# alt_chart2 = alt.Chart(survival_df).mark_line().encode(
#     x='time:Q',
#     y='survival_prob:Q',
#     color='drug:N'
# ).add_selection(
#     selection
# ).transform_filter(
#     selection
# )
#
# new = alt_chart | alt_chart2

st.altair_chart(alt_chart_12)

# Part 2
st.write("# Part 2: Comparing the most frequently mutated genes in patients with different Ethnicity/Race")

# a = pd.read_table(r"J:\Download\data_mutations_extended.txt")
# a = a[a['SIFT_Prediction'] == 'deleterious']
#
# p = a[['Tumor_Sample_Barcode', 'Hugo_Symbol']]
# p.to_csv(r"C:\Users\tangz\Desktop\BMI706PJ\mut.csv")









