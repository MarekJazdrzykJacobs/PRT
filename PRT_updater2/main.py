import sys

import fill_database
from MODULES.DataFrame import DF
from MODULES.Array import Array
from MODULES.SQL import SQL, MySQL
from typing import Iterable, Dict, List
import pandas as pd
from config import *
import numpy as np
#from user_table import *
from sector import SectorMaintainer
import os
from MODULES.Sharepoint import Sharepoint, SharePointCrashed
from logger import logger
from datetime import datetime
from path_manager import *
from utylization import get_utylization_data
from fill_database import updload_data_to_sql


class Maintainer:

    """
    Data maintainer. It allows for cleaning/uploading data to database.
    It is uploading data to following tables:
        - PrtProjectsTable
        - DisciplineTable
        - UserTable
        - PrtProjectsDetailsTable
    """

    def __init__(self, upload2database: bool = True, clear_database: bool = True):
        """

        parameters:
            upload2database: bool
                If True then data will be uploaded to database

            clear_database: bool
                If True then database will be cleaned before any upload.
        """

        self.upload2database = upload2database


        #Initial SQL connector
        self.sql = SQL()
        self.sql.make_connection(connstring = connstring)

        #Initial connection to MySQL database
        self.mysql = MySQL()
        self.mysql.make_connection(HOST, USER, PASSWORD, DATABASE)

        #Before cleaning gather column 'SummaryBookedHours' mapper
        self.last_summary_booked_hours = self.sql.table2dict(table_name='PrtProjectsDetailsTable', key_column='PrtProjectsModelsProjectNumber', value_column='SummaryBookedHours')



        #Clear tables
        if clear_database:
            self.sql.clear_table(table_name = 'PrtProjectsTable')
            self.sql.clear_table(table_name = 'DisciplineTable')
            self.sql.clear_table(table_name = 'UserTable')
            self.sql.clear_table(table_name = 'PrtProjectsDetailsTable')


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        #Close database connection
        self.sql.kill_connection()
        self.mysql.kill_connection()



    def find_sector_lead(self, discipline: str):
        """
        Based on discipline find sector lead

        :parameter
            discipline: str

        :return:
            sector_lead: str
        """

        _group = None
        sector_lead = ''

        #Find group in which indicated discipline is
        for group, disciplines in groups.items():
            if discipline in disciplines:
                _group = group
                break

        #Find sector lead
        if _group and _group in sector_leads_mapper:
            sector_lead = sector_leads_mapper[_group]

        return sector_lead


    def find_discipline(self, employee_gen: str):
        """
        Based on Employee GEN number find discipline id the employee is assigned to.

        IMPORTANT:
        Method can be used only be method self.fill_database.
        It caused because of the method is utilizing json file which is input to self.fill_database method.

        :parameter
            employee_gen: str
                Employee number in 6 or 9 digit format

        :return
            employee_disc_id: str
                Id of discipline to which indicated employee is assigned to. If employee does not exist in json file then
                return 'UNASSIGNED'.
        """

        #Make sure employee_gen is a str
        employee_gen = str(employee_gen)

        if employee_gen not in self.gen2discipline:
            return int(self.disciplines['UNASSIGNED'])

        employee_disc = self.gen2discipline[employee_gen]

        #Take id of employee_disc
        if employee_disc not in self.disciplines:
            return int(self.disciplines['UNASSIGNED'])

        employee_disc_id = self.disciplines[employee_disc]

        return int(employee_disc_id)



    def find_email(self, employee_gen: str) -> str:
        """
        Based on employee_gen find employee email.

        :parameter
            employee_gen: str
        :return
            employee_email: str
        """

        #Make sure employee_gen is a str
        employee_gen = str(employee_gen)

        #Make sure GEN has 6 characters
        if len(employee_gen) == 9:
            employee_gen = employee_gen[3:]

        #Make sure employee_gen is in mapper
        if employee_gen not in self.gen2email:
            return f'GEN: {employee_gen}'

        return self.gen2email[employee_gen]


    def fill_database(self, projects_dfs: Iterable[pd.DataFrame], json_all: Iterable[Dict[str, str]], sector_mapper_path: str, utylization_report: str):
        """
        todo: add descirption

        :parameters


        """

        #Initial sector maintainer
        try:
            sector_maintainer = SectorMaintainer(sector_mapper_path)
        except Exception as e:
            logger.critical(str(e))

        #Use Utylization report from xlsx instead of using sharepoint lists in json format
        utylization_df = get_utylization_data()


        #Take date for tables: DisciplineTable, UserTable
        usr_table = self.mysql.query("""
        SELECT
        Den AS `Employee Number`,
        UserEmail AS `Employee Email Address`,
        RoleName AS `Local Job Title`,
        JacobsOffice AS `Employee Work Location`,
        departments.DepartmentName AS `Employee Department`,
        Supervisor
        
        FROM Users
        
        LEFT JOIN departments ON
        Users.DepartmentId = departments.DepartmentId
        
        WHERE Users.AssignmentStatus != 'Deleted'
        """)

        usr_table['Line Of Business'] = ''
        usr_table['Sub Region'] = 'Europe GDC'

        fill_database.updload_data_to_sql(usr_table, 'Importer_User_Table', True, False)

        disciplines = set(usr_table['Employee Department'].values)

        #Add discipline 'UNASSIGNED' to disciplines
        disciplines.add('UNASSIGNED')

        #Make mapper 'UserNumber': 'Employee Department'
        self.gen2discipline = Array.array2dict(array = usr_table.values, key_idx = 0, value_idx = 4)

        #Make mapper 'UserNumber': 'Employee Department'
        self.gen2email = Array.array2dict(array = usr_table.values, key_idx = 0, value_idx = 1)

        # ____________________________________________________________________________________________
        #DisciplineTable

        #Convert disciplines
        disciplines = np.array([[disc] for idx, disc in enumerate(disciplines)])
        disciplines_columns = ['DisciplineName']


        #Sent disciplines to DisciplineTable
        if self.upload2database:
            self.sql.send_data2table(table_name = 'DisciplineTable', table_columns = disciplines_columns,
                                     data = disciplines,
                                     filter_data = True,
                                     replace_nan_on_empty = False)


        #Pull DisciplineTable from database. We need to know what id was assigned to each discipline
        disciplines: np.ndarray = self.sql.query("""
        SELECT *
        FROM [DisciplineTable]
        """).values


        #Convert disciplines to dict
        self.disciplines = Array.array2dict(array = disciplines, key_idx = 1, value_idx = 0)



        # ____________________________________________________________________________________________
        #UserTable
        usr_table: np.ndarray = usr_table.values
        usr_table = np.delete(usr_table, 4, 1)

        usr_table_columns = ['UserNumber', 'Email', 'Position', 'Location', 'Supervisor', 'LineOfBusiness', 'Region', 'DisciplinesModelId']


        #Create DisciplinesModelId column
        disciplines_id = [[self.find_discipline(employee_gen = gen)] for gen in usr_table[:, 0]]
        disciplines_id = np.array(disciplines_id)

        #Append disciplines_id column to usr_table
        usr_table = np.hstack([usr_table, disciplines_id])

        # pd.DataFrame(data = usr_table).to_excel('usr_table.xlsx', index = False)

        #Drop rows where 'DisciplinesModelId' in ''
        usr_table = Array.drop_rows(array = usr_table, column_index = 6, condition = '', axis = 0)

        #Send data to UserTable
        if self.upload2database:
            # pd.DataFrame(usr_table, columns=usr_table_columns).to_excel('df.xlsx', index = False)
            self.sql.send_data2table(table_name = 'UserTable', table_columns = usr_table_columns,
                                     data = usr_table,
                                     filter_data = True,
                                     replace_nan_on_empty = True)

        self.usr_table = pd.DataFrame(data = usr_table, columns = usr_table_columns)
        del usr_table

        # self.json_df.to_excel('json_df.xlsx', index = False)

        # Go thru each df
        for idx, df in enumerate(projects_dfs):

            #df.to_excel('test.xlsx', index = False)

            #Take only required columns
            df = df.loc[:, ['Controlling PU', 'Project Number', 'Project Name', 'Customer Account Group Name', 'Project Description', 'Project Type', 'Project Manager', 'Market', 'Sub Market',
                            'Project Status Name']]

            #Merge df with json_df based on 'Project Number'
            df = df.merge(right = utylization_df, how = 'left', on = ['Project Number', 'Project Number'])

            #df.to_csv('test.csv', sep='\t', encoding='utf-8', index=False, header=True)
            fill_database.updload_data_to_sql(utylization_df, 'Importer_Utilization_Only', True, False)
            fill_database.updload_data_to_sql(df, 'Importer_Projects_With_Utilization', True, False)
            #Find sector sector leaders
            _sectors = []
            for pu, market, submarket, project_number in zip(df.loc[:, 'Controlling PU'], df.loc[:, 'Market'], df.loc[:, 'Sub Market'], df.loc[:, 'Project Number']):
                _sectors.append([project_number, sector_maintainer.find_discipline(pu, market, submarket)])

            sectors = pd.DataFrame(_sectors, columns = ['Project Number', 'ProSector'])
            fill_database.updload_data_to_sql(sectors, 'Importer_Sectors', True, False)

            sector_leads = pd.DataFrame(_sectors, columns = ['Project Number', 'SectorLead'])
            sector_leads.iloc[:, 1] = sector_leads.iloc[:, 1].apply(sector_maintainer.find_sector_lead)
            fill_database.updload_data_to_sql(sector_leads, 'Importer_Sector_Leads', True, False)
            #sector_leads.to_csv('sector_leads_ex.csv', sep='\t', encoding='utf-8', index=False, header=True)
            #ToDO from that point calculate in sql
            #Add sectors columns to table data
            df = df.merge(sectors, how = 'left', on = 'Project Number')

            #Add sector leads columns to table data
            #df = df.merge(sector_leads, how = 'left', on = 'Project Number')


            #____________________________________________________________________________________________
            #Table PrtProjectTable

            #Take data for table
            prt_project_table = df.loc[:, ['Project Number', 'Project Name', 'Customer Account Group Name', 'Discipline', 'SectorLead']].values
            #prt_project_table = df.loc[:, ['Project Number', 'Project Name', 'Customer Account Group Name', 'Discipline']].values




            #_________________________________
            #Table PrtProjectsDetailsTable
            project_details_table = df.loc[:, ['Project Number', 'Project Status Name', 'Project Description', 'Project Type', 'Project Manager', 'ProSector']]


            #Prepare support dfs. They will contains grouped hours

            #summary_hours
            summary_hours_df = utylization_df.groupby(['Project Number'])['Hours'].sum().reset_index()
            summary_hours_df.rename(columns = {'Hours': 'SummaryBookedHours'}, inplace = True)
            # summary_hours_df.to_excel('summary_hours.xlsx', index = False)

            #enginners hours
            engineers_hours_df = utylization_df[utylization_df['Group Type'] == 'Engineering'].groupby(['Project Number'])['Hours'].sum().reset_index()
            engineers_hours_df.rename(columns = {'Hours': 'EngineersBookedHours'}, inplace = True)
            # engineers_hours.to_excel('engineers_hours.xlsx', index = False)


            #non enginners hours
            non_engineers_hours_df = utylization_df[utylization_df['Group Type'] == 'Non Engineering'].groupby(['Project Number'])['Hours'].sum().reset_index()
            non_engineers_hours_df.rename(columns = {'Hours': 'WithoutEngineersBooked'}, inplace = True)
            # non_engineers_hours_df.to_excel('non_engineers_hours.xlsx', index = False)


            #most booked hours
            most_booked_df = utylization_df.groupby(['Project Number', 'Employee GEN'])['Hours'].agg(list)
            most_booked_df = most_booked_df.reset_index()
            #Take sum from 'Hours' lists
            most_booked_df['Hours'] = most_booked_df['Hours'].apply(lambda hours: sum(hours))
            #Sort it based on 'Hours'
            most_booked_df.sort_values(by = 'Hours', inplace = True, ascending = False)
            #Drop duplicates
            most_booked_df.drop_duplicates(subset = 'Project Number', keep = 'first', inplace = True, ignore_index = True)
            #most_booked_df.to_excel('most_booked_1.xlsx', index = True)
            #Convert 'Employee GEN' to email
            most_booked_df.iloc[:, 1] = most_booked_df.iloc[:, 1].apply(self.find_email)
            most_booked_df.to_excel('most_booked_2.xlsx', index = True)
            most_booked_df.rename(columns = {'Employee GEN': 'MostBookedhoursBy', 'Hours': 'MostBookedHours'}, inplace=True)
            # most_booked_df.to_excel('most_booked.xlsx', index = True)


            #last booked hours
            last_booked_df = utylization_df[['Project Number', 'Employee GEN', 'End of Week', 'Hours']].sort_values(by = 'End of Week', inplace = False, ascending = False)
            last_booked_df.drop_duplicates(subset = 'Project Number', keep = 'first', inplace = True, ignore_index = True)
            #Convert 'Employee GEN' to email
            last_booked_df.iloc[:, 1] = last_booked_df.iloc[:, 1].apply(self.find_email)
            last_booked_df.rename(columns = {'Employee GEN': 'LastBookedHoursBy', 'Hours': 'LastBookedHurs'}, inplace = True)
            last_booked_df.drop(labels = ['End of Week'], inplace = True, axis = 1)


            #first booked hours
            first_booked_df = utylization_df[['Project Number', 'Employee GEN', 'End of Week', 'Hours']].sort_values(by = 'End of Week', inplace = False, ascending = True)
            first_booked_df.drop_duplicates(subset = 'Project Number', keep = 'first', inplace = True, ignore_index = True)
            #Convert 'Employee GEN' to email
            first_booked_df.iloc[:, 1] = first_booked_df.iloc[:, 1].apply(self.find_email)
            first_booked_df.rename(columns = {'Employee GEN': 'ForstBookedHoursBy', 'Hours': 'ForstBookedHours'}, inplace = True)
            first_booked_df.drop(labels = ['End of Week'], inplace = True, axis = 1)


            #Merge main df with support dfs
            project_details_table = project_details_table.merge(right = summary_hours_df, on = 'Project Number', how = 'inner')
            project_details_table = project_details_table.merge(right = engineers_hours_df, on = 'Project Number', how = 'left')
            project_details_table = project_details_table.merge(right = non_engineers_hours_df, on = 'Project Number', how = 'left')
            project_details_table = project_details_table.merge(right = most_booked_df, on = 'Project Number', how = 'left')
            project_details_table = project_details_table.merge(right = last_booked_df, on = 'Project Number', how = 'left')
            project_details_table = project_details_table.merge(right = first_booked_df, on = 'Project Number', how = 'left')

            #Add column 'AmountOfSpecialists'
            specialists = utylization_df.groupby("Project Number")["Employee GEN"].agg(list)
            specialists_df = pd.DataFrame([[project_number, len(set(i))] for i, project_number in zip(specialists, specialists.index)])
            specialists_df.columns = ['Project Number', 'AmountOfSpecialists']
            project_details_table = project_details_table.merge(right = specialists_df, on = 'Project Number', how = 'left')


            #Rename columns
            project_details_table.rename(columns = {'Project Number': 'PrtProjectsModelsProjectNumber',
                                                    'Project Status Name': 'ProPhase',
                                                    'Project Description': 'ProDescription',
                                                    'Project Type': 'ProType',
                                                    # 'Market': 'ProSector',
                                                    'Project Manager': 'ProjectManager'}, inplace = True)




            #DeltaSummaryBookedHours
            for idx, (project_desc, sum_hours) in enumerate(zip(project_details_table['PrtProjectsModelsProjectNumber'], project_details_table['SummaryBookedHours'])):
                #Calc delta
                if project_desc in self.last_summary_booked_hours:
                    delta = round(float(sum_hours), 2) - round(float(self.last_summary_booked_hours[project_desc]), 2)
                else:
                    delta = 0

                project_details_table.loc[idx, 'DeltaSummaryBookedHours'] = delta



            #Change type for each column
            columns = {'SummaryBookedHours': float,
                       'WithoutEngineersBooked': float,
                       'EngineersBookedHours': float,
                       'MostBookedHours': float,
                       'LastBookedHurs': float,
                       'ForstBookedHours': float,
                       'DeltaSummaryBookedHours': float,
                       'AmountOfSpecialists': int}

            for col, col_type in columns.items():

                #Replace nan by 0
                project_details_table[col].fillna(value = 0, inplace = True)

                #Change type of column
                project_details_table[col] = project_details_table[col].astype(col_type)


            #In 'PrtProjectsTable' keep only projects exsist in 'PrtProjectsDetailsTable'
            idx2keep: list = Array.compare_arrays(array = prt_project_table[:, 0:1], array2compare = project_details_table.values[:, 0:1], drop_duplicates = False)
            prt_project_table = prt_project_table[idx2keep, :]


            # pd.DataFrame(prt_project_table).to_excel('prt_project_table.xlsx', index = False)
            # project_details_table.to_excel('project_details_table.xlsx', index = False)


            #Send data to Database
            if self.upload2database:

                #Table 'PrtProjectsTable'
                '''self.sql.send_data2table(table_name = 'PrtProjectsTable', table_columns = ['ProjectNumber', 'Name', 'Customer', 'Disciplines', 'SectorLead'],
                                         data = prt_project_table,
                                         filter_data = True,
                                         replace_nan_on_empty = True)'''
                self.sql.send_data2table(table_name='PrtProjectsTable',
                                         table_columns=['ProjectNumber', 'Name', 'Customer', 'Disciplines'],
                                         data=prt_project_table,
                                         filter_data=True,
                                         replace_nan_on_empty=True)

                # Table 'PrtProjectsDetailsTable'
                self.sql.send_data2table(table_name = 'PrtProjectsDetailsTable', table_columns = list(project_details_table.columns),
                                         data = project_details_table.values,
                                         filter_data = True,
                                         replace_nan_on_empty = True)



            #Update 'UpdateInfo' table
            self.sql.query(f"""
            INSERT INTO [UpdatesInfo] ([LastUpdate]) VALUES ('{datetime.now()}')
            """)

        logger.info("Table 'UserTable' updated")
        logger.info("Table 'PrtProjectsTable' updated")
        logger.info("Table 'PrtProjectsDetailsTable' updated")
        logger.info("Table 'UpdatesInfo' updated")
        logger.info("Process accomplished!")
        logger.info("---------------------------------------")


