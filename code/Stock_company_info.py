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



def get_stock_history(driver, start_date = r"2019-01-01", end_date = r"2020-10-06", stock_symbols = None):

    # Get all the historical data: daily prices and volumes
    # The data will be downloaded from the TopStock.pl website: https://www.topstock.pl

    # Set the default download directory
    download_path = "..."
    prefs = {'download.default_directory' : download_path}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', prefs)

    prox = Proxy()
    prox.proxy_type = ProxyType.MANUAL
    prox.http_proxy = "188.242.27.193:8080"

    capabilities = webdriver.DesiredCapabilities.CHROME
    prox.add_to_capabilities(capabilities)

    driver = webdriver.Chrome(executable_path=driver_path, desired_capabilities=capabilities,
                              options=chrome_options)

    # Initialize the file counter
    file_counter = 0

    # Get the data for each stock symbol
    for s in range(0, stock_symbols.shape[0], 1):

        file_counter += 1

        sym = stock_symbols.loc[s]

        instrument_url = "https://www.topstock.pl/stock/stock/download_history/{}?date_from={}&date_to={}".format(sym, start_date, end_date)

        # Go the the instrument site
        driver.get(instrument_url)

        # wait 2.7s until the change happens
        t = 3.7 + np.random.random(1)[0]*1.312936
        time.sleep(t)

        # wait until the file downloads
        len_lof = len([f for f in os.listdir(file_path) if f[-4:] == ".xls"])

        t = 9.7 + np.random.random(1)[0]*4.312936

        time.sleep(t)

        len_lof = len([f for f in os.listdir(file_path) if f[-4:] == ".xls"])

        # Change the name of the downloaded file to match the symbol
        list_of_files = os.listdir(file_path)
        list_of_times = [os.path.getmtime(file_path + f) for f in list_of_files]
        max_time_index = list_of_times.index(max(list_of_times))
        latest_file = list_of_files[max_time_index]

        new_name = sym + "_data_{}_{}.xls".format(start_date, end_date)

        original_path = file_path + latest_file
        modified_path = file_path + new_name
        os.rename(original_path, modified_path)
    
    driver.quit()
    
"""
The files are downloaded as .xls but the formatting is off and pandas.read_excel throws CompDocError.
A way around this is, e.g. open the file through olefile package and then feed it to the pandas.read_excel
function. It is safer to save the files as csv for further processing.
"""

import olefile

def fix_broken_XLS(folder_name = "/Users/.../Stock_data"):

    list_of_xls = [i for i in os.listdir(folder_name) if i[-4:] == ".xls"]

    for xls in list_of_xls:

        broken_file = olefile.OleFileIO(folder_name + xls)

        read_file = pd.read_excel(broken_file.openstream("Workbook"))
        
        changed_name = xls.replace(".xls", ".csv")
        
        read_file.to_csv(folder_name + changed_name, index=False)
        
"""
The function below takes the csv files from the Stock_data folder and computes the variances and differences
based on the split dates, e.g.:

# Quarterly variances and differences
split dates = ["2019-01-01", "2019-04-01", "2019-07-01", "2019-10-01", "2020-01-01"]

The dates below were chosen to compare the period of increased COVID-19 panic in Poland (Q1 2020)
to the last year (2019). The other period shows how much the company managed to go through the crisis,
by providing information on the variance and difference in Q2-4 for 2019 and 2020.
"""
       
def stock_params(folder_path = "/Users/Ligol/Documents/Jakies_inne_dokumenty/Analizy/Finansowe/Stock_data",
                 split_dates: list = None, prop = None, date = None):
    
    """
    The variances and differences are in %.
    """
    
    file_list = os.listdir(folder_path)
    csv_list = [i for i in file_list if i[-4:] == ".csv"]
    
    labels = ["19Q1", "19Q24", "20Q1", "20Q24"]
    dates_list = ["2019-01-01","2019-04-01","2020-01-01","2020-04-01","2021-01-01"]

    interval_frames = [(split_dates[i], split_dates[i+1]) for i in range(len(split_dates)-1)]
    
    result = pd.DataFrame()
    
    for csv in csv_list:
        sym = re.search(r"(\w+)_data", csv).group(1)
        #ind = pd.Index(Stock_full_info["Symbol"]).get_loc(sym)
        
        dataset = pd.read_csv(folder_path + csv)

        params = {}
        for d in range(len(interval_frames)):

            label = labels[d]
            var_label = label + "_var"
            dif_label = label + "_dif"

            interval = interval_frames[d]
            start = interval[0]
            end = interval[1]
            condition = (dataset[date] >= start) & (dataset[date] < end)
            subset = dataset[condition]

            try:
                begin_value = subset[subset[date] == subset[date].min()][prop].values[0]
                end_value = subset[subset[date] == subset[date].max()][prop].values[0]
                
                difference = 100 * (end_value - begin_value) / begin_value
            except IndexError:
                difference = np.nan
                
            variance = 100 * subset[prop].var() / subset[prop].mean()
            
            # Get the variance
            params[var_label] = [variance]

            # And the difference
            params[dif_label] = [difference]

        params["Symbol"] = sym
        params = pd.DataFrame(params)

        result = pd.concat([result, params], axis=0)
        
    return result
