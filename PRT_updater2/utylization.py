import pandas as pd
from MODULES.Array import Array

UTYLIZATION_REPORT = f'C:\\Users\\JAZDRZM\\Jacobs\\GDC Poland Reporting - Actual\\Utilization input.xlsx'

def get_utylization_data(utylization_report_file=UTYLIZATION_REPORT):
    dtype_dict = {
        'Source': str,
        'PROJECT': str,
        'Employee GEN': str,
        'Discipline': str,
        'Group': str,
        'UT_Project_Type': str,
        'End of Week': str,
        'OSL_Bill_Hrs': float,
        'OSL_NB_Hrs': float,
        'OSL_Proposal_Hrs': float,
        'OSL_OH_Hrs': float,
        'OSL_OH_Booked to other PU': float,
        'OSL_PT_Exception': float,
        'OSL_Sick_Hrs': float,
        'OSL_Vacation': float,
        'OSL_Holiday_Hrs': float
    }

    utylization_df = pd.read_excel(utylization_report_file, engine='openpyxl', dtype=dtype_dict)
        #Create Group Type column
    utylization_df['Group Type'] = utylization_df.apply(lambda row: 'Engineering' if (row['Group'] in ["AF", "TR", "WT"] or row['Discipline'] == "Digital Delivery") else 'Non Engineering', axis=1)
    utylization_df['tot_hrs_incl_fringe'] = (
        utylization_df['OSL_Bill_Hrs'] +
        utylization_df['OSL_NB_Hrs'] +
        utylization_df['OSL_Proposal_Hrs'] +
        utylization_df['OSL_OH_Hrs'] +
        utylization_df['OSL_OH_Booked to other PU'] +
        utylization_df['OSL_PT_Exception'] +
        utylization_df['OSL_Sick_Hrs'] +
        utylization_df['OSL_Vacation'] +
        utylization_df['OSL_Holiday_Hrs']
    )

    filtered_utylization_df = utylization_df[(utylization_df['UT_Project_Type'].isin(["CONTRACT", "Overhead booked to other PU", "PROPOSAL", "UT_PL_Exception"])) & (utylization_df['tot_hrs_incl_fringe'] != 0)]

    summarized_df = filtered_utylization_df.groupby([
            'Source',
            'PROJECT',
            'Employee GEN',
            'Discipline',
            'Group',
            'Group Type',
            'UT_Project_Type',
            'End of Week'
        ]).agg({'tot_hrs_incl_fringe': 'sum'}).reset_index()

    summarized_df.rename(columns={'tot_hrs_incl_fringe': 'Hours'}, inplace=True)

    summarized_df = summarized_df[['PROJECT', 'Discipline', 'Group Type', 'Hours', 'Employee GEN', 'End of Week']]
    summarized_df['End of Week'] = summarized_df['End of Week'].apply(lambda x: str(x).replace('T00:00:00', '').replace('-', '/'))
    summarized_df['End of Week'] = pd.to_datetime(summarized_df['End of Week'], errors='coerce')
    summarized_df.rename(columns={'PROJECT': 'Project Number'}, inplace=True)
    return summarized_df

#summarized_df_unique = pd.DataFrame(data=Array.drop_duplicated(array=summarized_df.values, unique_columns=[0]), columns=summarized_df.columns)
#summarized_df.to_csv('summarized_df_unique.csv', index=False)