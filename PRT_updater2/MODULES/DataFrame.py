import abc
import json
import re
import pandas as pd
from typing import Iterable, List, Union, Dict

class DF:
    """
    The class contains methods dedicated for pd.DataFrame objects.
    """

    @abc.abstractmethod
    def __init__(self):
        pass


    @staticmethod
    def json2df(json_all: Iterable[Dict[str, str]], columns: List[str]) -> pd.DataFrame:
        """
        Convert a bunch of json files to one pd.DataFrame object. All json files need to have the same structure.
        Columns are converted in accordance to project requirements. For example:
        'InputData[Source]' ---> 'Source'
        '[Hours]'           ---> 'Hours'

        :parameter
            json_all:
                Container with jsons

            columns:
                List with columns to dataframe. Amount of columns needs to match json data.

        :return
            df: pd.DataFrame
                Converted json files
        """

        # Convert jsons to pd.DataFrame
        df = pd.DataFrame(json_all)

        # Update columns
        re_pattern = re.compile('.*\[(.*)\]')
        _columns = [re_pattern.match(col).group(1) for col in df.columns]

        # Overwrite columns in df
        df.columns = _columns

        return df.loc[:, columns]



    @staticmethod
    def merge_df(dfs: Iterable[Union[pd.DataFrame, str]], how = 'vertical'):
        """
        Merge pd.DataFrames.

        :paramter
            dfs: Iterable[pd.DataFrame | str]
                Data structure with pd.DataFrames to be joined. If dfs contains strings that means these are paths to .csv files.

        :return
            df_merged: pd.DataFrame
        """

        _dfs = []

        for df in dfs:

            #Case where df is a path to csv file
            if isinstance(df, str) and df.lower().endswith('csv'):
                df = pd.read_csv(df, dtype = str)

            # Case where df is a path to xlsx file
            if isinstance(df, str) and df.lower().endswith('xlsx'):
                df = pd.read_excel(df, dtype = str)

            #Append dataframe to main list
            _dfs.append(df)

        if how == 'vertical':
            df_merged = pd.concat(_dfs, ignore_index = True)
            return df_merged

