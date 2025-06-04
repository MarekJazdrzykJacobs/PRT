import abc
import string
import re

class Text:
    """
    The class contains methods dedicated for string.
    """

    @abc.abstractmethod
    def __init__(self):
        pass


    @staticmethod
    def filter_string(text: str):
        """
        The method is used to:
        - filtering out forbidden signs from text
        - preparing text to be send to database
        - removing spaces/tabs/etc from the start and from the end of string

        :parameter
            text: (str): text to be filtered

        :return
            text: (str): modified text
        """

        #Makse sure text is a string
        if not isinstance(text, str):
            text = str(text)

        # filter out not printable characters
        text = ''.join([char for char in text if char in string.printable])

        # Replace ' by ''. It will be required when data will be send to SQL database
        text = text.replace("'", "''")

        #Remove spaces/tabs/etc.
        text = Text.remove_spaces(text = text, on_start = True, on_end = True)


        return text


    @staticmethod
    def filter_bring_back(text: str):
        """
        The method is used to bring back SOME OF CHANGES provided by Text.filter_string()

        :parameter
            text: (str): text

        :return
            text: (str): modified text
        """

        #Makse sure text is a string
        if not isinstance(text, str):
            text = str(text)

        return text.replace("''", "'")


    @staticmethod
    def flatten_string(text: str):
        """
        The method is used to flattening text.

        Example:
            flatten_string(text = 'Something FOR\nTest\t')  ---> 'somethingfortest'

        :parameter
            text (str): text to be flatten

        :return
            text (str): flatten text
        """


        #Convert to low case
        text = str(text).lower()

        #Remove special characters
        text = re.sub(r'\t|\n| |/', '' , text)

        #Remove not printable characters
        text = ''.join([char for char in text if char in string.printable])

        return text



    @staticmethod
    def remove_spaces(text: str, on_start: bool = True, on_end: bool = True):
        """
        The method is used to removing spaces/tabs/new lines on string beign/termination.

        :parameter
            text (str): text to update
            on_start (bool): remove spaces/tabs/new lines on string start
            on_end (bool): remove spaces/tabs/new lines on string termination

        :return
            text (str): upgraded text
        """

        #Make sure text is a string
        text = str(text)

        if on_start:
            re_pattern = re.compile('\A[ \t\n]*')
            text = re_pattern.sub('', text)
        if on_end:
            re_pattern = re.compile('[ \t\n]*\Z')
            text = re_pattern.sub('', text)

        return text

    @staticmethod
    def email2name(email: str):
        """
        The method used to build name based on email.

        :parameter:
            email (str): user email

        :return
            name (str): user name
        """

        #Check if email is valid
        if "@" not in email:
            return ''

        names, _ = email.split('@')

        #Take all sub names
        names = names.split('.')

        #Capitalize first letter in each name
        for idx, name in enumerate(names):
            names[idx] = name[0].upper() + name[1:]


        return ' '.join(names)

    @staticmethod
    def validation(text: str):
        """
        The method is used to checking if text does contain any non-printable characters.

        :return
            (bool). Return True if text does NOT contain non-printable characers, otherwise return False.
        """

        if not text:
            return True

        for char in str(text):
            if char not in string.printable:
                return False

        return True




