import pandas as pd
import pytest
import re
import hashlib

def load():
    return pd.read_csv("/app/data/employees.csv")

def test_correct_row_count():
    df = load()
    # The output should have exactly 17 rows
    assert len(df) == 17

def test_no_duplicates_or_missing_values():
    df = load()
    assert df.duplicated().sum() == 0
    assert df.isna().sum().sum() == 0

def test_type_casting():
    df = load()
    assert df['age'].dtype == 'int64'
    assert df['salary'].dtype == 'int64'
    assert pd.api.types.is_string_dtype(df['join_date'])
    assert pd.api.types.is_string_dtype(df['name'])
    assert pd.api.types.is_string_dtype(df['email'])
    assert pd.api.types.is_string_dtype(df['department'])
    assert pd.api.types.is_string_dtype(df['row_hash'])

def test_departments_standardized():
    df = load()
    departments = df['department'].unique()
    assert len(departments) == 3
    assert set(departments) == {'Engineering', 'Marketing', 'Sales'}

def test_near_duplicate_merging():
    df = load()
    
    # Grace Lee has two input rows:
    # 1. Grace Lee,grace.lee@company.com,29,,Growth,18 months ago
    # 2. Grace Lee,,29,48000,,
    # They should merge into one row with all info present
    grace = df[df['name'] == 'Grace Lee']
    assert len(grace) == 1
    assert grace.iloc[0]['email'] == 'grace.lee@company.com'
    assert grace.iloc[0]['age'] == 29
    assert grace.iloc[0]['salary'] == 48000
    assert grace.iloc[0]['department'] == 'Marketing'
    assert grace.iloc[0]['join_date'] == '2024-11-20'

def test_name_normalization_and_particles():
    df = load()
    
    # Renee du Pont: Dr. Renée du Pont -> Renee du Pont (retains lowercase 'du')
    renee = df[df['name'] == 'Renee du Pont']
    assert len(renee) == 1
    
    # Ludwig van Beethoven: LUDWIG VAN BEETHOVEN -> Ludwig van Beethoven (retains lowercase 'van')
    ludwig = df[df['name'] == 'Ludwig van Beethoven']
    assert len(ludwig) == 1

    # Caitlin O'Connor: reversed from "O'Connor, Caitlin"
    caitlin = df[df['name'] == "Caitlin O'Connor"]
    assert len(caitlin) == 1

    # Charlie Brown: Charlie Brown
    charlie = df[df['name'] == 'Charlie Brown']
    assert len(charlie) == 1

    # Verify no professional prefixes or suffixes left in any name
    for name in df['name']:
        assert 'Dr.' not in name
        assert 'Mr.' not in name
        assert 'Mrs.' not in name
        assert 'Ms.' not in name
        assert 'Prof.' not in name
        assert 'Sir' not in name
        assert 'Mme.' not in name
        assert 'Jr.' not in name
        assert 'Sr.' not in name
        assert 'III' not in name
        assert 'IV' not in name
        assert 'Ph.D.' not in name
        assert 'PhD' not in name
        assert 'MD' not in name
        assert '  ' not in name
        assert name == name.strip()

def test_email_collision_resolution():
    df = load()
    
    # John Smith gets first initial + last name -> j.smith@company.com
    john = df[df['name'] == 'John Smith']
    assert len(john) == 1
    assert john.iloc[0]['email'] == 'j.smith@company.com'

    # Jack Smith (Row 16) conflicts with John, resolves to j.smith2@company.com
    jack_smith = df[df['name'] == 'Jack Smith']
    assert len(jack_smith) == 1
    assert jack_smith.iloc[0]['email'] == 'j.smith2@company.com'

    # Julia Smith (Row 17) conflicts with John and Jack, resolves to j.smith3@company.com
    julia_smith = df[df['name'] == 'Julia Smith']
    assert len(julia_smith) == 1
    assert julia_smith.iloc[0]['email'] == 'j.smith3@company.com'

    # Check all emails are valid
    for email in df['email']:
        assert email.endswith('@company.com')
        assert email.count('@') == 1
        username = email.split('@')[0]
        # Username can contain a digit at the end due to collision resolution
        assert re.match(r'^[a-z0-9.]+$', username)
        assert username.count('.') <= 1
        assert not username.startswith('.')
        assert not username.endswith('.')
        assert '..' not in username

def test_salary_crypto_and_currency_conversions():
    df = load()

    # Alice Williams: £4.5k/month -> GBP 1.28 -> 4500 * 1.28 = 5760 * 12 = 69120
    alice = df[df['name'] == 'Alice Williams']
    assert len(alice) == 1
    assert alice.iloc[0]['salary'] == 69120

    # Diana Prince: €48k -> EUR 1.12 -> 48000 * 1.12 = 53760
    diana = df[df['name'] == 'Diana Prince']
    assert len(diana) == 1
    assert diana.iloc[0]['salary'] == 53760

    # Renee du Pont: C$81k -> CAD 0.74 -> 81000 * 0.74 = 59940
    renee = df[df['name'] == 'Renee du Pont']
    assert len(renee) == 1
    assert renee.iloc[0]['salary'] == 59940

    # Jack White: 12 ETH -> ETH 3000 -> 12 * 3000 = 36000 USD
    jack = df[df['name'] == 'Jack White']
    assert len(jack) == 1
    assert jack.iloc[0]['salary'] == 36000

    # Ludwig van Beethoven: 0.15 BTC/mo -> BTC 65000 -> 0.15 * 65000 = 9750 * 12 = 117000
    ludwig = df[df['name'] == 'Ludwig van Beethoven']
    assert len(ludwig) == 1
    assert ludwig.iloc[0]['salary'] == 117000

