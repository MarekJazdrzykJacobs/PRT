import logging
import datetime
import time, os, shutil
import selenium.common.exceptions as exeptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from pathlib import Path
#from O365 import Account, FileSystemTokenBackend


MONTH = datetime.datetime.now().month
YEAR = datetime.datetime.now().year

today = datetime.datetime.today()
DAY = today.day
WEEK = (today.day - 1) // 7 + 1

"script vals"
DATE_TIME = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
EDGE_WEBDRIVER_PATH = r'C:\Users\JAZDRZM\OneDrive - Jacobs\Desktop\edgedriver_win64\msedgedriver.exe'
STARTING_PAGE = "https://jacobsanalytics.jacobs.com/analytics/saw.dll?Dashboard"
PATH_TO_FOLDER_FOR_DOWNLOAD = str(Path.home() / "Downloads")
RECURSIVE:bool = False

concat = []

" LOGGING "
logging.basicConfig(filename=f'Projects_Logs_{DATE_TIME}.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')





def swith_window(driver):
    _ = driver.window_handles
    new_ = _[-1]
    driver.switch_to.window(new_)
    driver.get(STARTING_PAGE)
    return driver


def wait_till_load(driver, class_name=None, time=10):
    if not class_name:
        return driver
    wait = WebDriverWait(driver, time)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, f"{class_name}")))
    return driver


def close_(driver):
    driver.close()
    driver.quit()


def go_to_projects(driver):
    try:
        wait = WebDriverWait(driver, 20)
        dropdown = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'dropdown')))

        for i in range(7):
            button = dropdown[i].find_element(By.TAG_NAME, 'button')
            button.click()

        opt = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, 'Project')))
        opt.click()
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        return driver
    except Exception as e:
        #logging.error(e)
        raise e



def findchkboxnumber(driver, chkbox_label=None, filter_name=None):
    """
    return check box radio button
    :param chkbox_label:
    :param driver:
    :return: driver, id
    """
    # if chkbox_label:
    #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, f'.checkboxRadioButton[value="{chkbox_label}"]')))
    # elif filter_name:
    #     WebDriverWait(driver, 20).until(
    #         EC.visibility_of_element_located((By.CSS_SELECTOR, f'.label[title="{chkbox_label}"]')))

    # driver = wait_till_load(driver, class_name="checkboxRadioButton")
    #Get the HTML code for the page
    html_code = driver.page_source
    #Parse the code through BeautifulSoup
    beautifulsoup_data = BeautifulSoup(html_code, 'html.parser')

    if chkbox_label:
        "only for radio box - select"

        #Every time the page loads it gives different IDs (sigh...). Get the one for Controlling Business Unit
        id_tag = beautifulsoup_data.find("input", {"class":"checkboxRadioButton","value":chkbox_label})
        #The ID is in the for HTML tag
        if id_tag:
            id_ = id_tag["id"]
            if chkbox_label in ["Charged LOB","Charged BU", "Project Type"]:
                try:
                    id_ = id_.split("_")[-1]
                except Exception as e:
                    logging.error(e)
                    raise TypeError
            return driver, id_
            # Correct the code to match the ID needed for the dropdown
            # id_ = id_.split("_")[-1]
        else:
            logging.error(f"method: findchkcboxnumber, error: no id_tag extracted from html tags: {chkbox_label}")
            raise TypeError

    elif filter_name:
        " for filters "
        _ = beautifulsoup_data.find("label", {"title": filter_name})
        # The ID is in the for HTML tag
        _ = _["for"]
        try:
            _ = _.replace("op", "1")
        except Exception as e:
            logging.error(e)
            raise TypeError
        return driver, _


