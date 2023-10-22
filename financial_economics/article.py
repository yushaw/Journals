from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def get_articles(url):
    # 启动Selenium
    driver = webdriver.Chrome()
    driver.implicitly_wait(2)

    driver.get(url)

    driver.implicitly_wait(3)

    # 点击按钮展示全部摘要
    try:
        driver.execute_script('document.querySelector("input.js-previews-switch").click();')
    except Exception as e:
        print("Error while clicking button using JS:", e)

    time.sleep(3)

    # 获取所有文章项
    articles = driver.find_elements(By.CSS_SELECTOR, "li.js-article-list-item")

    results = []

    for article in articles:
        
        # 获取其他文章信息
        try:
            abstract = article.find_element(By.CSS_SELECTOR, "div.js-abstract-body-text p").text
        except:
            abstract = None

        try:
            article_type = article.find_element(By.CSS_SELECTOR, "span.js-article-subtype").text
        except:
            article_type = None

        try:
            title = article.find_element(By.CSS_SELECTOR, "span.js-article-title").text
        except:
            title = None

        try:
            author = article.find_element(By.CSS_SELECTOR, "div.js-article__item__authors").text
        except:
            author = None

        try:
            doi = article.find_element(By.CSS_SELECTOR, "div[hidden]").get_attribute('textContent')
        except:
            doi = None

        try:
            link = article.find_element(By.CSS_SELECTOR, "a.anchor.article-content-title").get_attribute("href")
        except:
            link = None

        try:
            page_article_no = article.find_element(By.CSS_SELECTOR, "dd.js-article-page-range").text
        except:
            page_article_no = None

        article_data = {
            "Type": article_type,
            "Title": title,
            "Author": author,
            "DOI": doi,
            "Link": link,
            "Page/Article No": page_article_no,
            "Abstract": abstract,
        }

        results.append(article_data)
    driver.close()

    return results