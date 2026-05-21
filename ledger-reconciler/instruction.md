Task: Clean the ledger data.

We need a Python script that reads `/app/data/transactions.json`, processes it, and writes the cleaned records to `/app/data/reconciled_ledger.json`. Each output record must contain these fields exactly:
- `id` (string)
- `user_id` (string)
- `name` (string)
- `email` (string)
- `amount_usd` (float, two‑decimal places)
- `fee_usd` (float, two‑decimal places)
- `type` (string)
- `status` (string)
- `timestamp` (string formatted as `YYYY‑MM‑DD HH:MM:SS`)
- `row_hash` (string)

The script should perform the following steps:

1. **Deduplication** – Remove exact duplicate rows and also merge near‑duplicate rapid double‑charges (same `user_id`, `type`, amount and timestamps within 3 seconds).
2. **Name cleaning** – Strip whitespace, flip “Last, First” to “First Last”, drop quoted nicknames, middle initials, common titles, and normalise diacritics and ligatures. Apply title‑case while keeping particles like “de”, “van”, etc., lower‑cased.
3. **Email handling** – Fix common placeholders (`[at]`, `(at)`, `_at_`, `[dot]`, `(dot)`, `_dot_`). If the resulting address isn’t a single `@company.com` address, generate one as `{first_initial}.{last_name}@company.com`. If that address already exists, append a numeric suffix (second record gets `…2@company.com`, third gets `…3@company.com`, and so on).
4. **Currency conversion** – Use fixed rates: USD 1.00, EUR 1.10, GBP 1.25, BTC 60000.00, ETH 3000.00. Recognise a trailing “k”/“K” on the amount (multiply by 1 000) and on the currency code (e.g., `kUSD`).
5. **Fee imputation** – When `fee_usd` is missing, try the median of fees for the same department + year (needs at least three values). Otherwise compute a weighted average: 0.5 × dept‑year median + 0.3 × year median + 0.2 × department median. If nothing is available, fall back to the global median; if that is also zero, use **7.30**.
6. **Refund matching** – Link refund rows (`type == "refund"`) to their parent transaction via `parent_id`. If the refund amount is at least the parent amount, set the parent’s status to `refunded`; otherwise `partially_refunded`. Set the refund’s own status to `settled`.
7. **Timestamp parsing** – Accept many formats, in order of preference:
   - "N days ago" (relative to 2026‑05‑20 12:00:00)
   - Hex timestamps starting with `0x`
   - Excel serial dates between 10 000 and 99 999 (base 30‑Dec‑1899)
   - Unix timestamps > 100 000 000
   - ISO‑8601 strings (with optional timezone, which should be converted to UTC)
   Any unparsable or missing timestamp is replaced by the median timestamp for its department, or the company‑wide median if needed.
8. **Row removal** – Drop records where:
   - `amount_usd` is null, < 5.00 or > 1 000 000.00
   - the parsed timestamp is earlier than 2020‑01‑01 00:00:00
   - `user_id` contains characters other than letters, digits, hyphens or underscores.
9. **Sorting** – Order the final list by `timestamp` ascending, then by `id` ascending.
10. **Row hash** – Compute a SHA‑256 hash of the pipe‑delimited string:
    `{id}|{user_id}|{amount_usd:.2f}|{fee_usd:.2f}|{type}|{status}|{timestamp}`
    Store the hex digest in `row_hash`.
11. **Output** – Write the cleaned list as pretty‑printed JSON (2‑space indentation) to the target file.

That’s it – the script should follow the steps exactly so the test suite passes.
