from scripts.utils import conn 



isDerivedReportQ = f"""
SELECT COUNT(*) Count, isDerived FROM words GROUP BY isDerived;
"""
res = conn.execute(query=isDerivedReportQ)
print(res)
