from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import pickle
from selenium.common.exceptions import WebDriverException
import time
import random
import csv
import re

class InternalServerErrorException(Exception):
    """自定义异常，用于表示页面上出现内部服务器错误。"""
    pass

# 状态保存和加载函数
def save_state(state, filename='state.pickle'):
    with open(filename, 'wb') as f:
        pickle.dump(state, f)

def load_state(filename='state.pickle'):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None  # 如果文件不存在，返回 None
    
def process_all_journals(start_volume, end_volume, start_issue=1):
    state = load_state()  # 尝试加载之前保存的状态
    if state:
        current_volume, current_issue = state
    else:
        current_volume, current_issue = start_volume, start_issue

    try:
        for volume in range(current_volume, end_volume + 1):
            while True:
                try:
                    articles = get_article_info(volume, current_issue)
                    # Write articles to a CSV file
                    with open('journal_of_finance.csv', 'a', newline='', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, fieldnames=articles[0].keys())
                        if volume == start_volume and current_issue == start_issue:
                            writer.writeheader()  # Only write the header once
                        for article in articles:
                            writer.writerow(article)
                    print(f"Volume {volume}, Issue {current_issue} processed.")
                    current_issue += 1
                except InternalServerErrorException:
                    print(f"Volume {volume} completed. Moving to next volume.")
                    break
                except WebDriverException as e:
                    save_state((volume, current_issue))
                    raise e
            current_issue = 1  # Reset issue number for the next volume
    except Exception as e:
        save_state((volume, current_issue))
        raise e

    driver.quit()
    
    
# Setup Selenium Chrome WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

def get_article_info(volume, issue):
    # Define the base URL
    base_url = f"https://afajof.org/issue/volume-{volume}-issue-{issue}"
    driver.get(base_url)
    
    
    # Wait for the page to load by checking for a common page element or an error message
    try:
        WebDriverWait(driver, 40).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "div.article-result-container") or
                      d.find_elements(By.CSS_SELECTOR, "section.error-404")
        )
    except TimeoutException:
        # If neither element is found within the timeout period, raise an exception
        raise TimeoutException(f"Timed out waiting for page elements at Volume {volume}, Issue {issue}")
    
    # Check if the 404 error message is present on the page
    if "Oops! That page can’t be found." in driver.page_source:
        raise InternalServerErrorException(f"Page not found at Volume {volume}, Issue {issue}")
    
    time.sleep(random.randint(2, 4))
        
    # Initialize the list to hold all articles' information
    articles_info = []

    # Find all article entries on the page
    articles = driver.find_elements(By.CSS_SELECTOR, 'div.article-result-container')
    for article in articles:
        # Initialize dictionary to store article details
        article_info = {
            'year': None, 'volume': volume, 'issue': issue,
            'date': None, 'title': None, 'author': None,
            'pages': None, 'doi': None, 'link': None, 'abstract': None
        }

        # Extract the DOI and construct the full DOI link
        doi_element = article.find_element(By.CSS_SELECTOR, '[data-doi]')
        doi_suffix = doi_element.get_attribute('data-doi')
        article_info['doi'] = f"https://doi.org/{doi_suffix}" if doi_suffix else None
        article_info['link'] = article_info['doi']  # Use the DOI URL as the link

        # Extract the title
        title_element = article.find_element(By.CSS_SELECTOR, 'p.has-medium-font-size a')
        article_info['title'] = title_element.text if title_element else None

        # Extract authors if available
        author_element = article.find_element(By.CSS_SELECTOR, 'strong')
        article_info['author'] = author_element.text if author_element else None

        # Extract published date and year
        date_element = article.find_element(By.CSS_SELECTOR, 'p[style*="margin-bottom:1em;"]')
        if date_element:
            date_text = date_element.text
            published_match = re.search(r"Published:\s*(\d+)/(\d+)", date_text)
            if published_match:
                month, year = published_match.groups()
                article_info['date'] = f"{month}/{year}"
                article_info['year'] = year

        # Extract abstract if available
        # The abstract is the paragraph right before the div with class 'wp-block-button'
        button_div = article.find_element(By.CSS_SELECTOR, 'div.wp-block-button.is-style-outline')
        abstract_paragraph = button_div.find_element(By.XPATH, "./preceding-sibling::p[1]")
        article_info['abstract'] = abstract_paragraph.text if abstract_paragraph else None
            
                    
        # Save the article information
        articles_info.append(article_info)

    return articles_info


process_all_journals(1, 79)