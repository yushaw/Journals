from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import article
import time
import re

# 使用函数获取结果
bare_href = "https://www.sciencedirect.com"
base_href = "https://www.sciencedirect.com/journal/journal-of-financial-economics/issues"

def process_all_journals():
    volume_results = get_volume_issue(base_href)
    # 创建一个 csv 文件并写入数据
    with open('financial_economics.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入表头
        writer.writerow(['year', 'volume', 'issue', 'date', 'title', 'author', 'page/article no', 'doi', 'link', 'abstract'])
        
        # 遍历 volume_results 获取每个 volume 和 issue 的信息
        for volume_issue in volume_results:
            year = volume_issue[0]
            volume_num = volume_issue[1]
            issue = volume_issue[2]
            date = volume_issue[3]
            issue_url = bare_href + volume_issue[5]  # 假设是完整的 URL，如果不是请加上基础 URL
            
            # 使用 get_articles 函数获取文章列表
            articles = article.get_articles(issue_url)
            for item in articles:
                writer.writerow([
                    year, volume_num, issue, date,
                    item['Title'], item['Author'], item['Page/Article No'], item['DOI'], item['Link'], item['Abstract']
                ])


def get_volume_issue(base_href):
    driver = webdriver.Chrome()
    driver.implicitly_wait(2)

    results = []

    # 循环处理三个链接
    for page in range(1, 4):
        href = base_href + f"?page={page}"
        driver.get(href)
        driver.implicitly_wait(4)

        buttons = driver.find_elements(By.CSS_SELECTOR, "li.accordion-panel > button")    

        for button in buttons:
            if button.get_attribute("aria-expanded") == "false":
                driver.execute_script("arguments[0].click();", button)
                time.sleep(2)

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                for accordion_panel in soup.find_all("li", class_="accordion-panel"):
                    year_text = accordion_panel.find("span", class_="accordion-title").text
                    year = year_text.split('—')[0].strip()

                    for issue in accordion_panel.find_all("div", class_="issue-item"):
                        issue_link = issue.find("a", class_="js-issue-item-link")

                        match = re.match(r"Volume (\d+), (.+)", issue_link.text.strip())
                        if match:
                            volume = "Volume " + match.group(1)
                            issue_number = match.group(2)
                        else:
                            continue

                        href = issue_link['href']

                        status = issue.find("h3", class_="js-issue-status").text
                        pages, date = status.split(" (")
                        date = date.rstrip(")")

                        results.append((year, volume, issue_number, date, pages, href))
        print(f"第{page}页处理完毕, 共找到{len(results)}个结果")

    driver.close()

    # 去掉重复的项
    unique_results = list(set(results))

    print(f"共找到{len(unique_results)}个结果")
    return unique_results