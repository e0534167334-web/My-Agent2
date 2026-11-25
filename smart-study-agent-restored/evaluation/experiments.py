import argparse,json,os
from pathlib import Path
from datetime import datetime,timedelta
from config import TIMEZONE
from domain.policies import make_reminders
from infrastructure.llm import OpenAIPlanner
from evaluation.evaluators import score

def main():
    p=argparse.ArgumentParser(); p.add_argument('--confirm-paid',action='store_true'); p.add_argument('--variant',choices=['before','after'],required=True); p.add_argument('--dataset',default='smart-study-policy-v1'); a=p.parse_args()
    if not a.confirm_paid: p.error('Explicit --confirm-paid required: up to 3 model calls per experiment')
    if not os.getenv('LANGSMITH_API_KEY'): p.error('LANGSMITH_API_KEY required')
    os.environ['LANGSMITH_TRACING']='true'
    from langsmith import Client
    client=Client(); rows=json.loads(Path(__file__).with_name('dataset.json').read_text())
    if not client.has_dataset(dataset_name=a.dataset):
        ds=client.create_dataset(a.dataset); client.create_examples(inputs=[{'text':r['text']} for r in rows],outputs=[r['expected'] for r in rows],dataset_id=ds.id)
    planner=OpenAIPlanner(); now=datetime(2030,1,10,8,tzinfo=TIMEZONE)
    def target(inputs):
        x=planner.extract(inputs['text'],[],now.isoformat())
        if not x.events: return {'type':None,'reminders':0}
        e=x.events[0]
        # Baseline: generic one-day reminder. Improved: domain policy.
        n=int(e.reminder_enabled and e.start_at-timedelta(days=1)>now) if a.variant=='before' else len(make_reminders([e],now))
        return {'type':e.event_type.value,'reminders':n}
    client.evaluate(target,data=a.dataset,evaluators=[score],experiment_prefix='study-'+a.variant,max_concurrency=1)
if __name__=='__main__': main()
