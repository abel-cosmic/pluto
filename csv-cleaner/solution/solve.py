import re
import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

def unobfuscate_email(email):
    if pd.isna(email) or str(email).strip() == "" or str(email).lower() == 'nan':
        return ""
    email_str = str(email).strip().lower()
    email_str = email_str.replace('[at]', '@').replace('(at)', '@').replace(' at ', '@').replace('_at_', '@')
    email_str = email_str.replace('[dot]', '.').replace('(dot)', '.').replace(' dot ', '.').replace('_dot_', '.')
    return email_str

def merge_duplicates(df):
    # Trim all string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
            
    # Drop exact duplicate rows (keeping first)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    merged_rows = []
    
    # Process rows top to bottom
    for idx, row in df.iterrows():
        name = str(row['name']).strip()
        email = unobfuscate_email(row['email'])
        
        name_lower = name.lower()
        email_lower = email.lower()
        
        # Check if this matches any already merged row
        found_match = False
        for m_row in merged_rows:
            m_name_lower = str(m_row['name']).strip().lower()
            m_email_lower = unobfuscate_email(m_row['email']).lower()
            
            name_match = (name_lower == m_name_lower and name_lower != "")
            email_match = (email_lower == m_email_lower and email_lower != "")
            
            if name_match or email_match:
                # Merge current row into the matched row!
                # Take first non-null / non-empty value for each column
                for col in df.columns:
                    val = row[col]
                    m_val = m_row[col]
                    
                    is_val_null = pd.isna(val) or str(val).strip() == "" or str(val).lower() == 'nan'
                    is_m_val_null = pd.isna(m_val) or str(m_val).strip() == "" or str(m_val).lower() == 'nan'
                    
                    if is_m_val_null and not is_val_null:
                        m_row[col] = val
                    elif not is_m_val_null and not is_val_null:
                        # Conflict check for age and salary (keep higher value)
                        if col in ['age', 'salary']:
                            try:
                                # Standardize currency/multipliers to numbers for proper comparison if salary
                                v_num = correct_salary(val) if col == 'salary' else float(val)
                                mv_num = correct_salary(m_val) if col == 'salary' else float(m_val)
                                
                                if v_num > mv_num:
                                    m_row[col] = val
                            except:
                                pass
                found_match = True
                break
                
        if not found_match:
            merged_rows.append(dict(row))
            
    return pd.DataFrame(merged_rows)

def clean_name(name):
    if pd.isna(name) or str(name).strip() == "":
        return ""
    name_str = str(name).strip()
    
    # Reverse "Last, First" format
    if ',' in name_str and name_str.count(',') == 1:
        parts = name_str.split(',')
        name_str = parts[1].strip() + ' ' + parts[0].strip()
        
    # Suffixes and prefixes to strip
    prefixes = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sir', 'Mme.']
    suffixes = ['Jr.', 'Sr.', 'III', 'IV', 'Ph.D.', 'PhD', 'MD']
    
    # Remove prefixes from the start (case-insensitive)
    words = name_str.split()
    while words and any(words[0].lower() == p.lower() for p in prefixes):
        words = words[1:]
    
    # Remove suffixes from the end (case-insensitive)
    while words:
        last_word_clean = words[-1].rstrip(',')
        if any(last_word_clean.lower() == s.lower() for s in suffixes):
            words = words[:-1]
        else:
            break
            
    name_str = " ".join(words)
    
    # Remove nicknames in quotes
    name_str = re.sub(r'["\'][^"\']*["\']', '', name_str)
    
    # Remove middle initials
    words = name_str.split()
    words_cleaned = []
    for w in words:
        w_stripped = w.rstrip('.')
        if len(w_stripped) == 1 and w_stripped.isalpha():
            continue
        words_cleaned.append(w)
    name_str = " ".join(words_cleaned)
    
    # Unicode normalisation
    name_str = name_str.replace('æ', 'ae').replace('Æ', 'Ae')
    name_str = name_str.replace('œ', 'oe').replace('Œ', 'Oe')
    name_str = name_str.replace('ß', 'ss')
    
    nfkd_form = unicodedata.normalize('NFKD', name_str)
    name_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Strip extra whitespaces
    name_str = re.sub(r'\s+', ' ', name_str).strip()
    
    # Title Case with preserved particles
    words = name_str.split()
    particles = {'de', 'di', 'van', 'von', 'der', 'du'}
    cased_words = []
    for i, w in enumerate(words):
        w_lower = w.lower()
        if w_lower in particles and i > 0:
            cased_words.append(w_lower)
        else:
            if "'" in w:
                parts = w.split("'")
                cased_words.append("'".join([p.capitalize() for p in parts]))
            else:
                cased_words.append(w.capitalize())
                
    return " ".join(cased_words)

