import pandas as pd
import numpy as np
import os
import glob
import sidetable
import altair as alt
import lifelines as lf
import streamlit as st
from collections import Counter

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
    mut = pd.read_csv(r"https://raw.githubusercontent.com/ZkTang/BMI706PJ/master/mut.csv")
    return cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs,mut

cancer_idx, cancer_nonidx, cancer_panel, cancer_imaging, cancer_manifest, cancer_medonc, cancer_path, cancer_patientlevel, cancer_drugs, mut = load_data()

# Head
st.write("# Visulization of GENIE BPC NSCLC v2.0-public dataset")
st.write("###### BMI706,Zhengkuan Tang & Irbaz Riaz")

# Task 1.1
st.write("### Part 1: Comparing oncologist-assessed progression vs imaging-assessed progression for different drugs")
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
drugs_multiselect_1 = st.multiselect('Treatments_1', drug_list, default=['Carboplatin', 'Pemetrexed Disodium'])
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
    alt.X('Time_to_progression:Q', bin=alt.Bin(maxbins=100),title='Time to Progression (Months)'),
    alt.Y('count()', stack=None),
    alt.Color('Drugs:N', legend=alt.Legend(title='Treatment'))
).properties(
     width=700,
     height=300,
     title='Time to Progression for Each Treatment for Patients Diagnosed by Oncologists')

chart_ib = alt.Chart(survival_df_ib).mark_bar(
    opacity=0.3,
    binSpacing=0
).encode(
    alt.X('Time_to_progression:Q', bin=alt.Bin(maxbins=100),title='Time to Progression (Months)'),
    alt.Y('count()', stack=None),
    alt.Color('Drugs:N', legend=alt.Legend(title='Treatment'))
).properties(
     width=700,
     height=300,
     title='Time to Progression for Each Treatment for Patients Diagnosed by Image-based Techniques')

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
    x=alt.X('time:Q', title='Time (Months)'),
    y=alt.Y('survival_prob:Q', title='Survival Prob.'),
    color=alt.Color('drug:N', legend=alt.Legend(title='Treatment'))
).properties(
     width=700,
     height=300,
     title='K-M Curve for Each Treatment')

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
st.write("### Part 2: Comparing the Most Frequently Mutated Genes in Patients with Different Race Background")

# a = pd.read_table(r"J:\Download\data_mutations_extended.txt")
# a = a[a['SIFT_Prediction'] == 'deleterious']
#
# p = a[['Tumor_Sample_Barcode', 'Hugo_Symbol']]
# p.to_csv(r"C:\Users\tangz\Desktop\BMI706PJ\mut.csv")

#mut = pd.read_csv(r"C:\Users\tangz\Desktop\BMI706PJ\mut.csv")

# Sex Filter
sex_button = st.radio('Sex',['Male','Female'], index = 0 )
subset = mut[mut["Sex"] == sex_button]

#Race selectbox
race_list = list(set(mut['Race'].to_list()))
race_list = list(set(race_list) - {'Not Applicable', 'Not collected', 'Unknown'})
race_select = st.selectbox('Race_1', race_list, index=1)
race_select_2 = st.selectbox('Race_2', race_list, index=3)
subset_1 = subset[subset["Race"] == race_select]

dd_1 = dict(Counter(subset_1['Hugo_Symbol']))
sor_list_1 = sorted(dd_1.items(), key=lambda x:x[1],reverse=True)

sig_gene_1 = []
for s in range(10):
    sig_gene_1.append(sor_list_1[s][0])

gelist_1 = subset_1['Hugo_Symbol'].tolist()
gelist_modified_1 = ['Other' if gene not in sig_gene_1 else gene for gene in gelist_1]

subset_1['Gene_modified'] = gelist_modified_1
cor_1 = dict(Counter(subset_1['Gene_modified']))
cor_df_1 = pd.DataFrame.from_dict(cor_1,orient='index')
cor_df_1['Gene'] = cor_df_1.index
cor_df_1.columns = ['Count',"Gene"]
cor_df_1 = cor_df_1.drop(index='Other')
base_1 = alt.Chart(cor_df_1).encode(
    theta=alt.Theta("Count:Q", stack=True), color=alt.Color("Gene:N")
).properties(
     title='Top 10 Mutated Genes for Race: ' + str(race_select) )
pie_1 = base_1.mark_arc(outerRadius=120)
text_1 = base_1.mark_text(radius=140, size=20).encode(text="Gene:N")

chart3 = pie_1 + text_1

#Race selectbox
subset = subset[subset["Race"] == race_select_2]

dd = dict(Counter(subset['Hugo_Symbol']))
sor_list = sorted(dd.items(), key=lambda x:x[1],reverse=True)

sig_gene = []
for s in range(10):
    sig_gene.append(sor_list[s][0])

gelist = subset['Hugo_Symbol'].tolist()
gelist_modified = ['Other' if gene not in sig_gene else gene for gene in gelist]

