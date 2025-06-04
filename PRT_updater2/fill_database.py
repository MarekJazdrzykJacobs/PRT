import datetime

from sqlalchemy import create_engine
import pandas as pd

server = '10.251.68.98'
database = 'prt_prod'
username = 'prtapp'
password = '479app'

MS_SQL_CONNSTRING = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"



def updload_data_to_sql(dataframe, table_name, replace: bool, index: bool):
    engine = create_engine(MS_SQL_CONNSTRING)
    if replace:
        dataframe.to_sql(name=table_name, con=engine, if_exists='replace', index=index)
        return True
    else:
        dataframe.to_sql(name=table_name, con=engine, if_exists='fail', index=index)
        return False


