import requests
from config import SHAREPOINT_PULL_URL, SHAREPOINT_TOKEN
import json
from typing import List, Dict




class SharePointCrashed(Exception):
    pass

class Sharepoint:
    """
    Class provide methods to collaborate with Sharepoint.
    """

    HEADERS = {
        'x-token': SHAREPOINT_TOKEN
    }

    def pull_jsons(self) -> List[Dict[str, str]]:
        """
        Pull jsons from sharepoint.
        Method does not allow to indicate specified sharepoint file. It is hardcoded in SHAREPOINT_PULL_URL

        :return
            list with jsons
        """

        #Make a get request to power automate endpoint
        response = requests.get(url=SHAREPOINT_PULL_URL, headers=self.HEADERS, verify=False)

        if response.status_code != 200:
            raise SharePointCrashed('Can not download jsons from sharepoint')

        json_string = response.content.decode('utf-8')
        json_list = json.loads(json_string)

        return json_list
