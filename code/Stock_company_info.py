import pandas as pd
import numpy as np
import requests as rs
import bs4
import re
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.expected_conditions import text_to_be_present_in_element
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.webdriver.support.expected_conditions import url_changes
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import JavascriptException


url = "https://www.gpw.pl/spolki"

driver_path = "/Users/Ligol/Documents/UpWork/Drivers/chromedriver"
driver = webdriver.Chrome(executable_path=driver_path)
driver.get(url)

def More_data(driver):

    """
    Clicks "More results..." button until all results are loaded.
    """
    
    try:
        more_data = driver.find_element(By.CSS_SELECTOR, ".text-center.pager-company").find_element(By.TAG_NAME, "a")
        while more_data.is_displayed() == True:
            more_data.click()
            time.sleep(3.3 + np.random.random(1)[0]*1.53)
    except:
        pass
    
def get_stocks(driver):

    """
    Navigates through the page to get the names, tags and the link to the sub-page of that specific company.
    """

    search_results = driver.find_element(By.CSS_SELECTOR, ".footable.table.PaL.footable-loaded").find_element(By.TAG_NAME, "tbody")
    
    all_entries = search_results.find_elements(By.TAG_NAME, "tr")
    
    # Initiate the result dataframe
    Stocks = pd.DataFrame(columns=["Name", "Symbol", "Tags"])
    
    for e in all_entries:
        cols = e.find_elements(By.TAG_NAME, "td")
        
        # Get the stock name and tags
        stock_name = cols[0].find_element(By.TAG_NAME, "a").text
        stock_link = cols[0].find_element(By.TAG_NAME, "a").get_attribute("href")
        stock_symbol = cols[0].find_element(By.TAG_NAME, "a").find_element(By.CLASS_NAME, "grey").text
        stock_tags = cols[0].find_element(By.TAG_NAME, "small").text
        
        stock_entry = pd.DataFrame({
            "Name": [stock_name],
            "Link": [stock_link],
            "Symbol": [stock_symbol],
            "Tags": [stock_tags]
        })
        
        Stocks = pd.concat([Stocks, stock_entry])
        
    return Stocks

def get_instrument_info(driver, link_list = None):
    """
    Takes the list of link to the instrument subpage and copies the information on the company.
    """
    
    Instrument_info = pd.DataFrame()
    
    for k in link_list:
        
        # Enter the instrument subpage:
        driver.get(k)
        
        # wait some time
        time.sleep(3.1 + np.random.random(1)[0]*1.1627)
        
        # Save all the addresses - href in the stock name or near it
        params_css = ".col-md-8.col-lg-9.margin-bottom-20"
        params_id = "company-card-tabs"
        indicators_tab_css = ".panel.panel-default.nav-item.indicatorsTab"
        indicators_click_css = ".accordion-toggle.nav-link"
        indicators_css = ".collapse-indicatorsTab"
        name_id = "setH1"
        indicators_id = "indicatorsTab"
        
        try:
            
            # Enter the indicators table
            WebDriverWait(driver, timeout=25, poll_frequency=0.5
                         ).until(presence_of_element_located((By.ID,
                                                              params_id))
                                ).find_element(By.CSS_SELECTOR,".nav-item.indicatorsTab"
                                              ).find_element(By.CLASS_NAME, "nav-link").click()

            time.sleep(1.1 + np.random.random(1)[0]*0.3123)

            params = driver.find_element(By.ID, params_id).find_element(By.ID, indicators_id)

            # get the name of the instrument
            instrument_name = driver.find_element(By.CSS_SELECTOR, params_css).find_element(By.ID, name_id).text

            # tu znaleźć wszystkie tagi tr
            indicators = params.find_elements(By.TAG_NAME, "tr")
            Instrument_data = pd.DataFrame({i.find_element(By.TAG_NAME, "th").text: [i.find_element(By.TAG_NAME, "td").text] for i in indicators})

            # Save info about the company
            info_css = ".col-md-4.col-lg-3.margin-bottom-30"
            info_paragraph_css = ".margin-bottom-20.grey"

            info = driver.find_element(By.CSS_SELECTOR, info_css)
            info_paragraph = info.find_element(By.CSS_SELECTOR, info_paragraph_css).text

            # Stitch the data together
            Instrument_data["Description"] = info_paragraph

            company_name = re.search(r"(\w+)\s\(", instrument_name).group(1)

            # Rename the index
            Instrument_data.rename(index={0: company_name}, inplace=True)

            Instrument_info = pd.concat([Instrument_info, Instrument_data], axis=0)
            
        except UnexpectedAlertPresentException:
            continue
            
    Instrument_info.reset_index(inplace=True, drop=True)
        
    return Instrument_info
