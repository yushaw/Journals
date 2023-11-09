from financial_economics import volume as fe
import review_of_financial_studies.volume as rfs
import journal_of_finance.volume as jf

# 生成 review_of_financial_studies.csv 文件
rfs.process_all_journals(1, 36)

# 生成 journal_of_finance.csv 文件
jf.process_all_journals(1, 76)

# 生成 financial economics 文件
fe.process_all_journals()
