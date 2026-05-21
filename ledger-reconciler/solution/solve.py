import json
import os
import re
import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import List, Dict, Any, Optional

APP_DATA = '/app/data'

def resolve_path(filename: str) -> str:
    """Return absolute path to a data file, preferring the container mount."""
    if os.path.isdir(APP_DATA):
        return os.path.join(APP_DATA, filename)
    return os.path.join(os.path.dirname(__file__), '..', 'data', filename)

def clean_string(s: Optional[str]) -> str:
    return '' if not s else s.strip()

def normalize_name(name: str) -> str:
    cleaned = name.strip()
    # Reverse "Last, First"
    if ',' in cleaned:
        parts = cleaned.split(',')
        if len(parts) == 2:
            cleaned = f"{parts[1].strip()} {parts[0].strip()}"
            
    # Remove trailing comma/spaces
    cleaned = re.sub(r',\s*$', '', cleaned)
    
    # Remove quoted nicknames
    cleaned = re.sub(r'"[^"]*"', '', cleaned)
    
    # Remove middle single initials like "A. "
    cleaned = re.sub(r'\b[A-Z]\.\s', '', cleaned)
    
    # Normalize accents/diacritics
    cleaned = ''.join(c for c in unicodedata.normalize('NFD', cleaned)
                      if unicodedata.category(c) != 'Mn')
    
    # Replace special ligatures
    cleaned = (cleaned
               .replace('æ', 'ae').replace('Æ', 'ae')
               .replace('œ', 'oe').replace('Œ', 'oe')
               .replace('ß', 'ss')
               .replace('Æ', 'ae').replace('Œ', 'oe')) # Case insensitive replacements
    
    # Remove prefixes
    prefixes = {'dr.', 'mr.', 'mrs.', 'ms.', 'prof.', 'sir', 'mme.', 'md', 'ph.d.', 'phd', 'jr.', 'sr.', 'iii', 'iv'}
    words_arr = cleaned.split()
    words_arr = [w for w in words_arr if w.lower() not in prefixes]
    cleaned = ' '.join(words_arr)
    
    # Title case with particles
    particles = {'de', 'di', 'van', 'von', 'der', 'du'}
    words = cleaned.lower().split()
    for i in range(len(words)):
        if i == 0 or words[i] not in particles:
            words[i] = words[i].capitalize()
    return ' '.join(words)

def process_email(email: Optional[str], name: str) -> str:
    em = clean_string(email)
    em = re.sub(r'\[at\]|\(at\)|_at_', '@', em, flags=re.IGNORECASE)
    em = re.sub(r'\[dot\]|\(dot\)|_dot_', '.', em, flags=re.IGNORECASE)
    
    is_valid = '@' in em and em.endswith('@company.com') and em.count('@') == 1
    if is_valid:
        return em.lower()
        
    words = name.lower().split()
    first_initial = words[0][0]
    last_name = words[-1]
    return f"{first_initial}.{last_name}@company.com"

def parse_currency(amount: Any, currency: str) -> Optional[float]:
    if amount is None or amount == '':
        return None
    amt_str = str(amount).strip()
    curr = currency.strip().upper()
    
    multiplier = 1
    if amt_str.lower().endswith('k'):
        multiplier = 1000
        amt_str = amt_str[:-1]
    if curr.startswith('K'):
        multiplier *= 1000
        curr = curr[1:]
        
    try:
        amt = float(amt_str) * multiplier
    except ValueError:
        return None

    rate = 1.0
    curr = re.sub(r'[^A-Z]', '', curr)
    if curr == 'EUR':
        rate = 1.10
    elif curr == 'GBP':
        rate = 1.25
    elif curr == 'BTC':
        rate = 60000.00
    elif curr == 'ETH':
        rate = 3000.00
    elif curr == 'USD':
        rate = 1.00
        
    return amt * rate

