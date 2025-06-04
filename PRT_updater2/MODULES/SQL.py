import pyodbc
import mysql.connector
import pandas as pd
import numpy as np
import string
import math
import uuid
from .Text import Text
from typing import Dict



class SQL:

    __slots__ = ['connector', 'cursor', 'tables', 'syntax']

    def __init__(self):

        self.connector = None
        self.cursor = None
        self.tables = None

        self.syntax = ['NEWID()'] #SQL syntax recognized by class

    def make_connection(self, connstring: str):

        """
        The function is used to preparing database connector.

        To reach a connection to any of Jacobs database the user must be connected to VPN or be in Jacobs web

        :parameter
            connstring (str): connection string to achieve database connector.
        """

        # Prepare connector
        self.connector = pyodbc.connect(connstring)
        # Prepare cursor
        self.cursor = self.connector.cursor()
        # Find the all tables in connected database
        self.tables = [i[2] for i in list(self.cursor.tables()) if i[3] == 'TABLE']



    def query(self, q: str, double_apostrof: bool = True):
        """
        The function is used to executing query in connected database.

        :parameter
            q (str): query. Example: 'SELECT * FROM table'
            double_apostrof (bool): if True then in SELECT case the mehtod will return data where all apostrof will be double.

        :return
            It depends of query. If query contains 'SELECT' then function will return data in pandas DataFrame format.
            Otherwise function will return None.

        """

        # Execute query (q)
        # print(q)
        # print('---')
        data = self.cursor.execute(q)

        if self.cursor.description != None:
            # Find columns name
            columns = [col[0] for col in self.cursor.description]

            # Transfer it to pandas DataFrame
            data = pd.DataFrame.from_records(data = data, columns = columns)

            if double_apostrof:
                # Additional filters
                for column in data.columns:
                    data[column] = data[column].apply(Text.filter_string)

            return data

        else:
            # Make a commit to database
            self.cursor.commit()

    def create_table(self, table_name: str, table_columns: iter):

        """
        The method is used to creating table in database.

        IMPORTANT:
        If table with the same name already exists in database then it will be deleted and re-created.

        By default, table columns datatype = 'text'

        :parameter
            table_name (str): name of table
            table_columns (iter): columns

        :return
            None. The method will create table in connected SQL database
        """

        # Delete table
        if table_name in self.tables:
            self.query(f"DROP TABLE [{table_name}]")

        # Prepare part of the query
        columns = ''
        for col in table_columns:
            columns = columns + '\n' + f'[{col}]  text,'

        columns = columns[:-1]

        query = f"""
        CREATE TABLE {table_name} ({columns})
        """

        # Create table
        self.query(query)

    def get_GUID(self):
        """The method generate GUID"""
        return str(uuid.uuid4()).upper()

    def send_data2table(self, table_name: str,
                        table_columns: list,
                        data: np.ndarray,
                        ignore_sql_syntax: bool = True,
                        return_query: bool = False,
                        filter_data: bool = False,
                        replace_nan_on_empty: bool = False):

        """
        The method is used to adding data to table.

        :parameter
            table_name (str): name of table into which user want to insert data
            table_columns (list of strings): list with columns
            data (np.ndarray): Data to be send to database. Shape must be (..., len(table_columns))
            ignore_sql_syntax (bool): if any value in data is in self.syntax then ignore_SQL_syntax take a decision if it should be treat as SQL syntax or simple string.
                                        For example:
                                        if data[0,0] == 'NEWID()' and ignore_sql_syntax = False that means 'NEWID()' is not string but it should be executed as SQL command
                                        if data[0,0] == 'NEWID()' and ignore_sql_syntax = True that means 'NEWID()' is a simple string.
            return_query (bool): if True then query is not executed but instead of it the query is returned\
            filter_data (bool): if True then data is filtered from forbidden signs and "'"

        :return
            None.
            Data added to table.

        IMPORTANT:
        - Table columns need to corresponding to data (np.array)
        """




        """
        IMPORTANT:
        SQL allows to insert max 1000 rows in one query.
        """

        if filter_data:
            # Make sure data is ready to be send to database
            f = np.vectorize(Text.filter_string)

            for idx in range(data.shape[1]):
                data[:, idx] = f(data[:, idx])


        #Determine how many loops are required. Each loop will add max 1000 rows to SQL database
        qty = math.floor(data.shape[0]/1000) + 1

        for i in range(qty):

            #Last set (equal or less than 1000 rows)
            if i + 1 == qty:
                data_1000 = data[1000*i:data.shape[0], :]
            else:
                #Take 1000 rows
                data_1000 = data[1000*i: 1000*i + 1000, :]

            #Break loop if there is no more data to upload
            if data_1000.shape[0] == 0:
                break

            # Prepare query
            query = f"""INSERT INTO [{table_name}] ("""

            for column in table_columns:
                query = query + f'[{column}], '

            query = query[:-2] + ') VALUES '

            for values in data_1000:
                query = query  + '('
                for idx, value in enumerate(values):

                    #last value
                    if idx + 1 == len(values):

                        if replace_nan_on_empty and any([value in (None, '', 'nan'), pd.isna(value)]):
                            query = query + f"""''"""
                        elif value not in self.syntax:
                            query = query + f"""'{value}'"""
                        elif value in self.syntax:
                            query = query + f"""{value}"""

                    else:
                        if replace_nan_on_empty and any([value in (None, '', 'nan'), pd.isna(value)]):
                            query = query + f"""'', """
                        elif value not in self.syntax:
                            query = query + f"""'{value}', """
                        elif value in self.syntax:
                            query = query + f"""{value}, """

                query = query + '), '

            # Cut last comma from query
            query = query[:-2]

            # Remove not printable characters
            query = [s for s in query if s in string.printable]
            query = ''.join(query)

            if not return_query:
                # Commit changes
                self.query(query)
            else:
                return query


    def kill_connection(self):
        """
        The method is used to closing SQL connection
        """
        if self.connector is not None:
            self.connector.close()


    def clear_table(self, table_name: str):
        """
        The method is used to cleaning table [table_name] without deleting entire table

        :parameter
            table_name (str): table to be deleted
        """

        self.query(f"""
        DELETE FROM [{table_name}]
        """)


    def take_column(self, column_name: str, table_name: str, conditions: iter, condition_values: iter):
        """
        The method used to getting column_name from 'table_name' based on 'conditions' and 'condition_values'.

        :parameter
            column_name (str): value to be found
            table_name (str): table name where value need to be looked for
            conditions (iter): column names to be compared
            condition_values (iter): values to be compared with conditions. For example: conditions[0] == condition_values[0] -> True etc.

        :return
            final_value (str): value from column_name
        """

        #Make sure data is ready to be send to database
        column_name = Text.filter_string(column_name)
        # conditions = [Text.filter_string(i) for i in conditions]
        # condition_values = [Text.filter_string(i) for i in condition_values]


        #Build query
        query = f"""
        SELECT [{column_name}]
        FROM [{table_name}]
        """

        #Go thru conditions and condition_values
        for condition, value in zip(conditions, condition_values):
            if "WHERE" not in query:
                query += f"\nWHERE [{condition}] = '{value}'"
            else:
                query += f"\nAND [{condition}] = '{value}'"


        final_value = self.query(query) #pd.DataFrame

        #Determine if final_value is not empty
        if final_value.shape[0] >= 1:
            final_value = final_value.iloc[0,0]
        else:
            final_value = ''

        return final_value


    def update_column(self, table_name: str, conditions: iter, condition_values: iter, columns2update: iter, new_values: iter, return_query: bool = False):
        """
        The method used to updating 'column2update' from table_name based on conditions and condition_values.

        :parameter
            table_name (str): table name where value need to be looked for
            conditions (iter): column names to be compared
            condition_values (iter): values to be compared with conditions. For example: conditions[0] == condition_values[0] -> True etc.
            columns2update (iter): columns to be updated
            new_values (iter): new value in 'columns2update'
            return_query (bool): if True then query is not executed but instead of it the query is returned

        IMPORTANT:
        1. conditions must correspond with condition_value.
        2. columns2update must correspond with new_values.
        """


        #Make sure data is ready to be send to database
        # conditions = [Text.filter_string(i) for i in conditions]
        # condition_values = [Text.filter_string(i) for i in condition_values]
        # columns2update = [Text.filter_string(i) for i in columns2update]
        # new_values = [Text.filter_string(i) for i in new_values]

        #Build query
        query = f"""
        UPDATE [{table_name}]
        """

        #Go thru columns2update and new_values
        for column, value in zip(columns2update, new_values):
            if "SET" not in query:
                query += f"\nSET [{column}] = '{value}'"
            else:
                query += f"\n, [{column}] = '{value}'"


        #Go thru conditions and condition_values
        for condition, value in zip(conditions, condition_values):
            if "WHERE" not in query:
                query += f"\nWHERE [{condition}] = '{value}'"
            else:
                query += f"\nAND [{condition}] = '{value}'"

        query = f'{query};'

        if not return_query:
            #Execute query
            self.query(query)
        else:
            return query

    def delete_row(self, table_name: str, conditions: iter, condition_values: iter):
        """
        The method used to removing rows from 'table_name' based on 'conditions' and 'condition_values'.

        :parameter
            table_name (str): table name where rows need to be removed
            conditions (iter): column names to be compared
            condition_values (iter): values to be compared with conditions. For example: conditions[0] == condition_values[0] -> True etc.

        """

        #Initial query
        query = f"""
        DELETE FROM [{table_name}]
        """

        #Go thru conditions and condition_values
        for condition, value in zip(conditions, condition_values):
            if "WHERE" not in query:
                query += f"\nWHERE [{condition}] = '{value}'"
            else:
                query += f"\nAND [{condition}] = '{value}'"

        # Execute query
        self.query(query)



    def table2dict(
        self, table_name: str, key_column: str, value_column: str, conditions = None, condition_values = None
    ) -> Dict[str, str]:
        """
        Convert table to python dict.
        If table does not exist then method will return empty dict.

        :parameter
            table_name: Table name to be converted to dict
            key_column: column to be used as key in dict
            value_column: column to be used as value in dict
            conditions (iter): column names to be compared
            condition_values (iter): values to be compared with conditions. For example: conditions[0] == condition_values[0] -> True etc.

        :return
            Dict[column1, column2]
        """
        # Initial output
        output = {}

        if not isinstance(conditions, list):
            conditions = []

        if not isinstance(condition_values, list):
            condition_values = []

        if table_name not in self.tables:
            return output


        #Initial query:
        query = f"""
                SELECT [{key_column}], [{value_column}]
                FROM [{table_name}]
                """

        # Go thru conditions and condition_values
        for condition, value in zip(conditions, condition_values):

            if "WHERE" not in query:
                value = str(value).replace("'", "")
                query += f"\nWHERE [{condition}] = '{value}'"

            else:
                value = str(value).replace("'", "")
                query += f"\nAND [{condition}] = '{value}'"


        # Take data from table
        data: pd.DataFrame = self.query(query)

        for key, value in zip(data.iloc[:, 0], data.iloc[:, 1]):
            output[key] = value

        return output


class MySQL:

    __slots__ = ['connector', 'cursor', 'tables']

    def __init__(self):

        self.connector = None
        self.cursor = None
        self.tables = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close database connection"""
        if self.connector is not None:
            self.connector.close()

    def kill_connection(self):
        """Close database connection"""
        if self.connector is not None:
            self.connector.close()

    def make_connection(self,
                        host: str,
                        user: str,
                        password: str,
                        database: str):

        """
        The function is used to preparing database connector.
        """

        # Prepare connector
        self.connector = mysql.connector.connect(host=host,
                                                 user=user,
                                                 password=password,
                                                 database=database)

        # Prepare cursor
        self.cursor = self.connector.cursor()

        # Find the all tables in connected database
        self.cursor.execute("SHOW TABLES")
        self.tables = [table[0] for table in self.cursor.fetchall()]


    def query(self, q: str):
        """
        Execute query

        :parameter
            q: query
        """
        self.cursor.execute(q)

        data = self.cursor.fetchall()

        if self.cursor.description != None:
            # Find columns name
            columns = [col[0] for col in self.cursor.description]

            # Transfer it to pandas DataFrame
            data = pd.DataFrame.from_records(data=data, columns=columns)

        return data