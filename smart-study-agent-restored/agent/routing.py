from config import MAX_PLAN_RETRIES
def after_extract(s): return 'clarify' if s['questions'] else 'generate'
def after_clarify(s): return 'end' if s.get('status')=='cancelled' else 'extract'
def after_validate(s): return 'retry' if s['errors'] and s.get('status')=='revise' and s.get('feedback') and s.get('retries',0)<MAX_PLAN_RETRIES else 'review'
def after_review(s): return 'generate' if s.get('status')=='revise' else 'end'