with Maintainer(upload2database = True, clear_database = True) as maintainer:

    logger.info("---------------------------------------")
    logger.info("Start the process of refreshing data...")
    ###############################################
    #Take projects data - csv files from 'Download' folder
    try:
        projects_dfs = get_projects_csv()
        logger.info(f".csv files with project data were successfully pull from '{DOWNLOAD_DIR}'")
    except NonProjectCsvFound:
        logger.critical(f"None .csv with project data was found for this day in directory '{DOWNLOAD_DIR}'")

    sharepoint = Sharepoint()
    '''
    ###############################################
    #Take json files from sharepoint
    sharepoint = Sharepoint()
    try:
        json_files = sharepoint.pull_jsons()
        logger.info(f"Json files were successfully pulled from sharepoint")
    except SharePointCrashed:
        logger.critical(f"Json files can not be pulled. Sharepoint is not responding.")

    json_files = [i['data'] for i in json_files]

    # Initial list which is going to contain data from all json files
    json_all = []

    # Go thru each json and  save data in json_all
    for json_file in json_files:
        json_all.extend(json_file)
    '''
    json_all = []

    ###############################################
    #Run process
    try:
        maintainer.fill_database(projects_dfs = projects_dfs, json_all = json_all, sector_mapper_path = SECTOR_MAPPER_DIR, utylization_report = UTYLIZATION_REPORT)
    except Exception as e:
        logger.critical(str(e))
        logger.info("The process failed!")
        logger.info("---------------------------------------")

