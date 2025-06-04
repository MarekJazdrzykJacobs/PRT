import os
import pandas as pd
import warnings
from config import sector_leads_mapper

# Ignore the pandas warnings
warnings.filterwarnings("ignore", message = "Boolean Series key will be reindexed to match DataFrame index", category = UserWarning)
warnings.filterwarnings("ignore", message = "Series.__getitem__ treating keys as positions is deprecated", category = FutureWarning)




class SectorVsMarekDoNotExist(Exception):
    pass


class SectorMaintainer:
    """
    Class allows to perform below actions:
        - finding disciplines for the specified project
        - finding sector lead for the specified project

    The core of class is provided pd.DataFrame (refer to constructor input parameters). It is the excel file "Sector vs Market". Within the methods are looking for information
    about the project sector and sector lead.
    """

    #Allowable disciplines
    disciplines = ['Adv Facilities%', 'Water/Utilities%', 'Transportation%', 'CMS/Built Environ%']


    def __init__(self, path2df: str):
        """
        :parameter
            path2df: str
                Path to "Sector vs Market.xlsx" file.
        """

        if not os.path.exists(path2df):
            raise SectorVsMarekDoNotExist(f"Excel file '{path2df}' do not exist!")


        #Read "Sector vs Market.xlsx"
        self.df = pd.read_excel(path2df).iloc[:, [1,2,3,4,5,6,7]].astype(str)
        self.df.fillna('', axis = 0, inplace = True)

        #Make all columns upper case. We will always compare upper case values.
        for col in self.df.columns:
            self.df[col] = self.df[col].apply(lambda x: str(x).upper())




    @staticmethod
    def find_sector_lead(discipline: str, return_email: bool = True) -> str:
        """
        Find the sector lead for the project. The method is mapping discipline with sector lead based on following dict:
            {"Water/Utilities": "katarzyna.skibinska@jacobs.com",
            "Adv Facilities": 'lukasz.mach@jacobs.com',
            "Transportation": 'marcin.kasprzak@jacobs.com',
            "CMS/Built Enviro": "tomasz.baradziej@jacobs.com"}

        IMPORTANT:
        If sector lead can not be found (for example because of wrong discipline) then method is returning 'Unassigned'.

        :parameters
            discipline: str
                name of project discipline

            return_email: str
                If True then sector lead will be return as email address.
                If False then sector lead will be return common convention Name + Surname

        :return
            Sector lead
        """

        #Check if discipline in in dict mapper
        if discipline in sector_leads_mapper:

            #Take email from mapper dict
            email = sector_leads_mapper[discipline]

            if return_email:
                return email
            else:
                #Convert email t Name + Surname
                email = email.split('@')[0]
                email = [i.capitalize() for i in email.split('.')]
                return ' '.join(email)

        return 'Unassigned'


    def find_discipline(self, pu: str, market: str, submarket: str) -> str:
        """
        Find disciplines for the project.

        IMPORTANT:
        If the method is not able to find discipline then it is returning ''

        :parameters
            pu: str
                data from column 'Controlling PU'

           market: str
                data from column 'Market'

           submarket: str
                data from column 'Sub Market'

        :return
            discipline
        """

        #Make sure input parameters are upper case
        pu = str(pu).upper()
        market = str(market).upper()
        submarket = str(submarket).upper()

        #Find discipline
        disciplines: pd.DataFrame = self.df[self.df['Controlling PU'] == pu][self.df['Market'] == market][self.df['Submarket'] == submarket][self.disciplines]

        if disciplines.shape[0] < 1:
            return ''

        for idx, disc in enumerate(self.disciplines):
            if disciplines.iloc[0, idx] == '1.0':
                return disc[:-1]
        return ''
