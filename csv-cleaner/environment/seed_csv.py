import os

DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Create a dirty CSV file with various advanced data quality issues
DIRTY_CSV = """name,email,age,salary,department,join_date
John Smith,john.smith@example.com,30,$50000,Eng,2021-03-15T14:30:00-05:00
Jane Doe,jane[at]example.com,,€60000,Marketing,12/04/2020
John Smith,john.smith@example.com,30,$50000,Eng,2021-03-15T14:30:00-05:00
  Alice Williams  ,,28,£4.5k/month,Sales,2022-11-01
Charlie Brown,charlie.b@company.com,42,65000,software engineering,May 14 2018
Diana Prince,diana.prince@company.com,31,€48k,Mktg,Q2 2020
Eve Davis,eve.davis(at)company.com,,$52000,Sales,44195
Prof. Frank Miller,frank.miller at company dot com,45,70000,Engineering,15-VI-2017
Grace Lee,grace.lee@company.com,29,,Growth,18 months ago
Grace Lee,,29,48000,,
Henry Wilson,henry.w@company.com,38,£62000,Sls,05/XII/18
Ivy Chen,ivy.chen@company.com,33,,Eng,2022-04-12
Jack White,jack.white_at_company_dot_com,40,12 ETH,Marketing,2020-10-22
Dr. Renée du Pont,renee_dupont@example.com,50,C$81k,Engineering,2022-01-01
LUDWIG VAN BEETHOVEN,,56,0.15 BTC/mo,Eng,2019-05-10
"O'Connor, Caitlin",,,62000,Sales,2023-08-12
Jack Smith,,25,$45000,Eng,2024-01-15
Julia Smith,,35,$55000,Sales,2025-02-15
Arthur Pendragon,,,,Sales,2015-05-12
Young Joiner,young.joiner@company.com,20,35000,Engineering,2018-05-10
Trash Row,,999,999999,Eng,2021-03-15
Bad Name 123,bad.name@company.com,25,45000,Sales,2021-03-15
Ab,,22,35000,Marketing,2021-03-15
"""

with open(f"{DATA_DIR}/employees.csv", "w", encoding="utf-8") as f:
    f.write(DIRTY_CSV)
