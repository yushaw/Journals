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
                    with open('review_of_financial_studies.csv', 'a', newline='', encoding='utf-8') as file:
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
    base_url = f"https://academic.oup.com/rfs/issue/{volume}/{issue}"
    driver.get(base_url)
    
    # Wait for the articles list to load
    try:
        WebDriverWait(driver, 40).until(
            lambda d: d.find_elements(By.ID, "ArticleList") or d.find_elements(By.CLASS_NAME, "error-title")
        )
    except TimeoutException:
        # If neither element is found within the timeout period, raise an exception
        raise TimeoutException("Timed out waiting for page elements.")    
    if "Internal Server Error" in driver.page_source:
        raise InternalServerErrorException(f"Internal Server Error at Volume {volume}, Issue {issue}")
    
    # 检查是否存在内部服务器错误
    error_elements = driver.find_elements(By.CLASS_NAME, "error-title")
    if error_elements and any("Internal Server Error" in elem.text for elem in error_elements):
        raise InternalServerErrorException(f"Internal Server Error at Volume {volume}, Issue {issue}")
    
    # Find all articles using Selenium
    selenium_articles = driver.find_elements(By.CSS_SELECTOR, 'div.al-article-items')
    
    # Click all "Extract" or "Abstract" buttons to reveal the abstracts
    for selenium_article in selenium_articles:
        try:
            # Extract data-articleid attribute
            article_id = selenium_article.get_attribute('data-articleid')

            # Find and click the abstract button
            abstract_button = selenium_article.find_element(By.CSS_SELECTOR, ".showAbstractLink.js-show-abstract")
            driver.execute_script("arguments[0].click();", abstract_button)
            # Wait for the abstract to load after click if necessary
            # WebDriverWait(driver, 10).until(...)
            # Wait for the abstract to load after click
            time_to_wait = random.randint(3, 5)
            time.sleep(time_to_wait)    
            
        except NoSuchElementException:
            print(f"Abstract button not found for article {article_id}")
    
    
    time_to_wait = random.randint(3, 5)
    time.sleep(time_to_wait)    
    # Now that the dynamic content has loaded, we can pass the page source to BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Initialize the list to hold all articles' information
    articles_info = []

    # Find all article entries on the page
    articles = soup.find_all('div', class_='al-article-items')
    for article in articles:
        # Initialize dictionary to store article details
        article_info = {
            'year': None, 'volume': volume, 'issue': issue,
            'date': None, 'title': None, 'author': None,
            'page/article_no': None, 'doi': None, 'link': None, 'abstract': None
        }
        
        # Extract the abstract text
        if 'data-articleid' in article.attrs:
            article_id = article['data-articleid']
            abstract_div = soup.find('div', id=f'abstract-{article_id}')
            if abstract_div:
                article_info['abstract'] = abstract_div.get_text(strip=True).strip('"')
    
        # Check if the title exists and get its text
        title_element = article.find('a', class_='at-articleLink')
        if title_element:
            article_info['title'] = title_element.get_text(strip=True)

        # Check if the author exists and get its text
        author_element = article.find('div', class_='al-authors-list')
        if author_element:
            article_info['author'] = author_element.get_text(strip=True)

        # Check if the link exists and construct the full URL
        link_element = article.find('a', class_='at-articleLink')
        if link_element and link_element.get('href'):
            article_info['link'] = base_url + link_element['href']
        
        # Extract details from the issue-info-date
        issue_info = soup.find('div', class_='issue-info-text')
        if issue_info:
            date_info = issue_info.find('div', class_='issue-info-date')
            if date_info:
                article_info['date'] = date_info.get_text(strip=True)
                # Assuming the year is always at the end of the date string
                article_info['year'] = date_info.get_text(strip=True).split()[-1]
        
        # Extract the publication history details for page/article no and doi
        pub_history = article.find('div', class_='pub-history-row')
        if pub_history:
            # Use regex to find the DOI
            doi_match = re.search(r"https://doi\.org/10\.1093/rfs/(.+)", pub_history.get_text())
            if doi_match:
                article_info['doi'] = doi_match.group()

            # Use regex to find the Pages
            pages_match = re.search(r"Pages\s+(\d+–\d+|\d+)", pub_history.get_text())
            if pages_match:
                article_info['page/article_no'] = pages_match.group(1)

        
        # Save the article information
        articles_info.append(article_info)

    # Return all articles' information
    return articles_info

process_all_journals(1, 37)