def test_date_parsers_and_imputations():
    df = load()
    date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    # John Smith: ISO 8601 with timezone -> 2021-03-15
    john = df[df['name'] == 'John Smith']
    assert len(john) == 1
    assert john.iloc[0]['join_date'] == '2021-03-15'

    # Jane Doe: Slash-separated DD/MM/YYYY -> 2020-04-12
    jane = df[df['name'] == 'Jane Doe']
    assert len(jane) == 1
    assert jane.iloc[0]['join_date'] == '2020-04-12'

    # Eve Davis: Excel serial number 44195 -> 2020-12-30
    eve = df[df['name'] == 'Eve Davis']
    assert len(eve) == 1
    assert eve.iloc[0]['join_date'] == '2020-12-30'

    # Frank Miller: Roman numeral month 15-VI-2017 -> 2017-06-15
    frank = df[df['name'] == 'Frank Miller']
    assert len(frank) == 1
    assert frank.iloc[0]['join_date'] == '2017-06-15'

    # Henry Wilson: Roman numeral month 05/XII/18 -> 2018-12-05
    henry = df[df['name'] == 'Henry Wilson']
    assert len(henry) == 1
    assert henry.iloc[0]['join_date'] == '2018-12-05'

    # Grace Lee: "18 months ago" relative to 2026-05-20 -> 2024-11-20
    grace = df[df['name'] == 'Grace Lee']
    assert len(grace) == 1
    assert grace.iloc[0]['join_date'] == '2024-11-20'

    for date in df['join_date']:
        assert date_regex.match(str(date)) is not None

def test_blended_and_simple_imputation():
    df = load()

    # Jane Doe (Marketing, 2020s): imputed using simple group median
    # Marketing 2020s ages: Diana Prince (31), Grace Lee (29), Jack White (40), Ab (22) -> count is 4 >= 3
    # Group median of [22, 29, 31, 40] = 30.0 -> rounded to 30
    jane = df[df['name'] == 'Jane Doe']
    assert len(jane) == 1
    assert jane.iloc[0]['age'] == 30

    # Eve Davis (Sales, 2020s): imputed using simple group median
    # Sales 2020s ages: Alice (28), Bad Name 123 (25), Julia Smith (35) -> count is 3 >= 3
    # Group median of [25, 28, 35] = 28.0 -> rounded to 28
    eve = df[df['name'] == 'Eve Davis']
    assert len(eve) == 1
    assert eve.iloc[0]['age'] == 28

    # Arthur Pendragon (Sales, 2010s): both age and salary imputed using blended formula
    # For Sales 2010s: only Henry Wilson (age 38, salary 79360) -> group count = 1 < 3 (triggers blending)
    # Arthur's Age Blend:
    #   - dept-decade median (Sales 2010s): 38.0
    #   - company-wide decade median (2010s): Charlie (42), Frank (45), Henry (38), Ludwig (56), Young Joiner (20) -> median is 42.0
    #   - dept-wide overall median (Sales): Alice (28), Henry (38), Julia (35), Bad Name 123 (25) -> median is 31.5
    #   Blend: 0.5 * 38 + 0.3 * 42 + 0.2 * 31.5 = 19 + 12.6 + 6.3 = 37.9 -> rounds to 38
    # Arthur's Salary Blend:
    #   - dept-decade median (Sales 2010s): 79360.0
    #   - company-wide decade median (2010s): Charlie (65000), Frank (70000), Henry (79360), Ludwig (117000), Young Joiner (35000) -> median is 70000.0
    #   - dept-wide overall median (Sales): Alice (69120), Eve (52000), Henry (79360), Caitlin (62000), Julia (55000), Bad Name 123 (45000) -> median is 58500.0
    #   Blend: 0.5 * 79360 + 0.3 * 70000 + 0.2 * 58500 = 39680 + 21000 + 11700 = 72380 -> rounds to 72380
    arthur = df[df['name'] == 'Arthur Pendragon']
    assert len(arthur) == 1
    assert arthur.iloc[0]['age'] == 38
    assert arthur.iloc[0]['salary'] == 72380

def test_anomaly_filtering():
    df = load()

    # Trash Row (age 999, salary 999999) filtered out
    assert len(df[df['name'].str.contains('Trash Row', na=False)]) == 0
    # Bad Name 123 (contains digits) filtered out
    assert len(df[df['name'].str.contains('Bad Name', na=False)]) == 0
    # Ab (name length < 3 letters) filtered out
    assert len(df[df['name'] == 'Ab']) == 0
    # Young Joiner (joined at age 12, which is < 18) filtered out
    assert len(df[df['name'] == 'Young Joiner']) == 0

def test_row_hashes():
    df = load()
    assert 'row_hash' in df.columns
    
    for idx, row in df.iterrows():
        name = str(row['name']).strip()
        email = str(row['email']).strip()
        age = int(row['age'])
        salary = int(row['salary'])
        dept = str(row['department']).strip()
        date = str(row['join_date']).strip()
        
        hash_str = f"{dept}|{date}|{email}|{age}|{salary}|{name}"
        expected_hash = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
        assert row['row_hash'] == expected_hash