def set_pagefilter_radio(driver, filter_name=None, filter_value=None):

    def worker2(driver, _):
        if radio_[1]:
            radio_button = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @id="{radio_[1]}"]')
            radio_button.click()
        driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).send_keys(
            Keys.RETURN)
        time.sleep(5)
        return driver

    def worker1(driver):
        _ = findchkboxnumber(driver, filter_name=filter_name)
        driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
        # driver.find_element_by_xpath("""//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
        driver = wait_till_load(driver, class_name="masterMenuItem")
        driver = wait_till_load(driver, class_name="promptDropdownNoBorderDiv")
        time.sleep(5)
        return _

    _ = worker1(driver)
    # if filter_name == "OPR Flag":
    #     radio_ = findchkboxnumber(driver, chkbox_label="*)nqgtac(*")
    # else:
    radio_ = findchkboxnumber(driver, chkbox_label=filter_value)
    try:
        driver = worker2(driver, _)
        return driver
    except TypeError as e:
        logging.error(e)
        time.sleep(5)
    #except Exception:
    #     ...

    if filter_name == "(All Column Values)":
        radio_ = findchkboxnumber(driver, chkbox_label="*)nqgtac(*")
    else:
        radio_ = findchkboxnumber(driver, chkbox_label=filter_value)
    time.sleep(5)
    try:
        driver = worker2(driver, _)
        return driver
    except Exception as e:
        logging.error(e)
        raise ValueError


def set_pagefilter_labels(driver, filter_name=None, filter_value=None):
    _ = findchkboxnumber(driver, filter_name=filter_name)
    driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
    driver = wait_till_load(driver, class_name="masterMenuItem")
    time.sleep(7)
    try:
        driver = driver.find_element(By.XPATH, f"//span[text()='{filter_value}']")
    except Exception as e:
        # el = driver.find_element(By.CLASS_NAME, "promptMenuOptionText")
        time.sleep(7)
        driver = driver.find_element(By.XPATH, f"//span[text()='{filter_value}']")
        # driver = WebDriverWait(driver, 10).until(
        #             EC.element_to_be_clickable((By.XPATH, f"//span[text()='{filter_value}']")))
    try:
        driver.click()
    except exeptions.ElementNotInteractableException as e:
        logging.error(e)
    except exeptions.ElementClickInterceptedException as e:
        logging.error(e)
    return _[0]

def unmark_all_values(driver, filter_name=None, filter_value=None):

    def get_value(driver, filter_value):
        # click filter Value
        radio_button = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{filter_value}"]')
        radio_button.click()
        driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).send_keys(Keys.RETURN)
        return driver

    _ = findchkboxnumber(driver, filter_name=filter_name)
    driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
    driver = wait_till_load(driver, class_name="masterMenuItem")
    # driver = wait_till_load(driver, class_name="promptDropdownNoBorderDiv")
    time.sleep(5)

    if _:
        wait_till_load(driver, class_name="checkboxRadioButton")
        time.sleep(1)
        chckbox = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="*)nqgtac(*"]')
        if chckbox.is_selected():
            chckbox.click()
            time.sleep(2)
            driver = get_value(driver, filter_value)
            return driver
        else:
            driver = get_value(driver, filter_value)
    return driver


def unmark_selected_values(driver, filter_name=None, unfilter_values=None, filter_value=None):

    def get_value(driver, filter_value):
        # click filter Value
        radio_button = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{filter_value}"]')
        radio_button.click()
        driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).send_keys(Keys.RETURN)
        return driver

    _ = findchkboxnumber(driver, filter_name=filter_name)
    driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
    driver = wait_till_load(driver, class_name="masterMenuItem")
    # driver = wait_till_load(driver, class_name="promptDropdownNoBorderDiv")
    time.sleep(5)

    if _:
        wait_till_load(driver, class_name="checkboxRadioButton")
        time.sleep(1)

        for i in unfilter_values:
            chckbox = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{i}"]')
            if chckbox.is_selected():
                chckbox.click()
                time.sleep(2)
        driver = get_value(driver, filter_value)
        return driver
    else:
        driver = get_value(driver, filter_value)
    return driver


def select_many(driver, filter_name=None, filters_values=None):

    _ = findchkboxnumber(driver, filter_name=filter_name)
    driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).click()
    driver = wait_till_load(driver, class_name="masterMenuItem")
    # driver = wait_till_load(driver, class_name="promptDropdownNoBorderDiv")
    time.sleep(5)

    if _:
        wait_till_load(driver, class_name="checkboxRadioButton")
        time.sleep(1)
        for i in filters_values:
            chckbox = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{i}"]')
            if not chckbox.is_selected():
                chckbox.click()
                time.sleep(1)
        driver.find_element(By.XPATH, """//*[@id="{}_dropdownIcon"]""".format(_[1])).send_keys(Keys.RETURN)
        return driver
    else:
        raise ValueError


