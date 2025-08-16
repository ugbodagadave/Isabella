RECEIPT_EXTRACTION_PROMPT = """
Extract expense data from this receipt as valid JSON. Follow the exact schema below.

REQUIRED SCHEMA:
{{
  "vendor": "string (cleaned company name, proper caps)",
  "amount": "number (total amount, no $ symbol)",
  "date": "string (YYYY-MM-DD format)",
  "category": "string (from categories below)"
}}

OPTIONAL FIELDS:
{{
  "payment_method": "string (Cash/Credit/Debit/etc)",
  "receipt_number": "string (TC#/TR#/ID# from header/totals)",
  "tax_amount": "number (if shown separately)",
  "location": "string (full address on one line)",
  "description": "string (1-3 items: join with '; '; >3 items: summary)",
  "items": ["array of item names with optional prices"]
}}

CATEGORIES: Office Supplies, Meals & Entertainment, Travel & Transportation, Equipment & Software, Marketing & Advertising, Professional Services, Utilities & Communications, Training & Education, Maintenance & Repairs, Other Business Expenses

RULES:
- Clean vendor: "WAL*MART" → "Walmart", remove extra spaces
- Date: prefer one near TOTAL/header, convert to YYYY-MM-DD
- Amount: use largest TOTAL/AMOUNT DUE (ignore SUBTOTAL)
- Category: pick most specific match for vendor/items
- Return ONLY valid JSON, no markdown/comments

RECEIPT TEXT:
{receipt_text}
"""


QUERY_ANALYSIS_PROMPT = """
Convert this natural language query about expenses into a structured JSON plan. Return ONLY valid JSON.

SCHEMA (all fields required, use null if unknown):
{{
  "intent": "summary|search|aggregate|trend|top_n|compare",
  "time_range": {{"start_date": "YYYY-MM-DD|null", "end_date": "YYYY-MM-DD|null", "relative": "last_month|this_month|this_year|last_quarter|last_7_days|last_90_days|custom|null"}},
  "filters": {{"vendors": ["string"]|null, "categories": ["string"]|null, "min_amount": number|null, "max_amount": number|null, "text_search": "string|null"}},
  "group_by": "none|vendor|category|date",
  "trend": {{"enabled": boolean, "granularity": "day|week|month|quarter|year"}},
  "top_n": {{"enabled": boolean, "dimension": "vendor|category", "limit": number}},
  "compare": {{"enabled": boolean, "baseline": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}|null, "target": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}|null}},
  "sort": {{"by": "amount|date|vendor|category|count|total", "direction": "asc|desc"}},
  "output": {{"format": "summary|table|detailed|chart", "chart": {{"type": "bar|line|pie|area|null", "dimension": "vendor|category|date|null", "metric": "amount|count|total|null"}}}}
}}

CATEGORIES: Office Supplies, Groceries, Travel & Transportation, Meals & Entertainment, Equipment & Software, Professional Services, Marketing & Advertising, Utilities & Communications, Training & Education, Maintenance & Repairs, Other Business Expenses

CURRENT DATE: {current_date}
USER QUERY: {user_query}

EXAMPLES:
{{"intent":"top_n","time_range":{{"start_date":null,"end_date":null,"relative":"last_90_days"}},"filters":{{"vendors":null,"categories":null,"min_amount":null,"max_amount":null,"text_search":null}},"group_by":"vendor","trend":{{"enabled":false,"granularity":"month"}},"top_n":{{"enabled":true,"dimension":"vendor","limit":5}},"compare":{{"enabled":false,"baseline":null,"target":null}},"sort":{{"by":"total","direction":"desc"}},"output":{{"format":"summary","chart":{{"type":null,"dimension":null,"metric":null}}}}}}
{{"intent":"search","time_range":{{"start_date":null,"end_date":null,"relative":"this_year"}},"filters":{{"vendors":["Walmart"],"categories":["Groceries"],"min_amount":20,"max_amount":null,"text_search":null}},"group_by":"none","trend":{{"enabled":false,"granularity":"month"}},"top_n":{{"enabled":false,"dimension":"vendor","limit":5}},"compare":{{"enabled":false,"baseline":null,"target":null}},"sort":{{"by":"date","direction":"desc"}},"output":{{"format":"table","chart":{{"type":null,"dimension":null,"metric":null}}}}}}
""" 