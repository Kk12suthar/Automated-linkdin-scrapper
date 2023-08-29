import time
import configparser
import numpy as np
from selenium.common.exceptions import NoSuchElementException
from ExcelFileHandler.manageExcelFile import ManageExcelFile

config = configparser.ConfigParser()
config.read('config.ini')


CATEGORY_WHITELIST = ['information technology & services', 'logiciels informatiques', 'information technology','hospitals',"construction"]


def fetch_data(list_companies_links):
    list_companies_links = list(dict.fromkeys(list_companies_links))  # remove duplicates

    # re-adjusting the link in order to retrieve data after
    for i in range(len(list_companies_links)):
        list_companies_links[i] += "about/"

    return list_companies_links



class BrowserNavigator:
    BASE_NEXT_PAGE = '&page='

    def retrieve_data(self, links, filename):
        xls_file = ManageExcelFile(filename)
        j = 0

        print("[+] Retrieving information about companies...")
        for link in links:
            self.browser.get(link)
            self._wait_to_find_element_by_css('div.org-module-card__margin-bottom')

            dic = dict()
            try:
                dic['name'] = self.browser.find_element_by_css_selector('h1.ember-view.text-display-medium-bold org-top-card-summary__title').get_attribute('title')
            except NoSuchElementException:
                dic['name'] = None

            try:
                dic['overview'] = self.browser.find_element_by_css_selector('p.break-words white-space-pre-wrap.t-black--light.text-body-medium').text
            except NoSuchElementException:
                dic['overview'] = None
            try:
                dic['website'] = self.browser.find_element_by_css_selector('span.link-without-visited-state').text
            except NoSuchElementException:
                dic['website'] = None
            try:
                dic['size'] = self.browser.find_element_by_css_selector('dd.t-black--light mb4.text-body-medium').text
            except NoSuchElementException:
                dic['size'] = None

            infos_key = self.browser.find_elements_by_css_selector('dt.org-page-details__definition-term.t-14.t-black'
                                                                   '.t-bold')
            infos_value = self.browser.find_elements_by_css_selector('dd.org-page-details__definition-text.t-14.t'
                                                                     '-black--light.t-normal')

            for i in range(len(infos_key)):
                infos_key[i] = infos_key[i].text

            # web site is in pos = 0, moreover in infos_key will appear also 'Company size' but it will not
            # considered since the css id is different from the group below
            if 'Website' in infos_key:
                pos = 1
            else:
                pos = 0
            if 'Industry' in infos_key:
                dic['industry'] = infos_value[pos].text
                pos += 1
            else:
                dic['industry'] = None
            if 'Headquarters' in infos_key:
                dic['headquarters'] = infos_value[pos].text
                pos += 1
            else:
                dic['headquarters'] = None
            if 'Type' in infos_key:
                dic['type'] = infos_value[pos].text
                pos += 1
            else:
                dic['type'] = None
            if 'Founded' in infos_key:
                dic['founded'] = infos_value[pos].text
                pos += 1
            else:
                dic['founded'] = None
            if 'Specialties' in infos_key:
                dic['specialties'] = infos_value[pos].text
                pos += 1
            else:
                dic['specialties'] = None

            j = j + 1
            xls_file.save_into_xls(dic, j)

    def get_companies_name(self, base_link):
        print("Loading initial page...")
        self.browser.get(base_link)
        self._wait_to_find_element_by_css('div.search-results-container')

        self.scroll_page_to_end()
        pages = self.browser.find_elements_by_css_selector('li.artdeco-pagination__indicator.artdeco'
                                                           '-pagination__indicator--number')
        n_pages = pages[-1].text
        print("[!] Total pages: " + str(n_pages))

        print("[+] Saving companies links...")
        list_elements_companies_links = self.browser.find_elements_by_css_selector('span.entity-result__title-text.t-16>a.app-aware-link')
        list_elements_companies_category = self.browser.find_elements_by_css_selector('div.entity-result__primary-subtitle.t-14.t-black.t-normal')

        list_companies_links = tuple([element.get_attribute('href') for element in list_elements_companies_links])
        list_companies_links = fetch_data(list_companies_links)

        for i in range(1, 2):
            print("Parsing page " + str(i+1) + " over " + str(n_pages))

            next_page = base_link + self.BASE_NEXT_PAGE + str(i+1)
            self.browser.get(next_page)
            self._wait_to_find_element_by_css('div.search-results-container')
            self.scroll_page_to_end()

            list_elements_companies_links = self.browser.find_elements_by_css_selector('span.entity-result__title-text.t-16>a.app-aware-link')
            list_elements_companies_category = self.browser.find_elements_by_css_selector('div.entity-result__primary-subtitle.t-14.t-black.t-normal')

            list_elements_companies_links = tuple([element.get_attribute('href') for element in list_elements_companies_links])
            list_elements_companies_links = fetch_data(list_elements_companies_links)
            print(list_companies_links,"links available for retrival")

        return list_companies_links

    def scroll_page_to_end(self):
        sleep_time = self.sleep_time

        page_is_fully_loaded = False
        while page_is_fully_loaded is False:
            page_is_fully_loaded = self._verify_all_page_is_loaded()
            time.sleep(sleep_time)

        print("Finished scrolling the page.")

    def _verify_all_page_is_loaded(self):
        print("Scrolling the page...")

        pre_scroll_page_height = self.browser.execute_script("return document.body.scrollHeight")
        self._scroll_page()
        after_scroll_page_height = self.browser.execute_script("return document.body.scrollHeight")

        # change the id of the element in order to looking for ending elements
        indicator_projects_still_loading = len(self.browser.find_elements_by_id('globalfooter-copyright'))

        if after_scroll_page_height == pre_scroll_page_height and indicator_projects_still_loading != 0:
            page_is_fully_loaded = True
        else:
            page_is_fully_loaded = False

        return page_is_fully_loaded

    def _scroll_page(self):
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def _wait_to_find_element_by_css(self, css_selector):
        sleep_time = self.sleep_time
        for attempts in range(self.max_loading_attempts):
            print("Attempt n°" + str(attempts + 1) + ". Current page: " + self.browser.current_url +
                  " element searched: " + css_selector)

            time.sleep(sleep_time)
            element = self._try_find_element(css_selector)
            if element is not None:
                time.sleep(sleep_time)
                return element

        raise NoSuchElementException("after ", self.sleep_time, " attempts the element is still not found.")

    def _try_find_element(self, css_selector):
        try:
            return self._find_element(css_selector)
        except NoSuchElementException:
            pass

    def _find_element(self, css_selector):
        element = self.browser.find_element_by_css_selector(css_selector)
        print('"' + css_selector + '"' + ' has been found')
        return element

    def log_in(self):
        print("Logging in...")

        self.browser.find_element_by_id("username").send_keys(config["LOGIN"]["EMAIL"])
        self.browser.find_element_by_id("password").send_keys(config["LOGIN"]["PASSWORD"])
        self.browser.find_element_by_xpath('//*[@id="organic-div"]/form/div[3]/button').click()
        #//*[@id="organic-div"]/form/div[3]/button

        while self.browser.current_url == "https://www.linkedin.com/uas/login":
            time.sleep(self.sleep_time)

        print("Logged")

    def __init__(self, browser):
        self.sleep_time = int(config['BROWSER']['DEFAULT_SLEEP_TIME'])
        self.max_loading_attempts = int(config['BROWSER']['MAX_LOADING_ATTEMPTS'])
        self.browser = browser
        browser.get("https://www.linkedin.com/uas/login")