def do_filter(driver, FILE_NAME, PATH_TO_FOLDER_FOR_DOWNLOAD, part):



    """
    Controlling LOB -> Poeple & places solutions
    Controlling PU -> 001600-AM North America
    Controlling BU -> PPS Advances facilities
    Controlling Region -> Advanced Manufacturing
    Controlling Sub Region -> AM North America
    Controlling Sub Region 2 -> AM North America SUB2

    :param driver:
    :param FILE_NAME:
    :param PATH_TO_FOLDER_FOR_DOWNLOAD:
    :return:
    """
    driver = wait_till_load(driver, class_name="PromptViewCell")

    try:

        if part == 1:
            """
            controlling LOB set as: PPS
            Projects Status Name set as: Active, Pending

            """
            set_pagefilter_radio(driver, filter_name="Controlling LOB", filter_value="PEOPLE & PLACES SOLUTIONS")
            time.sleep(5)
            return driver

        elif part == 2:

            print('inside item 2')
            """
            controlling LOB set as: PPS
            Projects Status Name set as: Close [unmark Acitve, Pending ]
            """
            set_pagefilter_radio(driver, filter_name="Controlling LOB", filter_value="PEOPLE & PLACES SOLUTIONS")
            time.sleep(5)
            driver = unmark_selected_values(driver, filter_name="Project Status Name", unfilter_values=['Active','Pending Close'] ,filter_value="Closed")
            time.sleep(5)
            return driver

        elif part == 3:

            """
            Controlling Lob : select all without PPS
                CORPORATE FUNCTIONS
                CRITICAL MISSION SOLUTIONS
                DIVERGENT SOLUTIONS
                ENERGY,CHEMICALS, & RESOURCES
                PA CONSULTING
                UNSPECIFIED
                Unspecified
            Project Satus Name : select all : 
                'Active,
                'Closed',
                'Pending Close',
                'Unspecified'
            """


            driver = select_many(driver, filter_name="Controlling LOB", filters_values=[
                'CORPORATE FUNCTIONS',
                'CRITICAL MISSION SOLUTIONS',
                'ENERGY, CHEMICALS, & RESOURCES',
                'PA CONSULTING',
                'UNSPECIFIED',
                'Unspecified'
            ])
            time.sleep(5)

            driver = select_many(driver, filter_name="Project Status Name", filters_values=[
                'Active',
                'Closed',
                'Pending Close',
                'Unspecified'
            ])
            time.sleep(5)

    except Exception as e:
        logging.error(e)
        raise e

    return driver


def export_current_screen(driver, folder_path, file_name, exportlinknumber, file_type, export_type):
    time.sleep(10)
    i = False
    x = 0
    while i == False and x <= 600:
        click_name = driver.find_elements(By.XPATH, value="//*[contains(@onclick,'idDownloadLinksMenud') and @name='ReportLinkMenu']")
        time.sleep(1)
        x = x + 1
        if x == 601:
            return False

        if click_name:
            click_name[exportlinknumber].click()
            i = True

    click_name = driver.find_element(By.XPATH, value="//a[@aria-label='" + export_type + "']")
    click_name.click()
    click_name = driver.find_element(By.XPATH, value="//a[@aria-label='" + file_type + "']")
    click_name.click()

    x = 0
    while not os.path.exists(os.path.join(folder_path, 'Project Search.csv')) and x <= 600:
    # while not any(filename.endswith('.crdownload') for filename in os.listdir(folder_path)) and x <= 600:
        if x in range(595, 601):
            return False
        time.sleep(5)
        x = x + 5

    print('crdownload->downloaded')
    time.sleep(5)

    for file in os.listdir(folder_path):
        # if file.endswith('Project Search.csv'):
        if file == 'Project Search.csv':
            print('.csv -is found')
            old_file_path = os.path.join(folder_path, file)
            new_file_path = file_name
            while True:
                try:
                    shutil.move(old_file_path, new_file_path)
                    break
                except Exception:
                    raise Exception

    time.sleep(3)
    click_name = driver.find_element(By.NAME, "OK")
    click_name.click()
    time.sleep(5)
    return True


def download_(driver, file_name, path_to_download):

    apply = driver.find_element(By.ID, "gobtn")
    # scroll to be visible
    driver.execute_script("arguments[0].scrollIntoView();", apply)
    apply.click()

    driver = wait_till_load(driver, class_name="PTChildPivotTable", time=600)
    time.sleep(5)

    try:
        is_download_true = export_current_screen(driver, path_to_download, file_name, 0, "CSV", "Data")   # "Excel", "Formatted"
        return driver, is_download_true
    except Exception as e:
        logging.error(e)
        raise NotImplementedError


