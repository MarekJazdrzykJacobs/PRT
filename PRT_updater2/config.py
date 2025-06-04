import os

from dotenv import load_dotenv
load_dotenv()

#Microsoft SQL server
connstring = os.getenv('MS_SQL_CONNSTRING')


#MySQL credentials
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')

sector_leads_mapper = {
    "Water/Utilities": "katarzyna.skibinska@jacobs.com",
    "Adv Facilities": 'lukasz.mach@jacobs.com',
    "Transportation": 'marcin.kasprzak@jacobs.com',
    "CMS/Built Environ": "tomasz.baradziej@jacobs.com"
}


#Sharepoint credentials
SHAREPOINT_PULL_URL = os.getenv('SHAREPOINT_PULL_URL')
SHAREPOINT_TOKEN = os.getenv('SHAREPOINT_TOKEN')

