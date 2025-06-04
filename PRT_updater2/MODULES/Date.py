import re
from datetime import datetime, timedelta
import abc
from dateutil.parser import parse



class Date:
    """
    The class supports the work with date.
    """

    @abc.abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def get_current_date(day_delay: int = 0):
        """
        The method is used to returning current date / delayed current date.

        :parameter:
            day_delay (str): how many days should be added to current date

        :return:
            date (str)

        """

        #Initial date
        date: datetime = datetime.now() + timedelta(days = day_delay)

        #Convert date to string
        date = date.strftime("%Y-%m-%d %H:%M:%S.0000000")

        return date


    @staticmethod
    def is_date(text: str, fuzzy: bool = False):
        """
        Return whether the string can be interpreted as a date.

        :parameter
            text (str): string to check for date
            fuzzy (bool): ignore unknown tokens in string if True

        :return
            (bool)
        """

        if not isinstance(text, str):
            return False

        pattern = re.compile("(\d{1,2}).(\d{1,2}).(\d+).*")
        match = pattern.match(text)

        if not match:
            return False

        #Check month
        month = match.group(2)
        if month.isdigit():
            if int(month) not in range(1,13):
                return False
        else:
            return False

        #Check day
        day = match.group(3)
        if day.isdigit():
            if int(day) not in range(1,32):
                return False
        else:
            return False


        try:
            parse(text, fuzzy = fuzzy)
        except ValueError:
            return False
        
        return True
    

    @staticmethod
    def compare_dates(dates: list):
        """
        The method is used to finding the newest date from list of dates.

        Valid format of date:
        '2023-01-15 00:00:00.0000000'

        :parameter
            dates (list): list of dates in string format
        """

        #Initial newest date
        newest_date = None

        #Pattern for splitting date
        re_pattern = re.compile('(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})[.](\d{7})')

        #Go thru each date
        for date in dates:

            #Skip not valid date
            if not Date.is_date(date):
                continue

            date = re_pattern.match(date)

            if not date:
                continue

            #Split date on sub-compose
            year, month, day, hour, minute, second = date.group(1), date.group(2), date.group(3), date.group(4), date.group(5), date.group(6)

            #Convert to datetime object
            date = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

            #Check if date is newer then previous one
            if newest_date == None:
                newest_date = date

            elif newest_date < date:
                newest_date = date

        return str(newest_date)