def main(driver, file_name, path_to_download, part):
    """
    Main method to run JA scrapping for Projects
    :param driver: already created driver
    :return: None

    """

    logging.info(f"Starting downloading projects")

    try:
        # GO TO THE PROJECTS
        driver = go_to_projects(driver)
        time.sleep(5)
        # SET FILTERS
        driver = do_filter(driver, file_name, PATH_TO_FOLDER_FOR_DOWNLOAD, part)
        time.sleep(5)
        # DOWNLOAD CSV
        logging.info(f"JA Project has been Filtered")
        logging.info(f"downloading process has started")

        is_fiile_downloaded: tuple = download_(driver, file_name, path_to_download)
        time.sleep(5)
        driver = is_fiile_downloaded[0]
        if is_fiile_downloaded[1] is True:
            time.sleep(5)
            return driver
        else: raise Exception("File not downloaded")

    except Exception as e:

        logging.info(f"Next PERFORMANCE AFTER UNEXPECTED ERRORS")
        close_(driver)
        # gc.collect()
        time.sleep(5)
        options = webdriver.EdgeOptions()
        r = r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
        # r = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe'
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("prefs", preferences)
        # options.binary_location = r
        # options.binary_location = EDGE_WEBDRIVER_PATH

        driver = webdriver.Edge(executable_path=EDGE_WEBDRIVER_PATH, options=options)

        driver.maximize_window()
        logging.info("Window created")
        time.sleep(5)

        # driver.get(STARTING_PAGE)
        driver = swith_window(driver)
        time.sleep(5)
        return main(driver, file_name, path_to_download, part)


def run_JA_scrapping(part=None):
    logging.info("Projects Scrapper is starting")

    global preferences
    preferences = {"download.default_directory": PATH_TO_FOLDER_FOR_DOWNLOAD + "\\",
                   "browser.show_hub_popup_on_download_start": False}

    # Set options for chromedriver
    options = webdriver.EdgeOptions()
    r = r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    # r = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe'
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_experimental_option("prefs", preferences)
    #options.binary_location = r
    #options.binary_location = EDGE_WEBDRIVER_PATH


    driver = webdriver.Edge(executable_path=EDGE_WEBDRIVER_PATH)  #
    # The microsoft authentication screen will appear so the function created earlier is used
    driver.maximize_window()
    logging.info("driver created")

    driver.get(STARTING_PAGE)

    # driver = swith_window(driver)
    time.sleep(5)

    FILE_NAME = Path(PATH_TO_FOLDER_FOR_DOWNLOAD).joinpath(f"Projects_{YEAR}_{MONTH}_{str(DAY)}_part{part}.csv")
    logging.info(FILE_NAME)

    main(driver, FILE_NAME, PATH_TO_FOLDER_FOR_DOWNLOAD, part)
    driver.service.stop()
    try:
        close_(driver) if driver else ...
    except Exception as e:
        print(e)
    finally:
        # driver.service.stop() if driver else ...
        logging.info("DONE")

        # file concatenation
        # df_concat = pd.concat([pd.read_csv(i, low_memory=False) for i in concat])
        # concat_file = Path(PATH_TO_FOLDER_FOR_DOWNLOAD).joinpath(f"Project_Transactions_full.csv")
        # df_concat.to_csv(concat_file, index=False)

        return FILE_NAME


def copy_final_prt_files():
    target_folder = r"C:\Users\JAZDRZM\OneDrive - Jacobs\Desktop\PRT_files"
    today_project_date = f"{today.year}_{today.month}_{today.day}"
    for filename in os.listdir(target_folder):
        file_path = os.path.join(target_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    for part in ["part1", "part2", "part3"]:
        file_name = f'Projects_{today_project_date}_{part}.csv'
        source_file = os.path.join(PATH_TO_FOLDER_FOR_DOWNLOAD, file_name)
        if os.path.exists(source_file):
            shutil.copy(source_file, target_folder)


if __name__ == "__main__":

    run_JA_scrapping(part=1)
    run_JA_scrapping(part=2)
    run_JA_scrapping(part=3)

    print('done')





