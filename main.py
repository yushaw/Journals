from financial_economics import volume
from financial_economics import article
import csv

# 使用函数获取结果
bare_href = "https://www.sciencedirect.com"
base_href = "https://www.sciencedirect.com/journal/journal-of-financial-economics/issues"
volume_results = volume.get_volume_issue(base_href)

# 创建一个 csv 文件并写入数据
with open('articles.csv', 'w', newline='', encoding='utf-8') as file:
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
