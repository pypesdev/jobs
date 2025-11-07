
import time, random, os, csv, platform
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import pyautogui
from fake_useragent import UserAgent
import re
import yaml
from datetime import datetime, timedelta
import chromedriver_autoinstaller
from urllib.parse import urlparse, parse_qs
import requests
from openai import OpenAI
from dotenv import load_dotenv

log = logging.getLogger(__name__)

#chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path
ua = UserAgent()
user_agent = ua.random
options = Options()

# Disable webdriver flags or you will be easily detectable
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument('--no-sandbox')
options.add_argument("--disable-extensions")
options.add_argument("--disable-blink-features")
options.add_argument(f'--user-agent={user_agent}')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches",["enable-automation"])

# todo: running on selenium grid doesn't work atm due to pytautogui lock avoidance
# driver = webdriver.Remote(command_executor='http://localhost:4444', options=options)
driver = webdriver.Chrome(options=options)



def setupLogger() -> None:
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S_")

    if not os.path.isdir('./logs'):
        os.mkdir('./logs')

    logging.basicConfig(filename=('./logs/' + str(dt) + 'applyJobs.log'), filemode='w',
                        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s', datefmt='./logs/%d-%b-%y %H:%M:%S')
    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)


class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 20 * 60 * 60


    def __init__(self,
                 username,
                 password,
                 phone_number,
                 uploads={},
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[]) -> None:
        # Check for OpenAI API key
        load_dotenv()  # Loads variables from .env file

        log.info("Welcome to Easy Apply Bot")
        dirpath: str = os.getcwd()
        log.info("current directory is : " + dirpath)

        self.uploads = uploads
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        self.filename: str = filename
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number
        self.checked_invalid = False

    def get_appliedIDs(self, filename) -> list | None:
        try:
            df = pd.read_csv(filename,
                             header=None,
                             names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                             lineterminator='\n',
                             encoding='utf-8')

            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            log.info(f"{len(jobIDs)} jobIDs found")
            return jobIDs
        except Exception as e:
            log.info(str(e) + "   jobIDs could not be loaded from CSV {}".format(filename))
            return None

    def start_linkedin(self, username, password) -> None:
        log.info("Logging in.....Please wait :)  ")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element("id","username")
            pw_field = self.browser.find_element("id","password")
            login_button = driver.find_element(By.CLASS_NAME, "btn__primary--large")
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(3)
        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")

    def fill_data(self) -> None:
        try:
            self.browser.set_window_size(1, 1)
            self.browser.set_window_position(2000, 2000)
        except Exception as e:
            log.info(f"Could not set window size/position: {e}")

    def start_apply(self, positions, locations) -> None:
        start: float = time.time()
        self.fill_data()

        

        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if len(combos) > 500:
                break

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time: float = time.time()

        log.info("Looking for jobs.. Please wait..")
        try:
            self.browser.set_window_position(1, 1)
            self.browser.maximize_window()
        except Exception as e:
            log.info(f"Could not set window size/position: {e}")
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            print(driver.current_url)
            if 'linkedin' not in driver.current_url:
                driver.switch_to.window(driver.window_handles[0])
            try:
                log.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                # sleep to make sure everything loads, add random to make us look human.
                randoTime: float = random.uniform(3.5, 4.9)
                log.debug(f"Sleeping for {round(randoTime, 1)}")
                time.sleep(randoTime)
                self.load_page(sleep=1)
                # get job links, (the following are actually the job card objects)
                links = self.browser.find_elements("xpath",
                    '//div[@data-job-id]'
                )
                if len(links) == 0:
                    log.debug("No links found")
                    break
                IDs: list = []
                # children selector is the container of the job cards on the left
                for link in links:
                    # Find anchor tags within each link
                    children = link.find_elements(
                        "xpath", './/a[contains(@class, "job-card-container__link")]'
                    )
                    for child in children:
                        href = child.get_attribute("href")
                        if href:
                            # Extract the job ID from the href
                            parsed_url = urlparse(href)
                            job_id = parsed_url.path.split('/')[-2]  # Extract the job ID from the URL path
                            if job_id and int(job_id) not in self.blacklist:
                                IDs.append(int(job_id))
                jobIDs: list = set(IDs)

                # it assumed that 25 jobs are listed in the results window
                if len(jobIDs) == 0 and len(IDs) > 23:
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                    location,
                                                                    jobs_per_page)
                # loop over IDs to apply
                for i, jobID in enumerate(jobIDs):
                    count_job += 1
                    self.get_job_page(jobID)

                    button = self.get_easy_apply_button()

                    if button is not False:
                        string_easy = "* has Easy Apply Button"
                        log.info("Clicking the EASY apply button")
                        time.sleep(3)
                        #self.fill_out_phone_number()
                        result: bool = self.send_resume()
                        count_application += 1
                    else:
                        log.info("The button does not exist.")
                        string_easy = "* Doesn't have Easy Apply Button"
                        result = False

                    position_number: str = str(count_job + jobs_per_page)
                    log.info(f"\nPosition {position_number}:\n {self.browser.title} \n {string_easy} \n")

                    self.write_to_file(button, jobID, self.browser.title, result)

                    # sleep every 20 applications
                    if count_application != 0 and count_application % 20 == 0:
                        sleepTime: int = random.randint(100, 300)
                        log.info(f"""********count_application: {count_application}************\n\n
                                    Time for a nap - see you in:{int(sleepTime / 60)} min
                                ****************************************\n\n""")
                        time.sleep(sleepTime)

                    # go to new page if all jobs are done
                    if count_job == len(jobIDs):
                        jobs_per_page = jobs_per_page + 25
                        count_job = 0
                        log.info("""****************************************\n\n
                        Going to next jobs page, YEAAAHHH!!
                        ****************************************\n\n""")
                        self.avoid_lock()
                        self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                        location,
                                                                        jobs_per_page)
            except Exception as e:
                log.error("Exception in main application loop", e)
                print(e)

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):
        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        try:
            button = self.browser.find_elements("xpath", '//*[contains(@aria-label, "Easy Apply to")]')
            if len(button) == 0:
                return False

            javascript = """
            let elements = Array.from(document.querySelectorAll('button[aria-label]'));
            let targetElement = elements.find(el => el.getAttribute('aria-label').includes('Easy Apply to'));
            if (targetElement) {
                targetElement.click();
            }
            """

            self.browser.execute_script(javascript)
            time.sleep(1)
            return True
        except Exception as e:
            log.error("exception in get_easy_apply_button", e)
            return False        

    def fill_out_phone_number(self):
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0
        try:
            next_locater = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            input_field = self.browser.find_element("xpath", "//input[contains(@id,'phoneNumber')]")


            if input_field:
                input_field.clear()
                input_field.send_keys(self.phone_number)
                time.sleep(random.uniform(4.5, 6.5))
            


                next_locater = (By.CSS_SELECTOR,
                                "button[aria-label='Continue to next step']")
                error_locator = (By.CLASS_NAME,
                                "artdeco-inline-feedback__message")

                # Click Next or submitt button if possible
                button: None = None
                if is_present(next_locater):
                    button: None = self.wait.until(EC.element_to_be_clickable(next_locater))

                if is_present(error_locator):
                    for element in self.browser.find_elements(error_locator[0],
                                                                error_locator[1]):
                        text = element.text
                        if "Please enter" in text:
                            button = None
                            break
                if button:
                    button.click()
                    time.sleep(random.uniform(1.5, 2.5))
                    # if i in (3, 4):
                    #     submitted = True
                    # if i != 2:
                    #     break

        except:
            log.debug(f"Could not find phone number field")
                


    def send_resume(self) -> bool:
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0
        def has_errors() -> bool:
            return len(self.browser.find_elements(By.XPATH, '//*[contains(@type, "error-pebble-icon")]'))

        try:
            time.sleep(random.uniform(1.5, 2.5))
            next_locater = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            review_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Review your application']")
            submit_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Submit application']")
            submit_application_locator = (By.CSS_SELECTOR,
                                          "button[aria-label='Submit application']")
            error_locator = (By.CLASS_NAME,
                             "artdeco-inline-feedback__message")
            follow_locator = (By.CSS_SELECTOR, "label[for='follow-company-checkbox']")

            submitted = False
            while True:
                button: None = None
                buttons: list = [next_locater, review_locater, follow_locator,
                           submit_locater, submit_application_locator]
                for i, button_locator in enumerate(buttons):
                    if is_present(button_locator) and not has_errors():
                        button: None = self.wait.until(EC.element_to_be_clickable(button_locator))

                    if is_present(error_locator):
                        try:
                            for element in self.browser.find_elements(error_locator[0],
                                                                    error_locator[1]):
                                text = element.text
                                # if ("Please enter" in text or "Please make" in text or "Enter a" in text) and self.checked_invalid:
                                #     button = None
                                #     break
                                if ("Please enter" in text or "Please make" in text  or "Enter a" in text or "Select checkbox to proceed") and not self.checked_invalid:
                                    self.fill_invalids()
                                    break
                        except Exception as e:
                            log.info(e)

                    if button:
                        button.click()
                        time.sleep(random.uniform(1.5, 2.5))
                        if i in (3, 4):
                            submitted = True
                        if i != 2:
                            break
                # if button == None:
                #     self.checked_invalid = False
                #     log.info("Could not complete submission")
                #     break
                if submitted:
                    self.checked_invalid = False
                    log.info("Application Submitted")
                    # send a get request to the api
                    try:
                        requests.get('https://api.pypes.dev/job-application')
                    except Exception as e:
                        log.info(e)
                        log.info("cannot send job application to the api")
                    break

            time.sleep(random.uniform(1.5, 2.5))


        except Exception as e:
            log.info(e)
            log.info("cannot apply to this job")
            raise (e)

        return submitted

    def get_field_label(self, input_element):
        """Extract the label text associated with an input element"""
        try:
            # Try to find label by 'for' attribute
            input_id = input_element.get_attribute('id')
            if input_id:
                label = self.browser.find_element(By.XPATH, f"//label[@for='{input_id}']")
                if label:
                    return label.text.strip()
            
            # Try to find parent label
            parent_label = input_element.find_element(By.XPATH, "./ancestor::label")
            if parent_label:
                return parent_label.text.strip()
            
            # Try to find nearby label by proximity
            label_elements = self.browser.find_elements(By.XPATH, "//label")
            for label in label_elements:
                if label.is_displayed():
                    label_rect = label.rect
                    input_rect = input_element.rect
                    # Check if label is near the input (within 50px)
                    if (abs(label_rect['y'] - input_rect['y']) < 50 and 
                        abs(label_rect['x'] - input_rect['x']) < 200):
                        return label.text.strip()
            
            # Try to find placeholder or aria-label
            placeholder = input_element.get_attribute('placeholder')
            if placeholder:
                return placeholder.strip()
            
            aria_label = input_element.get_attribute('aria-label')
            if aria_label:
                return aria_label.strip()
                
        except Exception as e:
            log.debug(f"Could not extract label for input: {e}")
        
        return ""

    def get_appropriate_value(self, label_text, input_type="text"):
        """Determine appropriate value based on label text"""
        label_lower = label_text.lower()
        
        # Phone number fields
        if any(keyword in label_lower for keyword in ['phone', 'mobile', 'telephone', 'contact']):
            return self.phone_number
        
        # City
        if 'city' in label_lower or 'location' in label_lower or 'reside' in label_lower:
            return 'Knoxville'
        
        # Have worked
        if 'have you ever worked' in label_lower:
            return 'No'

        # State
        if 'state' in label_lower:
            return 'Tennessee'
        
        # Zip code
        if 'zip' in label_lower or 'postal' in label_lower:
            return '37923'
        
        # Salary expectations
        if any(keyword in label_lower for keyword in ['salary', 'wage', 'income']):
            return '180000'
        
        # Years of experience
        if ('experience' in label_lower and 'years' in label_lower):
            return '5'
        
        # Availability
        if 'available' in label_lower or 'start' in label_lower or 'notice' in label_lower:
            return '2 weeks'
        
        # Skills or technologies
        if any(keyword in label_lower for keyword in ['skill', 'technology', 'programming', 'language']):
            return 'Python, JavaScript, SQL'
        
        # Education
        if any(keyword in label_lower for keyword in ['education', 'degree', 'university', 'college']):
            return 'Bachelor'
        
        if any(keyword in label_lower for keyword in ['linkedin', 'linked-in', 'linked in']):
            return 'https://www.linkedin.com/in/LINKEDIN_USERNAME/'
        

        # Default value for text inputs
        if input_type == "text":
            llm_answer = self.get_llm_suggested_answer(label_text, input_type)
            if llm_answer:
                return llm_answer
            return '5'
        
        return ''

    def fill_invalids(self):
        try:
            location = driver.find_element(By.CSS_SELECTOR, "input[id*='GEO-LOCATION']")
        except Exception:
            location = None
        if location:
            location.send_keys('Knoxville, Tennessee')
            # 3. Wait for the dropdown to appear
            dropdown_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class, 'basic-typeahead__selectable')]//span[contains(@class, 'search-typeahead-v2__hit-text')]"
                ))
            )
            dropdown_option.click()

        try:
            your_name_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Your Name')]")

            # Get the input associated with that label using the 'for' attribute
            input_id = your_name_label.get_attribute('for')
            input_element = self.browser.find_element(By.ID, input_id)
            input_element.clear()
            input_element.send_keys('YOUR_NAME')
        except Exception as e:
            log.error(f"Error finding your name label: {e}")
            
        text_inputs = self.browser.find_elements(By.XPATH, '//input[contains(@class, "fb-dash-form-element")]')
        for input_element in text_inputs:
            try:
                label_text = self.get_field_label(input_element)
                input_type = input_element.get_attribute('type') or 'text'
                appropriate_value = self.get_appropriate_value(label_text, input_type)
                
                if appropriate_value:
                    input_element.clear()
                    input_element.send_keys(appropriate_value)
                    log.info(f"Filled field '{label_text}' with value: {appropriate_value}")
                else:
                    # Fallback to default behavior
                    input_element.clear()
                    input_element.send_keys('5')
                    log.info(f"Filled field '{label_text}' with default value: 5")

            except Exception as e:
                log.error(f"Error filling input field: {e}")
                # Fallback to default behavior
                try:
                    input_element.clear()
                    input_element.send_keys('5')
                except:
                    pass

        time.sleep(1)         
        # todo: don't select yes for requiring visa....
        radio_inputs = self.browser.find_elements(By.XPATH, '//input[@data-test-text-selectable-option__input="Yes"]')
        for input_element in radio_inputs:
            try:
                # Get the question text for the radio group
                question_text = self.get_radio_question_text(input_element)
                question_lower = question_text.lower()
                # Don't select "Yes" for visa sponsorship questions
                if any(keyword in question_lower for keyword in ['visa', 'sponsor', 'work authorization', 'citizen']):
                    # Try to find and click "No" instead
                    no_input = self.browser.find_element(By.XPATH, '//input[@data-test-text-selectable-option__input="No"]')
                    if no_input:
                        loc = no_input.location
                        element_to_click = driver.execute_script(
                            "return document.elementFromPoint(arguments[0], arguments[1]);",
                            loc['x'],
                            loc['y'])
                        element_to_click.click()
                        log.info(f"Selected 'No' for visa-related question: {question_text}")
                        continue
                # For other questions, select "Yes" as before
                loc = input_element.location
                element_to_click = driver.execute_script(
                    "return document.elementFromPoint(arguments[0], arguments[1]);",
                    loc['x'],
                    loc['y'])
                element_to_click.click()
                log.info(f"Selected 'Yes' for question: {question_text}")
            except Exception as e:
                log.error(f"Error handling radio button: {e}")
                # Fallback to original behavior
                try:
                    loc = input_element.location
                    element_to_click = driver.execute_script(
                        "return document.elementFromPoint(arguments[0], arguments[1]);",
                        loc['x'],
                        loc['y'])
                    element_to_click.click()
                except:
                    pass
        time.sleep(1)

        try:
            select_inputs = self.browser.find_elements(By.CSS_SELECTOR, 'select[aria-required="true"]')

            for input in select_inputs:
                question_text = self.get_select_question_text(input)
                question_lower = question_text.lower()
                log.info(f"Select input question: {question_text}")
                select_obj = Select(input)
                options = select_obj.options
                for option in options:
                    ot = option.text.lower()
                    if "immediate family" in question_lower and "no" in ot:
                        select_obj.select_by_visible_text(option.text)
                        log.info(f"Selected option '{option.text}' for question: {question_text}")
                    if "no" in ot and "require" in question_lower:
                        select_obj.select_by_visible_text(option.text)
                        log.info(f"Selected option '{option.text}' for question: {question_text}")
                    if ("yes" in ot and "do you require" not in question_lower) or "native" in ot or "U.S." in ot or "us" in ot or "linkedin" in ot or "united states" in ot or "citizen" in ot:
                        select_obj.select_by_visible_text(option.text)
                        log.info(f"Selected option '{option.text}' for question: {question_text}")
                    # else:
                    #     select_obj.select_by_index(0)
        except Exception as e:
            log.error('error doing select inputs', e)
                    
            
        text_area_inputs = self.browser.find_elements(By.XPATH, '//textarea[contains(@class, "fb-dash-form-element")]')
        for textarea in text_area_inputs:
            try:
                label_text = self.get_field_label(textarea)
                appropriate_value = self.get_appropriate_value(label_text, input_type="text")
                
                if appropriate_value:
                    textarea.clear()
                    textarea.send_keys(appropriate_value)
                    log.info(f"Filled textarea '{label_text}' with value: {appropriate_value}")
                else:
                    # Fallback to default behavior
                    textarea.clear()
                    textarea.send_keys('5')
                    log.info(f"Filled textarea '{label_text}' with default value: 5")

            except Exception as e:
                log.error(f"Error filling textarea field: {e}")
                # Fallback to default behavior
                try:
                    textarea.clear()
                    textarea.send_keys('5')
                except:
                    pass

        


    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self) -> None:
        pyautogui.FAILSAFE = False
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')

    def next_jobs_page(self, position, location, jobs_per_page):
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&sortBy=DD&start=" + str(jobs_per_page))
        self.avoid_lock()
        log.info("Lock avoided.")
        self.load_page()
        return (self.browser, jobs_per_page)

    def finish_apply(self) -> None:
        self.browser.close()

    def get_radio_question_text(self, input_element):
        """Extract the question text associated with a radio input element"""
        try:
           # Try to find the closest ancestor with a label or legend
            fieldset = input_element.find_element(By.XPATH, "./ancestor::fieldset[1]")
            return fieldset.accessible_name
        except Exception as e:
            log.debug(f"Could not extract radio question text: {e}")
        return ""

    def get_select_question_text(self, select_element):
        """Extract the question text associated with a select input element"""
        try:
            # Try to find label by 'for' attribute
            select_id = select_element.get_attribute('id')
            if select_id:
                label = self.browser.find_element(By.XPATH, f"//label[@for='{select_id}']")
                if label:
                    return label.text.strip()
            # Try to find parent label
            parent_label = select_element.find_element(By.XPATH, "./ancestor::label[1]")
            if parent_label:
                return parent_label.text.strip()
            # Try to find nearby label (preceding sibling)
            label = select_element.find_element(By.XPATH, "preceding-sibling::label[1]")
            if label:
                return label.text.strip()
            # Try to find aria-label
            aria_label = select_element.get_attribute('aria-label')
            if aria_label:
                return aria_label.strip()
        except Exception as e:
            log.debug(f"Could not extract select question text: {e}")
        return ""
    
    def get_llm_suggested_answer(self, label_text, input_type="text"):
        """Query OpenAI API for a suggested answer to the given label_text."""
        try:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            client = OpenAI(api_key=openai_api_key)
            prompt = f"Your name is YOUR_NAME. You are a professional filling out a job application form with vast experience in data engineering and AI/ML. You have worked with AWS, python, pandas, Typescript, node, react, ML, tensorflow, pytorch. Some of the projects you have worked on include a scheduling application for TSA that uses AI to schedule federal air marshalls on planes, a challenging technical component was keeping the legacy oracle database in sync with postgres using cdc. Provide a short, succinct, professional answer for the following interview quesion: '{label_text}' if it asks for numerics such as years of experience or hourly wage. answer with a numeric digit response: 5 for years of experience, and 180000 for salary"
            response = client.responses.create(
                model="gpt-4o",
                instructions=prompt,
                input = label_text
            )
            
            answer = response.output_text.strip()
            log.info(f"LLM suggested answer for '{label_text}': {answer}")
            return answer
        except Exception as e:
            log.error(f"OpenAI LLM request failed: {e}")
        return ""


if __name__ == '__main__':

    with open("./config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    assert len(parameters['positions']) > 0
    assert len(parameters['locations']) > 0
    assert parameters['username'] is not None
    assert parameters['password'] is not None
    assert parameters['phone_number'] is not None

    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " filename & path")

    log.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password']})

    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f != None]
    output_filename: list = output_filename[0] if len(output_filename) > 0 else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])

    uploads = {} if parameters.get('uploads', {}) == None else parameters.get('uploads', {})
    for key in uploads.keys():
        assert uploads[key] != None

    bot = EasyApplyBot(parameters['username'],
                       parameters['password'],
                       parameters['phone_number'],
                       uploads=uploads,
                       filename=output_filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles
                       )

    locations: list = [l for l in parameters['locations'] if l != None]
    positions: list = [p for p in parameters['positions'] if p != None]
    bot.start_apply(positions, locations)

