# Active Context

Current Focus:
- M4 In Progress: QueryAnalyzer + controller query handling with filters, time range (periods), vendor breakdown (limited), and table rendering

Next Steps:
- Optional: add chart-friendly outputs and richer formatting; expand tests for edge cases

Decisions:
- Vendor breakdown limited by `TOP_VENDORS_LIMIT` (env, default 5)
- Period keywords supported: `last_month`, `this_month`, `this_year` 