Write a python script to clean /app/data/employees.csv and overwrite the file. The output should contain exactly 17 rows and these columns: `name, email, age, salary, department, join_date, row_hash` Age/salary: int64 Dates: string, format YYYY-MM-DD Save without index.

Tasks consist of:

Trim whitespace, eliminate duplicates, combine near-duplicates
* Normalize names, departments, emails, salaries, dates
* Convert to USD and annualize monthly compensation
 * Generate valid `@company.com` emails when missing/invalid 
* Fill missing ages/salaries with department/decade medians
Parsing multiple date formats and inferring invalid dates
* Filter out invalid records based on name, age, salary, email and join age rules
Generate SHA256 `row_hash` of final cleaned fields.