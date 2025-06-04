import os
from typing import List
import pandas as pd
from datetime import datetime
import re
from dotenv import load_dotenv
load_dotenv()

CWD = os.path.dirname(__file__)
DOWNLOAD_DIR = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Downloads')
#DOWNLOAD_DIR = r'C:\Users\JAZDRZM\Downloads'

#Sector vs Market
SECTOR_MAPPER_DIR = os.getenv('SECTOR_MAPPER_DIR')
UTYLIZATION_REPORT = os.getenv('UTYLIZATION_REPORT')

#Logger file
LOGS_DIR = os.path.join(CWD, 'logs.log')

class NonProjectCsvFound(Exception):
    def __init__(self, *args):
        self.message = 'None project csv has been found in Download directory'
        super().__init__(self.message)


def get_projects_csv(DIR: str = DOWNLOAD_DIR) -> List[pd.DataFrame]:
    """
    Get all projects csv from input DIR.

    :parameter DIR:
        DIR: path to directory where projects csv are

    :return:
        List with pd.DataFrames where each DateFrame mirror one csv file
    """
    #Initial output
    output = []

    #Get currect date
    today = datetime.today()

    re_pattern = re.compile(f'Projects_{today.year}_{today.month}_{today.day}_part\d+[.]csv')

    #Go thru each file in DIR
    for file in os.listdir(DIR):

        if re_pattern.match(file):
            path2csv = os.path.join(DIR, file)

            #Read csv file and append df to output
            output.append(pd.read_csv(path2csv, low_memory=False))

    if len(output) == 0:
        raise NonProjectCsvFound()
    return output