def parse_timestamp(ts: str) -> Optional[datetime]:
    if not ts or ts == 'Unknown Date':
        return None
    from datetime import timezone
    # Check relative days
    if 'days ago' in ts:
        try:
            days = int(ts.split()[0])
            anchor = datetime(2026, 5, 20, 12, 0, 0)
            return anchor - timedelta(days=days)
        except Exception:
            pass

    # Check hex timestamp
    if ts.startswith('0x'):
        try:
            secs = int(ts, 16)
            return datetime.fromtimestamp(secs, timezone.utc).replace(tzinfo=None)
        except ValueError:
            pass

    # Check numeric values
    try:
        val = float(ts)
        if 10000 < val < 100000:
            base = datetime(1899, 12, 30)
            return base + timedelta(days=val)
        elif val > 100000000:
            return datetime.fromtimestamp(val, timezone.utc).replace(tzinfo=None)
    except ValueError:
        pass

    # ISO / generic date parsing
    try:
        clean_ts = ts
        if clean_ts.endswith('Z'):
            clean_ts = clean_ts[:-1] + '+00:00'
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    return None

def standardize_dept(dept: str) -> str:
    d = dept.lower()
    if 'eng' in d or 'dev' in d:
        return 'Engineering'
    if 'mkt' in d or 'growth' in d:
        return 'Marketing'
    if 'sls' in d or 'sales' in d:
        return 'Sales'
    if 'hr' in d or 'human' in d:
        return 'HR'
    return dept

