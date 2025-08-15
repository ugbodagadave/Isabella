RECEIPT_EXTRACTION_PROMPT = """
You are Isabella, an expert AI bookkeeping agent. Analyze this receipt text and extract structured financial data.

EXTRACT THE FOLLOWING AS JSON:

REQUIRED FIELDS:
- vendor: Company/store name (cleaned, proper capitalization)
- amount: Total amount as number (no currency symbols)
- date: Date in YYYY-MM-DD format
- category: Best matching expense category from list below

OPTIONAL FIELDS (if clearly available):
- payment_method: Payment type (Cash, Credit, Debit, etc.)
- receipt_number: Transaction / ticket / invoice number. Look for labels like TC#, TR#, ID#, INV#, Invoice #, Receipt #. Use the value closest to the header or totals section. Accept 4–25 char mixed-case strings of letters, digits, dashes.
- tax_amount: Tax amount if separately shown
- location: Full store address on one line if possible (street, city, state/province, postal code, country if present). Combine multiple header lines with a comma.
- description: If 1-3 item lines exist, join their names with "; ". If >3 items or the list is long, use a concise phrase like "Various grocery items" or "Office supplies; 5 items".
- items: Array of purchased items (name and optional price / qty) when clearly listed.

EXPENSE CATEGORIES:
- Office Supplies
- Meals & Entertainment  
- Travel & Transportation
- Equipment & Software
- Marketing & Advertising
- Professional Services
- Utilities & Communications
- Training & Education
- Maintenance & Repairs
- Other Business Expenses

PROCESSING RULES:
1. Clean vendor names: remove extra spaces, fix capitalization, expand abbreviations (e.g., WAL*MART → Walmart).
2. Determine the vendor ONLY from the receipt text provided. Prefer the most prominent header line; do not infer from previous receipts.
3. Normalize obvious variants (e.g., "WAL-MART", "WALMART" → "Walmart").
4. If the vendor cannot be confidently determined from the text, set vendor to "Unknown".
5. For ambiguous dates, pick the one near TOTAL / header; format YYYY-MM-DD.
6. Choose the most specific appropriate category.
7. If multiple totals appear, use the largest value that is explicitly labelled TOTAL / AMOUNT DUE / CASH TEND etc.
8. Receipt number: prefer a labelled value (TC#, TR#, ID#, etc.). If multiple, choose the one closest to totals section; exclude barcodes.
9. Location: Concatenate consecutive header lines that form the store address (stop before phone or manager lines).
10. Description: summarise items as per OPTIONAL FIELDS spec.
11. Handle multiple currencies by noting the currency symbol when present.
12. Return ONLY valid JSON – no markdown, no comments, no trailing commas.
13. Do not carry over any context from prior tasks; rely exclusively on RECEIPT TEXT below.

RECEIPT TEXT:
{receipt_text}

JSON RESPONSE (no markdown):
"""


QUERY_ANALYSIS_PROMPT = """
You are Isabella, an AI bookkeeping agent. Analyze this user query about their expenses.

USER QUERY: {user_query}

CURRENT DATE: {current_date}

DETERMINE:
1. Query type: summary, search, analysis, or report
2. Time range: specific dates, relative periods (last month, this year, etc.)
3. Filters needed: categories, vendors, amounts, etc.
4. Response format: table, list, chart, or narrative

Return as JSON:
{{
  "query_type": "summary|search|analysis|report",
  "time_range": {{
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "period": "last_month|this_year|etc or null"
  }},
  "filters": {{
    "categories": ["category1", "category2"] or null,
    "vendors": ["vendor1", "vendor2"] or null,
    "min_amount": number or null,
    "max_amount": number or null
  }},
  "response_format": "table|summary|chart|detailed"
}}
""" 