subset['Gene_modified'] = gelist_modified
cor = dict(Counter(subset['Gene_modified']))
cor_df = pd.DataFrame.from_dict(cor,orient='index')
cor_df['Gene'] = cor_df.index
cor_df.columns = ['Count',"Gene"]
cor_df = cor_df.drop(index='Other')
base = alt.Chart(cor_df).encode(
    theta=alt.Theta("Count:Q", stack=True), color=alt.Color("Gene:N")
).properties(
     title='Top 10 Mutated Genes for Race: ' + str(race_select_2) )
pie = base.mark_arc(outerRadius=120)
text = base.mark_text(radius=140, size=20).encode(text="Gene:N")

chart4 = pie + text
chart_all = chart3 | chart4

st.altair_chart(chart_all)

genelist_total = set(cor_df['Gene'].tolist() + cor_df_1['Gene'].tolist())

text_w = 'There are ' + str(len(genelist_total)) + " genes on the top 10:"
st.write("#### "+ text_w)

for genes in genelist_total:
    text_hy = str(genes) + ' : ' + '[Genecard](https://www.genecards.org/cgi-bin/carddisp.pl?gene=' + str(genes) + ')'
    st.write(text_hy)

# task 3
st.write("### Part 3: Study the Survival Curve for Patients in the Different Stages when Diagnosed with NSCLC")

data = cancer_idx
df_melted2 = pd.melt(
    data,
    id_vars=["record_id", 'stage_dx', 'tt_os_dx_mos', 'tt_pfs_i_or_m_adv_mos'],
    value_vars=['os_dx_status', 'pfs_i_or_m_adv_status'],
    var_name="outcome_type",
    value_name="event_occurred"
)

# df_melted2["time_till_progression"] = df_melted2['tt_os_dx_mos']

df_melted2["time_till_event"] = df_melted2.apply(
    lambda x: x["tt_pfs_i_or_m_adv_mos"] if x["outcome_type"] == "pfs_i_or_m_adv_status" else x["tt_os_dx_mos"], axis=1)

df_melted2.drop(["tt_os_dx_mos", "tt_pfs_i_or_m_adv_mos"], axis=1, inplace=True)

df_melted2 = df_melted2.dropna(subset=['event_occurred', 'time_till_event', 'stage_dx'])

from lifelines import KaplanMeierFitter

# Define a list of unique combinations of stage_dx and progression_type
unique_combinations = [(stage, out_type) for stage in df_melted2['stage_dx'].unique()
                       for out_type in df_melted2['outcome_type'].unique()]

# Initialize a dictionary to store the fitted Kaplan-Meier models
kmf_dict = {}

# Loop over the unique combinations of stage_dx and progression_type
for stage, out_type in unique_combinations:

    # Select the data for the current combination of stage_dx and progression_type
    mask = (df_melted2['stage_dx'] == stage) & (df_melted2['outcome_type'] == out_type)
    data = df_melted2.loc[mask, ['time_till_event', 'event_occurred']].dropna()

    # Check if there are enough observations for reliable estimation
    if len(data) >= 10:
        # Fit the Kaplan-Meier model and store it in the dictionary
        kmf = KaplanMeierFitter()
        kmf.fit(data['time_till_event'], data['event_occurred'], label=f'{stage} ({out_type})')
        kmf_dict[(stage, out_type)] = kmf

survival_df = pd.DataFrame()
for (stage, out_type), kmf in kmf_dict.items():
    mask = (df_melted2['stage_dx'] == stage) & (df_melted2['outcome_type'] == out_type)
    survival_prob = kmf.survival_function_
    survival_prob.columns = ['survival_prob']
    survival_prob['stage_dx'] = stage
    survival_prob['out_type'] = out_type
    survival_prob['time'] = survival_prob.index
    survival_df = pd.concat([survival_df, survival_prob], axis=0)

survival_df['stage_dx'] = np.where(survival_df['stage_dx'] == 'Stage I-III NOS', 0,
                                   np.where(survival_df['stage_dx'] == 'Stage I', 1,
                                            np.where(survival_df['stage_dx'] == 'Stage II', 2,
                                                     np.where(survival_df['stage_dx'] == 'Stage III', 3, 4))))

# selection = alt.selection_single(
#     fields=['stage_dx'],
#     bind=alt.binding_range(min=0, max=4, step=1,
#                            name='Select Stage')
# )
slider = st.slider('Stage',min_value=0, max_value=4, value = 1)
survival_df = survival_df[survival_df['stage_dx'] == slider]

labels = {
    0: 'Stage I-III NOS',
    1: 'Stage I',
    2: 'Stage II',
    3: 'Stage III',
    4: 'Stage IV'
}

alt_chart = alt.Chart(survival_df).mark_line().encode(
    x=alt.X('time:Q', title='Time (Months)'),
    y=alt.Y('survival_prob:Q', title='Survival Prob.'),
    color=alt.Color('out_type:N', legend=alt.Legend(title='Outcome',
                                                    labelExpr="{'os_dx_status': 'Overall Survival', 'pfs_i_or_m_adv_status': 'Progression-free survival'}[datum.label]"))
).properties(
     width=700,
     height=300,
     title='K-M curve for Patients in the Different Stages when Diagnosed with NSCLC')

alt.data_transformers.enable('default', max_rows=10000)

# display the plot
st.altair_chart(alt_chart)




