from collections import Counter
from scripts.utils import conn 
from scripts.utils import fix_ar_display


isDerivedReportQ = f"""
SELECT COUNT(*) Count, isDerived FROM words GROUP BY isDerived;
"""
hasDefReportQ = f"""
SELECT COUNT(*) Count, id IN (SELECT wordId FROM `definitions`) hasDef 
FROM words 
GROUP BY hasDef;
"""
hasCategReportQ = f"""
SELECT COUNT(*) Count, id IN (SELECT wordId FROM `word_categories`) hasCateg, isDerived 
FROM words 
GROUP BY hasCateg, isDerived;
"""
undefWords = f"""
SELECT word
FROM words 
WHERE id NOT IN (SELECT wordId FROM `definitions`);
"""
undefWords = [fix_ar_display(w['word']) for w in conn.execute(query=undefWords)]
print(conn.execute(query=isDerivedReportQ))
print('='*50)
print(conn.execute(query=hasDefReportQ))
print('='*50)
print(conn.execute(query=hasCategReportQ))
print('='*50)
print(Counter(undefWords))
