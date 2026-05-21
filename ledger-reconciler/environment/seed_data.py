import json
import os

transactions = [
    {
        "id": "txn_001", "user_id": "USER_01", "raw_name": "Smith, John",
        "email": "j.smith[at]company.com", "amount": "150.00", "currency": "USD",
        "fee_usd": 2.50, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "2021-03-15T14:30:00-05:00"
    },
    {
        "id": "txn_001", "user_id": "USER_01", "raw_name": "Smith, John",
        "email": "j.smith[at]company.com", "amount": "150.00", "currency": "USD",
        "fee_usd": 2.50, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "2021-03-15T14:30:00-05:00"
    },
    {
        "id": "txn_001_dup", "user_id": "user_01", "raw_name": "John Smith",
        "email": "j.smith@company.com", "amount": 150.00, "currency": "USD",
        "fee_usd": 2.50, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "2021-03-15T14:30:02-05:00"
    },
    {
        "id": "txn_002", "user_id": "USR2", "raw_name": "Dr. Ren\u00e9e du Pont MD",
        "email": "r.pont_at_company.com", "amount": 100.00, "currency": "EUR",
        "fee_usd": None, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "1609372800"
    },
    {
        "id": "txn_003", "user_id": "U-100", "raw_name": 'William "Bill" Gates',
        "email": "william_dot_gates@company.com", "amount": 50.00, "currency": "GBP",
        "fee_usd": 1.00, "merchant_dept": "Sales", "type": "payment",
        "status": "pending", "timestamp": "0x616F6000"
    },
    {
        "id": "ref_001", "user_id": "U-100", "raw_name": "William Gates",
        "email": "w.gates@company.com", "amount": 50.00, "currency": "GBP",
        "fee_usd": 0.50, "merchant_dept": "Sales", "type": "refund", "parent_id": "txn_003",
        "status": "pending", "timestamp": "44488.5"
    },
    {
        "id": "txn_004", "user_id": "ABC9", "raw_name": "ludwig van beethoven",
        "email": None, "amount": 0.05, "currency": "BTC",
        "fee_usd": 15.00, "merchant_dept": "Marketing", "type": "payment",
        "status": "pending", "timestamp": "2023-01-01T10:00:00Z"
    },
    {
        "id": "ref_002", "user_id": "ABC9", "raw_name": "Ludwig Van Beethoven",
        "email": "invalid.email@other.com", "amount": 1000.00, "currency": "USD",
        "fee_usd": 5.00, "merchant_dept": "Marketing", "type": "refund", "parent_id": "txn_004",
        "status": "pending", "timestamp": "2 days ago"
    },
    {
        "id": "txn_005", "user_id": "u-tiny", "raw_name": "Tiny Tim",
        "email": "t.tim@company.com", "amount": 2.00, "currency": "USD",
        "fee_usd": 0.10, "merchant_dept": "HR", "type": "payment",
        "status": "pending", "timestamp": "2022-05-01T00:00:00Z"
    },
    {
        "id": "txn_006", "user_id": "u-old", "raw_name": "Old Guy",
        "email": "old@company.com", "amount": 100.00, "currency": "USD",
        "fee_usd": 1.00, "merchant_dept": "HR", "type": "payment",
        "status": "pending", "timestamp": "2019-12-31T23:59:59Z"
    },
    {
        "id": "ref_003", "user_id": "ghost", "raw_name": "Ghost Refund",
        "email": "ghost@company.com", "amount": 50.00, "currency": "USD",
        "fee_usd": 0.00, "merchant_dept": "Sales", "type": "refund", "parent_id": "txn_ghost",
        "status": "pending", "timestamp": "2023-05-01T00:00:00Z"
    },
    {
        "id": "txn_007", "user_id": "USER_02", "raw_name": "Jane Smith",
        "email": "j.smith@company.com", "amount": 250.00, "currency": "USD",
        "fee_usd": 3.00, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "2021-04-10T10:00:00Z"
    },
    {
        "id": "txn_008", "user_id": "HR_01", "raw_name": "Alice L. Wonderland",
        "email": "alice(at)company.com", "amount": 1.5, "currency": "kUSD",
        "fee_usd": None, "merchant_dept": "HR", "type": "payment",
        "status": "pending", "timestamp": "2024-06-01T12:00:00Z"
    },
    {
        "id": "txn_009", "user_id": "HR_02", "raw_name": "Bob Builder",
        "email": "b.builder@company.com", "amount": 500.00, "currency": "USD",
        "fee_usd": 10.00, "merchant_dept": "HR", "type": "payment",
        "status": "pending", "timestamp": "Unknown Date"
    },
    {
        "id": "txn_010", "user_id": "ETH_01", "raw_name": 'Charlie "Crypto" Chain',
        "email": "c.chain@company.com", "amount": 0.1, "currency": "ETH",
        "fee_usd": 12.00, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "1680307200"
    },
    {
        "id": "txn_011", "user_id": "ENG_03", "raw_name": "Dave Dev",
        "email": "dave_dot_dev@company.com", "amount": 400.00, "currency": "USD",
        "fee_usd": 4.00, "merchant_dept": "Engineering", "type": "payment",
        "status": "pending", "timestamp": "2021-08-15T09:00:00Z"
    },
    {
        "id": "txn_012", "user_id": "MKT_02", "raw_name": "Eve Market",
        "email": "e.market@company.com", "amount": 600.00, "currency": "USD",
        "fee_usd": 6.00, "merchant_dept": "Marketing", "type": "payment",
        "status": "pending", "timestamp": "2022-11-11T11:11:11Z"
    },
    {
        "id": "txn_013", "user_id": "SLS_02", "raw_name": "Frank Sales",
        "email": "frank@company.com", "amount": 700.00, "currency": "USD",
        "fee_usd": 7.00, "merchant_dept": "Sales", "type": "payment",
        "status": "pending", "timestamp": "2023-12-25T15:30:00Z"
    },
    {
        "id": "txn_014", "user_id": "HR_03", "raw_name": "Grace Human",
        "email": "grace@company.com", "amount": 800.00, "currency": "USD",
        "fee_usd": 8.00, "merchant_dept": "HR", "type": "payment",
        "status": "pending", "timestamp": "2024-02-14T08:45:00Z"
    },
    {
        "id": "txn_015", "user_id": "MKT_03", "raw_name": "Heidi Growth",
        "email": "heidi@company.com", "amount": 900.00, "currency": "USD",
        "fee_usd": None, "merchant_dept": "Marketing", "type": "payment",
        "status": "pending", "timestamp": "2024-03-10T10:20:00Z"
    }
]

out_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
if os.path.isdir('/app/data'):
    out_dir = '/app/data'
elif not os.path.isdir(out_dir):
    os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, 'transactions.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(transactions, f, indent=2)

print(f'Successfully generated transactions.json in {out_dir} with {len(transactions)} rows.')
