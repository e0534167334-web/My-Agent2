import pytest
pytest.importorskip('langgraph')
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from agent.graph import build_graph
from infrastructure.llm import DemoPlanner
from datetime import datetime,timedelta
from config import TIMEZONE

def test_review():
    now=datetime(2030,1,10,8,tzinfo=TIMEZONE); start=now+timedelta(days=1)
    g=build_graph(DemoPlanner(),InMemorySaver()); cfg={'configurable':{'thread_id':'test'}}
    g.invoke({'text':'demo','now':now.isoformat(),'preferences':{'available_slots':[{'start_at':start.isoformat(),'end_at':(start+timedelta(hours=3)).isoformat()}]}},cfg)
    assert g.get_state(cfg).interrupts
    g.invoke(Command(resume={'action':'approve'}),cfg); assert g.get_state(cfg).values['status']=='approved'


def test_edit_event():
    now=datetime(2030,1,10,8,tzinfo=TIMEZONE); start=now+timedelta(days=1)
    g=build_graph(DemoPlanner(),InMemorySaver()); cfg={'configurable':{'thread_id':'edit'}}
    g.invoke({'text':'demo','now':now.isoformat(),'preferences':{'available_slots':[{'start_at':start.isoformat(),'end_at':(start+timedelta(hours=3)).isoformat()}]}},cfg)
    events=g.get_state(cfg).values['events']
    edited=[dict(events[0],title='Updated exam',reminder_enabled=False)]
    g.invoke(Command(resume={'action':'change','events':edited}),cfg)
    state=g.get_state(cfg).values
    assert state['plan']['events'][0]['title']=='Updated exam'
    assert state['plan']['reminders']==[]
    assert not state['errors']
    g.invoke(Command(resume={'action':'approve'}),cfg)
    assert g.get_state(cfg).values['status']=='approved'


def test_change_availability():
    now=datetime(2030,1,10,8,tzinfo=TIMEZONE)
    g=build_graph(DemoPlanner(),InMemorySaver()); cfg={'configurable':{'thread_id':'availability'}}
    g.invoke({'text':'demo','now':now.isoformat(),'preferences':{'available_slots':[]}},cfg)
    assert g.get_state(cfg).values['errors']
    prefs={'available_slots':[{'start_at':now.isoformat(),'end_at':(now+timedelta(hours=3)).isoformat()}]}
    g.invoke(Command(resume={'action':'change','preferences':prefs}),cfg)
    assert not g.get_state(cfg).values['errors']


def test_clarification():
    from domain.models import Extraction
    class NeedsTime(DemoPlanner):
        def extract(self,text,images,now):
            if 'Clarification:' not in text: return Extraction(questions=['What time?'])
            return super().extract(text,images,now)
    now=datetime(2030,1,10,8,tzinfo=TIMEZONE)
    g=build_graph(NeedsTime(),InMemorySaver()); cfg={'configurable':{'thread_id':'clarify'}}
    g.invoke({'text':'tomorrow','now':now.isoformat(),'preferences':{'available_slots':[]}},cfg)
    assert g.get_state(cfg).interrupts[0].value['kind']=='clarify'
    g.invoke(Command(resume='18:00'),cfg)
    assert g.get_state(cfg).interrupts[0].value['kind']=='review'