def format_utc(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def median_safe(values: List[float]) -> float:
    if not values:
        return 0.0
    return median(values)

def main():
    input_path = resolve_path('transactions.json')
    raw_data: List[Dict[str, Any]] = json.load(open(input_path, 'r', encoding='utf8'))

    # Stage 1: exact duplicate removal
    stage1: List[Dict[str, Any]] = []
    seen = set()
    for txn in raw_data:
        key = json.dumps(txn, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        stage1.append(txn)

    # Stage 2: near duplicate merging based on name or email and timestamp proximity
    stage2: List[Dict[str, Any]] = []
    for curr in stage1:
        is_near = False
        curr_time = parse_timestamp(curr.get('timestamp', ''))
        curr_ts = curr_time.timestamp() if curr_time else 0
        for prev in stage2:
            prev_time = parse_timestamp(prev.get('timestamp', ''))
            prev_ts = prev_time.timestamp() if prev_time else 0
            
            try:
                curr_amt = float(curr.get('amount'))
                prev_amt = float(prev.get('amount'))
                amounts_match = curr_amt == prev_amt
            except (ValueError, TypeError):
                amounts_match = curr.get('amount') == prev.get('amount')
                
            if (str(curr.get('user_id')).lower() == str(prev.get('user_id')).lower() and
                curr.get('type') == prev.get('type') and
                amounts_match and
                abs(curr_ts - prev_ts) <= 3):
                is_near = True
                break
        if not is_near:
            stage2.append(curr)

    # Email uniqueness handling
    email_counts: Dict[str, int] = {}
    processed: List[Dict[str, Any]] = []
    for txn in stage2:
        user_id = clean_string(str(txn.get('user_id'))).lower()
        name = normalize_name(clean_string(str(txn.get('raw_name'))))
        base_email = process_email(txn.get('email'), name)
        # collision resolution: first user keeps base, subsequent get numeric suffix
        cnt = email_counts.get(base_email, 0)
        if cnt > 0:
            parts = base_email.split('@')
            email = f"{parts[0]}{cnt+1}@{parts[1]}"
        else:
            email = base_email
        email_counts[base_email] = cnt + 1
        amount_usd = parse_currency(txn.get('amount'), txn.get('currency'))
        timestamp_dt = parse_timestamp(txn.get('timestamp'))
        processed.append({
            'id': txn.get('id'),
            'user_id': user_id,
            'name': name,
            'email': email,
            'amount_usd': amount_usd,
            'fee_usd': float(txn['fee_usd']) if txn.get('fee_usd') is not None else None,
            'type': txn.get('type'),
            'status': txn.get('status'),
            'timestamp': '',
            'raw_dept': standardize_dept(str(txn.get('merchant_dept'))),
            'raw_date': timestamp_dt,
            'parent_id': txn.get('parent_id')
        })

    # Impute missing dates
    dept_times: Dict[str, List[float]] = {}
    all_times: List[float] = []
    for rec in processed:
        if rec['raw_date']:
            ts = rec['raw_date'].timestamp()
            all_times.append(ts)
            dept_times.setdefault(rec['raw_dept'], []).append(ts)
    company_median = median_safe(all_times)
    for rec in processed:
        if not rec['raw_date']:
            dept_list = dept_times.get(rec['raw_dept'], [])
            ts = median_safe(dept_list) if dept_list else company_median
            rec['raw_date'] = datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None)
        rec['timestamp'] = format_utc(rec['raw_date'])

    # Fee imputation
    group_fees: Dict[str, List[float]] = {}
    dept_fees: Dict[str, List[float]] = {}
    year_fees: Dict[int, List[float]] = {}
    for rec in processed:
        if rec['fee_usd'] is not None:
            yr = rec['raw_date'].year
            key = f"{rec['raw_dept']}-{yr}"
            group_fees.setdefault(key, []).append(rec['fee_usd'])
            dept_fees.setdefault(rec['raw_dept'], []).append(rec['fee_usd'])
            year_fees.setdefault(yr, []).append(rec['fee_usd'])
    for rec in processed:
        if rec['fee_usd'] is None:
            yr = rec['raw_date'].year
            key = f"{rec['raw_dept']}-{yr}"
            g = group_fees.get(key, [])
            if len(g) >= 3:
                rec['fee_usd'] = median_safe(g)
            else:
                gm = median_safe(g) if g else 0
                cym = median_safe(year_fees.get(yr, [])) if year_fees.get(yr) else 0
                dom = median_safe(dept_fees.get(rec['raw_dept'], [])) if dept_fees.get(rec['raw_dept']) else 0
                if not g and not year_fees.get(yr):
                    imputed = dom
                    if imputed == 0:
                        all_dept = []
                        for v in dept_fees.values():
                            all_dept.extend(v)
                        imputed = median_safe(all_dept)
                    # Default fallback to 7.30 if still zero
                    if imputed == 0:
                        imputed = 7.30
                else:
                    imputed = 0.5 * gm + 0.3 * cym + 0.2 * dom
                rec['fee_usd'] = imputed

    # Build lookup for refunds
    txns_by_id = {r['id']: r for r in processed if r['type'] != 'refund'}
    final: List[Dict[str, Any]] = []
    for rec in processed:
        if rec['type'] == 'refund':
            if not rec.get('parent_id') or rec['parent_id'] not in txns_by_id:
                continue
            parent = txns_by_id[rec['parent_id']]
            ref_amt = rec['amount_usd'] or 0
            par_amt = parent['amount_usd'] or 0
            if ref_amt >= par_amt:
                parent['status'] = 'refunded'
            else:
                parent['status'] = 'partially_refunded'
            rec['status'] = 'settled'
            final.append(rec)
        else:
            final.append(rec)

    # Filtering
    def valid(r: Dict[str, Any]) -> bool:
        if r['amount_usd'] is None or r['amount_usd'] < 5.0 or r['amount_usd'] > 1_000_000:
            return False
        if r['raw_date'] < datetime(2020, 1, 1):
            return False
        if not re.match(r'^[a-z0-9\-_]+$', r['user_id'], re.I):
            return False
        return True

    final = [r for r in final if valid(r)]

    # Sort
    final.sort(key=lambda x: (x['raw_date'], x['id']))

    # Row hash generation (match TypeScript implementation)
    for r in final:
        r['amount_usd'] = round(r['amount_usd'], 2)
        r['fee_usd'] = round(r['fee_usd'], 2)
        hash_str = f"{r['id']}|{r['user_id']}|{r['amount_usd']:.2f}|{r['fee_usd']:.2f}|{r['type']}|{r['status']}|{r['timestamp']}"
        r['row_hash'] = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
        # remove helper fields
        for k in ['raw_dept', 'raw_date', 'parent_id']:
            r.pop(k, None)

    out_path = resolve_path('reconciled_ledger.json')
    with open(out_path, 'w', encoding='utf8') as f:
        json.dump(final, f, indent=2)

if __name__ == '__main__':
    main()
