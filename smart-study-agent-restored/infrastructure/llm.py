import json
from datetime import datetime,timedelta
from config import MODEL
from domain.models import Extraction, Sessions, Event, EventType, Priority, StudySession
from agent.prompts import EXTRACT, PLAN
class OpenAIPlanner:
    def __init__(self):
        from langchain_openai import ChatOpenAI
        self.model=ChatOpenAI(model=MODEL,temperature=0,max_tokens=2500,max_retries=0,timeout=60)
    def extract(self,text,images,now):
        content=[{'type':'text','text':f'Current time: {now}\nData: {text}'}]+[{'type':'image_url','image_url':{'url':i,'detail':'low'}} for i in images]
        return self.model.with_structured_output(Extraction).invoke([('system',EXTRACT),('human',content)])
    def plan(self,events,slots,feedback,existing):
        payload=json.dumps(dict(events=events,slots=slots,feedback=feedback,existing=existing),ensure_ascii=False)
        return self.model.with_structured_output(Sessions).invoke([('system',PLAN),('human',payload)])
class DemoPlanner:
    def extract(self,text,images,now):
        return Extraction(events=[Event(title='Demo exam',event_type=EventType.EXAM,priority=Priority.HIGH,start_at=datetime.fromisoformat(now)+timedelta(days=10),preparation_hours=1)])
    def plan(self,events,slots,feedback,existing):
        result=[]
        for e in events:
            if e['preparation_hours'] and slots:
                start=datetime.fromisoformat(slots[0]['start_at']); result.append(StudySession(event_id=e['id'],start_at=start,end_at=start+timedelta(hours=e['preparation_hours'])))
        return Sessions(study_sessions=result)