def standardize_dept(row):
    dept = row['department']
    email = str(row['email']).lower()
    
    if pd.isna(dept) or str(dept).strip() == "" or str(dept).lower() == 'nan':
        if any(kw in email for kw in ['tech', 'dev', 'eng']):
            return 'Engineering'
        elif any(kw in email for kw in ['sales', 'deal']):
            return 'Sales'
        elif any(kw in email for kw in ['press', 'ad', 'buzz', 'growth']):
            return 'Marketing'
        else:
            return 'Engineering'
            
    dept_str = str(dept).strip().lower()
    if any(kw in dept_str for kw in ['eng', 'software', 'dev', 'r&d', 'tech', 'engineering']):
        return 'Engineering'
    elif any(kw in dept_str for kw in ['mktg', 'growth', 'pr', 'promo', 'marketing']):
        return 'Marketing'
    elif any(kw in dept_str for kw in ['sls', 'commerce', 'bd', 'sales']):
        return 'Sales'
    elif any(kw in dept_str for kw in ['hr', 'people', 'talent', 'human resources']):
        return 'Human Resources'
        
    return 'Engineering'

def clean_and_resolve_emails(df):
    assigned_emails = set()
    final_emails = []
    
    for idx, row in df.iterrows():
        email = row['email']
        name = row['name']
        
        is_valid = False
        email_str = ""
        
        if not (pd.isna(email) or str(email).strip() == "" or str(email).lower() == 'nan'):
            email_str = str(email).strip().lower()
            email_str = email_str.replace('[at]', '@').replace('(at)', '@').replace(' at ', '@').replace('_at_', '@')
            email_str = email_str.replace('[dot]', '.').replace('(dot)', '.').replace(' dot ', '.').replace('_dot_', '.')
            
            if email_str.count('@') == 1:
                username, domain = email_str.split('@', 1)
                if domain == 'company.com':
                    if re.match(r'^[a-z0-9]+(\.[a-z0-9]+)?$', username):
                        is_valid = True
                        
        if not is_valid:
            words = str(name).split()
            if not words:
                base_username = "temp"
            else:
                first_name = words[0]
                last_name = words[-1]
                prefix = first_name if len(first_name) < 3 else first_name[0]
                base_username = f"{prefix}.{last_name}".lower()
                base_username = re.sub(r'[^a-z0-9.]', '', base_username)
        else:
            base_username = email_str.split('@')[0]
            
        candidate = f"{base_username}@company.com"
        suffix = 2
        while candidate in assigned_emails:
            candidate = f"{base_username}{suffix}@company.com"
            suffix += 1
            
        assigned_emails.add(candidate)
        final_emails.append(candidate)
        
    df['email'] = final_emails

