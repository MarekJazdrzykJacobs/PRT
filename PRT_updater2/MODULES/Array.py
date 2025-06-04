import abc
import numpy as np
import re
import string
import pandas as pd
from .Text import Text

class Array:
    """
    The class contains methods dedicated for numpy.ndarray objects.
    """

    @abc.abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def drop_duplicated(array: np.ndarray, unique_columns: list):
        """
        The method is used to removing duplicated rows in array.
        Row is treat as duplicated if combination of columns in unique_columns is not unique.
        So for example:

        array =
        [[1,2,4],
        [1,2,6]]

        if unique_columns = [0,1] then second row in array is duplicated since combination of 1 and 2 is not unqiue. It's causing second row will be removed

        IMPORTANT:
            - as default the method keeps first duplicated row

        :parameter
            array (np.ndarray): numpy array where duplicated rows need to removed
            unique_columns (list): list of column indexes which the combination need to be unique value

        :return
            array (np.ndarray): array with removed rows
        """

        existing_row = []

        #Initial idx2drop
        idx2drop = []

        for idx, row in enumerate(array):
            unique = ''.join([str(i) for i in row[unique_columns]])

            if unique not in existing_row:
                existing_row.append(unique)
                continue
            else:
                #Row is duplicated
                idx2drop.append(idx)


        #Drop indexes
        array = np.delete(array, idx2drop, axis = 0)

        return array



    @staticmethod
    def column_validation(header_name: str, column: np.ndarray, re_pattern: str, empty_value_acceptable: bool):
        """
        The method is used to validating column values based on provided regular expression pattern.
        If at least one value in column does not match re_pattern then the method will return error as description of what is wrong.

        :parameter
            header_name (str): header name. If error occures the method referes to this name
            columns (np.ndarray): numpy array with shape = (...,1)
            re_pattern (str): input value to re.compile
            empty_value_acceptable (bool): if empty cell should be treated as error or not
        """

        #Compile re pattern
        if re_pattern:
            re_pattern = re.compile(re_pattern)
        else:
            re_pattern = None

        #Check if shape is valid
        if len(column.shape) > 1:
            raise Exception('Shape need to be (..., 1)!')

        #Check if any cell is empty
        if not empty_value_acceptable and pd.DataFrame(column).isnull().values.any():
            return f"""Header '{header_name}' can not contains empty cell!"""

        #Go thru values in column
        for idx, value in enumerate(column):

            #Make sure value is a string
            value = str(value)

            #Make a value validation
            match = re_pattern.match(value)

            #If none match has been found
            if not match:
                return f"""In column '{header_name}' detected not valid value: '{value}'"""

            #If match was found but it is different then value
            if value != match.group(0):
                return f"""In column '{header_name}' detected not valid value: '{value}'"""

        return False


    @staticmethod
    def filter_array(array: np.ndarray, columns: iter):
        """
        The method is used to filtering out forbidden signs from numpy array values.

        :parameter
            array: (np.ndarray): array to be filtered
            columns (iter): iterable object with columns to be filtered

        :return
            array: (np.ndarray): modified array
        """

        # Initial filter
        filter = np.vectorize(Text.filter_string)

        # Go thru each column
        for col in columns:
            # Implement filter in column data
            array[:, col] = filter(array[:, col])

        return array


    @staticmethod
    def special_merge_arrays(arrays: iter, fill_missing: bool, based_on: int):

        """
        The method is used to merging (LEFT JOIN implementation) the arrays.

        IMPORTANT:
             - arrays[0] is treat as 'main' and each of next array will be merged to this one

        :parameter
            arrays (iter): container with np.ndarray to be merged
            fill_missing (bool):
            based_on (int):

            #todo: add missing description
        """

        #Take first array as initial
        initial_array = arrays[0]

        #Go thru each array
        for array in arrays[1:]:

            #Create empty array
            empty_array = np.empty(shape = (len(initial_array[:,1]), 1), dtype = object)


            #Go rows in initial_array
            for row_idx, row_value in enumerate(initial_array):

                #Take row number from initial_array
                init_row: int = row_value[4]

                #Take order number from initial_array
                init_order: int = row_value[based_on]

                #Filter array based on row. Row is under index 4
                row_filter: np.ndarray = array[array[:, 4] == init_row]

                #Filter row_filter based on order number
                order_filter: np.ndarray = row_filter[row_filter[:, based_on] == init_order]

                #Check if row stayed in order_filter
                if len(order_filter) > 0:
                    #Assign value in empty_array
                    empty_array[row_idx, 0] = order_filter[0,0]
                    continue

                if fill_missing:
                    # Check if row stayed in row_filter
                    if len(row_filter) > 0:
                        #Assign value in empty_array
                        empty_array[row_idx, 0] = row_filter[0,0]
                        continue


            #Append empty_array to initial array
            initial_array = np.hstack((initial_array, empty_array))


        return initial_array


    @staticmethod
    def drop_rows(array: np.ndarray, column_index: int = None, condition: str | list = None, mode: str = 'equal', axis = 0):
        """
        The method is used to dropping rows where column_index is equal condition

        :parameter
            array: (np.ndarray): array where rows need to e drop
            column_index (int): column index in array to compare with condition

        :return
            array: (np.ndarray): modified array
        """

        if mode == 'equal':

            #Check if condition is string
            if not isinstance(condition, str):
                raise Exception(f'condition must be a string. Received type: {type(condition)}')

            array = array[array[:, column_index] != condition]
            return array


        elif mode == 'in':

            # #Check if condition is list
            # if not isinstance(condition, list):
            #     raise Exception(f'condition must be a list. Received type: {type(condition)}')

            # Initial indexes to drop
            idx2drop = []

            for idx, row in enumerate(array):

                # Check if value match with condition_value
                if row[column_index] not in condition:
                    idx2drop.append(idx)

            return np.delete(array, idx2drop, axis = axis)


        elif mode == 'contains only':

            # Initial indexes to drop
            idx2drop = []

            for idx, row in enumerate(array):

                # Check if row contains only value from condition
                if set(row).issubset(set(condition)):
                    idx2drop.append(idx)

            return np.delete(array, idx2drop, axis = axis)

    @staticmethod
    def check_uniqueness(array: np.ndarray, columns_index: iter, ref_name: iter):
        """
        The method is used to checking if combination of columns_index in array is unique.

        For example:
        array = [[1,2,3],
                [1,2,5]]
        check_uniqueness(array, [0,1])  --> False

        array = [[1,2,3],
                [1,3,5]]
        check_uniqueness(array, [0,1])  --> True

        :parameter
            array (np.ndarray): array to be checked
            columns_index (iter): container with column indexes

        :return
            (bool)
        """

        #Initial error
        error = None

        #Initial unique_row. It will contain unique comination of columns_index
        unique_row = []

        #Go thru each row in array:
        for row in array:

            #Take combination of columns
            column_combination  = ', '.join([f"'{i}'" for i in row[columns_index]])

            if column_combination in unique_row:
                error = f"""Combination of columns {', '.join([f"'{i}'" for i in ref_name])} must be unique. Combination of {column_combination} is not unique, it appears more than one time in spreadsheet."""
                return error
            else:
                unique_row.append(column_combination)



        return error


    @staticmethod
    def merge_arrays(arrays: list | tuple, based_on: list | tuple, how: str = 'left'):

        """
        The method is used to merging the arrays

        IMPORTANT:
             - arrays[0] is treat as 'main' and each of next array will be merged to this one
             - length of 'based_on' must be eqyal to 'arrays'
        :parameter
            arrays (list | tuple): container with np.ndarray to be merged
            based_on (list | tuple): column indexes based on arrays need to be merged

        :return
            intial_array (np.ndarray): merged array
        """

        if len(arrays) != len(based_on):
            raise Exception("Length of 'arrays' must be equal to length of 'based_on'!")

        #Convert main array to pandas dataframe
        initial_df = pd.DataFrame(arrays[0])

        #Take 'base_on' index for main array
        initial_on = based_on[0]

        #Go thru each array
        for idx, array in enumerate(arrays[1:], start = 1):

            #Convert array to pandas dataframe
            right_df = pd.DataFrame(array)

            #Take 'based_on' for array
            right_on = based_on[idx]

            #Merge arrays
            initial_df = initial_df.merge(right = right_df, how = how, left_on = initial_on, right_on = right_on)

            #Drop 'right_on' column
            initial_df.drop(labels = ['0_y'], axis = 1, inplace = True)

        #Return np.ndarray
        return initial_df.values


    @staticmethod
    def compare_arrays(array: np.ndarray, array2compare: np.ndarray, drop_duplicates: bool = False, axis: int = 0):
        """
        The method is used to dropping rows from 'array' which already exists in 'array2compare'.

        :parameter
            array (np.ndarray): array to be modified
            array2compare (np.ndarray): array only for referencing
            drop_duplicates (bool): if drop duplicated rows
            axis (int): applicable only for 'drop_duplicates' = True. Axis from numpy array.

        :return
            if 'drop_duplicates' == True:
                array (np.ndarray): upgraded array

            else
                idx2drop (list): list of indexes for duplicated row in 'array'
        """

        #Initial idx2drop
        idx2drop = []

        #Covert array2compare to list
        array2compare = array2compare.tolist()

        #Go thru each row in array
        for idx, row in enumerate(array):

            #Check if such row already exists in array2compare
            tmp_row = list(row) in array2compare

            if tmp_row:
                #The row already exist in array2compare
                idx2drop.append(idx)


        if drop_duplicates:
            return np.delete(array, idx2drop, axis = axis)
        else:
            return idx2drop



    @staticmethod
    def replace_value(array: np.ndarray, column2replace: int, new_value, conditions: list, conditions_value: list):
        """
        The method is used to conditional replacing values in np.ndarray.

        :parameter
            array (np.ndarray): array where values need to be replaced
            columns2replace (int): index of column where values need to be replaced
            new_value (str|int): value to be added to 'column2replace'
            conditions (list): column indexes to be compared
            condition_values (list): values to be compared with conditions. For example: conditions[0] == condition_values[0] -> True etc.

        """

        # Initial indexes row indexes where value need to be replaced
        idx2replace = []

        # Gg thru array
        for idx, row in enumerate(array):

            # Compare conditions
            if row[conditions].tolist() == conditions_value:
                idx2replace.append(idx)

        # Replace value
        array[idx2replace, column2replace] = new_value

        return array

    @staticmethod
    def array2dict(array: np.ndarray, key_idx: int , value_idx: int):
        """
        The method is used to converting numpy array to dict

        :parameter
            array (np.ndarray): numpy array
            key_idx (int): column index to be used as key in output dir
            value_idx (int): column index to be used as value in output dir

        :return
            output_dir (dir):
        """

        #Initial output dir
        output_dir = {}

        #Go thru each row in array
        for key, value in zip(array[:, key_idx], array[:, value_idx]):

            if key not in output_dir:
                output_dir[key] = value


        return output_dir

    @staticmethod
    def find_values(array: np.ndarray, column_index: int, re_pattern: str, skip_none: bool):
        """
        The method is used to finding values in array[:, column_index] which match indicated re_pattern

        :parameter
            array (np.ndarray): array in which method should looked for.
            column_index (int): index of column in array where the method should looked for.
            re_pattern (str): regex pattern
            skip_none (bool): off method should skip empty/None values

        :return
            (list): list with values which match re_pattern

        """

        #Initial pattern
        re_pattern = re.compile(re_pattern)

        #Initial output
        output = []

        #Go thru each value
        for value in array[:, column_index]:
            if skip_none and not value:
                #Skip value
                continue

            #Make sure value is a string
            value = str(value)

            #Try to match value
            match = re_pattern.match(value)

            if match:
                output.append(value)

        return output