def correct_salary(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == 'nan':
        return np.nan
        
    val_str = str(val).strip()
    val_lower = val_str.lower()
    
    rates = {
        'eur': 1.12, '€': 1.12,
        'gbp': 1.28, '£': 1.28,
        'cad': 0.74, 'c$': 0.74,
        'jpy': 0.0065, '¥': 0.0065,
        'btc': 65000.0, '₿': 65000.0,
        'eth': 3000.0, 'Ξ': 3000.0,
        'usdt': 1.0, '₮': 1.0,
        'usd': 1.0, '$': 1.0
    }
    
    sorted_keys = sorted(rates.keys(), key=len, reverse=True)
    rate = 1.0
    for key in sorted_keys:
        if key in val_lower:
            rate = rates[key]
            break
            
    is_monthly = any(ind in val_lower for ind in ['/month', '/mo', 'monthly', 'per month'])
    num_str = re.sub(r'[^0-9.kK]', '', val_str)
    
    multiply_k = 1.0
    if 'k' in num_str.lower():
        multiply_k = 1000.0
        num_str = re.sub(r'[kK]', '', num_str)
        
    try:
        amount = float(num_str) * multiply_k
        usd_amount = amount * rate
        
        if is_monthly:
            usd_amount *= 12
        elif usd_amount < 15000:
            usd_amount *= 12
            
        if usd_amount < 20000:
            return np.nan
            
        return usd_amount
    except:
        return np.nan

anchor_date = datetime(2026, 5, 20)

def roman_to_int(s):
    roman_dict = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
    res = 0
    for i in range(len(s)):
        if i > 0 and roman_dict[s[i]] > roman_dict[s[i-1]]:
            res += roman_dict[s[i]] - 2 * roman_dict[s[i-1]]
        else:
            res += roman_dict[s[i]]
    return res

def parse_single_date(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "" or str(date_val).lower() == 'nan':
        return None
        
    date_str = str(date_val).strip()
    
    # ISO 8601 with timezone (e.g. 2021-03-15T14:30:00-05:00)
    m_iso = re.match(r'^(\d{4}-\d{2}-\d{2})(T[\d:]+(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$', date_str)
    if m_iso:
        return m_iso.group(1)
        
    # Hex timestamp
    if date_str.lower().startswith('0x'):
        try:
            ts = int(date_str, 16)
            if ts > 1e11:
                ts = ts / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        except:
            pass
            
    # Unix timestamp
    if re.match(r'^\d{9,10}$', date_str):
        try:
            ts = int(date_str)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        except:
            pass
            
    # Excel serial date
    if re.match(r'^\d{5}$', date_str):
        try:
            days = int(date_str)
            dt = datetime(1899, 12, 30) + timedelta(days=days)
            return dt.strftime('%Y-%m-%d')
        except:
            pass
            
    # Quarters: Q2 2020 or 2020-Q2
    m_q1 = re.match(r'^(\d{4})-Q([1-4])$', date_str, re.IGNORECASE)
    if m_q1:
        year = int(m_q1.group(1))
        q = int(m_q1.group(2))
        month = {1: 1, 2: 4, 3: 7, 4: 10}[q]
        return f"{year:04d}-{month:02d}-01"
    m_q2 = re.match(r'^Q([1-4])\s+(\d{4})$', date_str, re.IGNORECASE)
    if m_q2:
        year = int(m_q2.group(2))
        q = int(m_q2.group(1))
        month = {1: 1, 2: 4, 3: 7, 4: 10}[q]
        return f"{year:04d}-{month:02d}-01"
        
    # Relative dates
    m_rel = re.match(r'^(\d+)\s+(year|month|day)s?\s+ago$', date_str, re.IGNORECASE)
    if m_rel:
        num = int(m_rel.group(1))
        unit = m_rel.group(2).lower()
        if unit == 'day':
            dt = anchor_date - timedelta(days=num)
        elif unit == 'month':
            month = anchor_date.month - num
            year = anchor_date.year
            while month <= 0:
                month += 12
                year -= 1
            dt = anchor_date.replace(year=year, month=month)
        elif unit == 'year':
            dt = anchor_date.replace(year=anchor_date.year - num)
        return dt.strftime('%Y-%m-%d')
        
    # Roman numeral month
    m_roman = re.match(r'^(\d{1,2})[-/]([IVXLCDM]+)[-/](\d{2,4})$', date_str, re.IGNORECASE)
    if m_roman:
        try:
            day = int(m_roman.group(1))
            month = roman_to_int(m_roman.group(2).upper())
            year_str = m_roman.group(3)
            if len(year_str) == 2:
                yy = int(year_str)
                year = 2000 + yy if yy < 30 else 1900 + yy
            else:
                year = int(year_str)
            dt = datetime(year, month, day)
            return dt.strftime('%Y-%m-%d')
        except:
            pass

    # Written out dates
    for fmt in ('%B %d %Y', '%B %d, %Y', '%b %d %Y', '%b %d, %Y', '%d-%B-%Y', '%d-%b-%Y'):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
            
    for fmt in ('%B %Y', '%b %Y'):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-01')
        except ValueError:
            pass
            
    try:
        dt = datetime.strptime(date_str, '%Y/%m/%d')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    try:
        dt = datetime.strptime(date_str, '%d/%m/%y')
        parts = date_str.split('/')
        yy = int(parts[2])
        year = 2000 + yy if yy < 30 else 1900 + yy
        dt = dt.replace(year=year)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    try:
        dt = datetime.strptime(date_str, '%d-%m-%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    return None

def parse_and_impute_dates(df):
    parsed_dates = df['join_date'].apply(parse_single_date)
    
    # Calculate Unix timestamps for aggregation
    unix_ts = []
    for d in parsed_dates:
        if d is not None:
            dt = datetime.strptime(d, '%Y-%m-%d')
            unix_ts.append(dt.timestamp())
        else:
            unix_ts.append(np.nan)
            
    df['temp_unix_date'] = unix_ts
    
    dept_median_ts = df.groupby('department')['temp_unix_date'].median()
    company_median_ts = df['temp_unix_date'].median()
    
    final_dates = []
    for idx, row in df.iterrows():
        p_date = parsed_dates.iloc[len(final_dates)]
        if p_date is not None:
            final_dates.append(p_date)
        else:
            dept = row['department']
            ts = dept_median_ts.get(dept, np.nan)
            if pd.isna(ts):
                ts = company_median_ts
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            final_dates.append(dt.strftime('%Y-%m-%d'))
            
    df['join_date'] = final_dates
    df.drop(columns=['temp_unix_date'], inplace=True)

def get_year_from_date(date_str):
    try:
        return int(date_str.split('-')[0])
    except:
        return np.nan

def impute_missing_metrics(df):
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df['salary'] = pd.to_numeric(df['salary'], errors='coerce')
    
    # Aggregates
    dept_decade_age = df.groupby(['department', 'decade'])['age'].median()
    company_decade_age = df.groupby('decade')['age'].median()
    dept_overall_age = df.groupby('department')['age'].median()
    company_overall_age = df['age'].median()
    
    dept_decade_age_count = df.groupby(['department', 'decade'])['age'].count()
    
    dept_decade_sal = df.groupby(['department', 'decade'])['salary'].median()
    company_decade_sal = df.groupby('decade')['salary'].median()
    dept_overall_sal = df.groupby('department')['salary'].median()
    company_overall_sal = df['salary'].median()
    
    dept_decade_sal_count = df.groupby(['department', 'decade'])['salary'].count()
    
    # Impute ages
    imputed_ages = []
    for idx, row in df.iterrows():
        age = row['age']
        if not pd.isna(age):
            imputed_ages.append(round(age))
            continue
            
        dept = row['department']
        dec = row['decade']
        
        if pd.isna(dec):
            val = dept_overall_age.get(dept, company_overall_age)
            imputed_ages.append(round(val))
            continue
            
        count = dept_decade_age_count.get((dept, dec), 0)
        if count >= 3:
            val = dept_decade_age.get((dept, dec))
        else:
            m1 = dept_decade_age.get((dept, dec), np.nan)
            if pd.isna(m1):
                m1 = dept_overall_age.get(dept, company_overall_age)
            m2 = company_decade_age.get(dec, np.nan)
            if pd.isna(m2):
                m2 = company_overall_age
            m3 = dept_overall_age.get(dept, company_overall_age)
            
            val = 0.5 * m1 + 0.3 * m2 + 0.2 * m3
            
        imputed_ages.append(round(val))
        
    # Impute salaries
    imputed_salaries = []
    for idx, row in df.iterrows():
        sal = row['salary']
        if not pd.isna(sal):
            imputed_salaries.append(round(sal))
            continue
            
        dept = row['department']
        dec = row['decade']
        
        if pd.isna(dec):
            val = dept_overall_sal.get(dept, company_overall_sal)
            imputed_salaries.append(round(val))
            continue
            
        count = dept_decade_sal_count.get((dept, dec), 0)
        if count >= 3:
            val = dept_decade_sal.get((dept, dec))
        else:
            m1 = dept_decade_sal.get((dept, dec), np.nan)
            if pd.isna(m1):
                m1 = dept_overall_sal.get(dept, company_overall_sal)
            m2 = company_decade_sal.get(dec, np.nan)
            if pd.isna(m2):
                m2 = company_overall_sal
            m3 = dept_overall_sal.get(dept, company_overall_sal)
            
            val = 0.5 * m1 + 0.3 * m2 + 0.2 * m3
            
        imputed_salaries.append(round(val))
        
    df['age'] = imputed_ages
    df['salary'] = imputed_salaries

def is_valid_row(row):
    name = str(row['name'])
    age = row['age']
    salary = row['salary']
    email = str(row['email'])
    join_date = str(row['join_date'])
    
    # Name checks
    letters = re.sub(r'[^a-zA-Z]', '', name)
    if len(letters) < 3:
        return False
    if any(c.isdigit() for c in name):
        return False
    if not re.match(r"^[a-zA-Z\s.'-]+$", name):
        return False
        
    # Age checks
    if pd.isna(age) or age < 18 or age > 65:
        return False
        
    # Salary checks
    if pd.isna(salary) or salary < 24000 or salary > 200000:
        return False
        
    # Email checks
    if not email.endswith('@company.com'):
        return False
    username = email.split('@')[0]
    if username.count('.') > 1:
        return False
        
    # Join Age Sanity check (joined age >= 18)
    try:
        join_year = int(join_date.split('-')[0])
        birth_year = 2026 - age
        if join_year - birth_year < 18:
            return False
    except:
        return False
        
    return True

def main():
    filepath = '/app/data/employees.csv'
    df = pd.read_csv(filepath)
    
    # 1. Merge Near-Duplicates & Remove Exact Duplicates
    df = merge_duplicates(df)
    
    # 2. Normalize Names
    df['name'] = df['name'].apply(clean_name)
    
    # 3. Standardize Departments
    df['department'] = df.apply(standardize_dept, axis=1)
    
    # 4. Email Recovery, Validation & Stateful Collision Resolution
    clean_and_resolve_emails(df)
    
    # 5. Convert Salaries (including Crypto)
    df['salary'] = df['salary'].apply(correct_salary)
    
    # 7. Parse and Standardize Join Dates
    parse_and_impute_dates(df)
    
    # Set decades temporarily for Aggregated Imputations
    df['year'] = df['join_date'].apply(get_year_from_date)
    df['decade'] = df['year'].apply(lambda y: np.nan if pd.isna(y) else int(10 * (y // 10)))
    
    # 6. Blended Aggregated Imputations
    impute_missing_metrics(df)
    
    # 8. Anomaly Filtering
    df = df[df.apply(is_valid_row, axis=1)]
    
    # 9. Type Casting
    df['age'] = df['age'].astype(np.int64)
    df['salary'] = df['salary'].astype(np.int64)
    
    # 10. Add SHA-256 Row Hash
    def compute_hash(row):
        name = str(row['name']).strip()
        email = str(row['email']).strip()
        age = int(row['age'])
        salary = int(row['salary'])
        dept = str(row['department']).strip()
        date = str(row['join_date']).strip()
        
        hash_str = f"{dept}|{date}|{email}|{age}|{salary}|{name}"
        return hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
        
    df['row_hash'] = df.apply(compute_hash, axis=1)
    
    # Keep only target columns
    df = df[['name', 'email', 'age', 'salary', 'department', 'join_date', 'row_hash']]
    
    # Save back to CSV in place
    df.to_csv(filepath, index=False)

if __name__ == '__main__':
    main()
