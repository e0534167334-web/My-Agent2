import streamlit as st
from datetime import datetime,timedelta
from uuid import uuid4
from config import TIMEZONE,DATA
from domain.models import StudyPlan,UserPreferences,AvailabilitySlot,Event,Priority,EventType
from infrastructure.file_readers import read_file
from infrastructure.llm import DemoPlanner,OpenAIPlanner
from infrastructure.repository import Repository
from infrastructure.calendar_exporter import export_calendar
from agent.graph import build_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
st.set_page_config(page_title='Smart Study Agent')
st.title('סוכן הלמידה החכם')
if 'checkpointer' not in st.session_state: st.session_state.checkpointer=InMemorySaver()
repo=Repository()
mode=st.radio('Mode',['Demo (no AI)','OpenAI (paid API)'],disabled='thread' in st.session_state)
if 'thread' not in st.session_state:
    text=st.text_area('אירועים והנחיות')
    upload=st.file_uploader('קובץ אופציונלי',type=['xlsx','pdf','png','jpg','jpeg','webp'])
    st.caption('Demo ignores input and creates a sample exam. Real mode sends entered data to OpenAI.')
    day=st.date_input('יום למידה ראשון',value=datetime.now(TIMEZONE).date())
    start=st.time_input('משעה',value=datetime.strptime('16:00','%H:%M').time())
    end=st.time_input('עד שעה',value=datetime.strptime('19:00','%H:%M').time())
    days=st.number_input('מספר ימי זמינות רצופים באותן שעות',1,14,1)
    consent=st.checkbox('אני מאשרת שליחת הקלט ופרטי אירועים שמורים ל-OpenAI במצב אמיתי')
    if st.button('יצירת תוכנית',disabled=mode.startswith('OpenAI') and not consent):
        try:
            images=[]
            if upload and not mode.startswith('Demo'):
                extra,images=read_file(upload.name,upload.getvalue()); text+='\n'+extra
            if len(text)>24000: raise ValueError('Input too long')
            a,b=datetime.combine(day,start,TIMEZONE),datetime.combine(day,end,TIMEZONE)
            if b<=a: raise ValueError('Invalid availability')
            prefs=UserPreferences(available_slots=[AvailabilitySlot(start_at=a+timedelta(days=i),end_at=b+timedelta(days=i)) for i in range(days)])
            st.session_state.thread=str(uuid4()); st.session_state.mode=mode
            st.session_state.pending=dict(text=text,images=images,now=datetime.now(TIMEZONE).isoformat(),preferences=prefs.model_dump(mode='json'),existing=[] if mode.startswith('Demo') else [e.model_dump(mode='json') for e in repo.events()])
            st.rerun()
        except Exception as exc: st.error(str(exc))
else:
    cfg={'configurable':{'thread_id':st.session_state.thread},'recursion_limit':40}
    if st.button('התחלה מחדש'):
        for k in ['thread','mode','pending','checkpointer']: st.session_state.pop(k,None)
        st.rerun()
    try:
        planner=DemoPlanner() if st.session_state.mode.startswith('Demo') else OpenAIPlanner()
        if True:
            cp=st.session_state.checkpointer
            graph=build_graph(planner,cp)
            if 'pending' in st.session_state:
                payload=st.session_state.pop('pending'); graph.invoke(payload,cfg)
            snap=graph.get_state(cfg); state=snap.values
            if snap.interrupts:
                value=snap.interrupts[0].value
                if value['kind']=='clarify':
                    st.write(value['questions']); answer=st.text_area('השלמת פרטים')
                    if st.button('המשך',disabled=not answer.strip()): graph.invoke(Command(resume=answer),cfg); st.rerun()
                else:
                    plan=StudyPlan.model_validate(value['plan'])
                    names={e.id:e.title for e in plan.events}
                    for title,rows in [('אירועים',[{'שם':e.title,'מועד':e.start_at.strftime('%d/%m/%Y %H:%M'),'חשיבות':e.priority.value} for e in plan.events]),('זמני למידה',[{'אירוע':names.get(s.event_id,''),'התחלה':s.start_at.strftime('%d/%m/%Y %H:%M'),'סיום':s.end_at.strftime('%d/%m/%Y %H:%M')} for s in plan.study_sessions]),('תזכורות',[{'אירוע':names.get(r.event_id,''),'מועד':r.remind_at.strftime('%d/%m/%Y %H:%M')} for r in plan.reminders])]:
                        st.subheader(title)
                        if rows: st.dataframe(rows,hide_index=True)
                        else: st.caption('אין פריטים')
                    for w in value['warnings']: st.warning(w)
                    for e in value['errors']: st.error(e)
                    feedback=st.text_area('הנחיות לשינוי זמני הלמידה')
                    edited=[]
                    valid=True
                    with st.expander('עריכת פרטי אירועים'):
                        for e in plan.events:
                            k=e.id+str(state.get('reviews',0))
                            title=st.text_input('שם',e.title,key=k+'title')
                            day=st.date_input('תאריך',e.start_at.date(),key=k+'date')
                            hour=st.time_input('שעה',e.start_at.time(),key=k+'time')
                            priority=st.selectbox('חשיבות',list(Priority),index=list(Priority).index(e.priority),key=k+'priority')
                            kind=st.selectbox('סוג',list(EventType),index=list(EventType).index(e.event_type),key=k+'kind')
                            hours=st.number_input('שעות הכנה',0.0,200.0,float(e.preparation_hours),key=k+'hours')
                            enabled=st.checkbox('תזכורות',e.reminder_enabled,key=k+'enabled')
                            new_start=datetime.combine(day,hour,TIMEZONE)
                            try:
                                edited.append(Event.model_validate(dict(e.model_dump(),title=title,start_at=new_start,end_at=new_start+(e.end_at-e.start_at) if e.end_at else None,priority=priority,event_type=kind,preparation_hours=hours,reminder_enabled=enabled)).model_dump(mode='json'))
                            except ValueError:
                                valid=False
                                st.error('פרטי אירוע אינם תקינים')
                    prefs=UserPreferences.model_validate(state['preferences'])
                    revised_prefs=prefs
                    with st.expander('שינוי זמינות ללמידה'):
                        slots=prefs.available_slots
                        first=slots[0] if slots else None
                        key='availability'+str(state.get('reviews',0))
                        day=st.date_input('יום למידה ראשון',first.start_at.date() if first else datetime.now(TIMEZONE).date(),key=key+'day')
                        start=st.time_input('משעה',first.start_at.time() if first else datetime.strptime('16:00','%H:%M').time(),key=key+'start')
                        end=st.time_input('עד שעה',first.end_at.time() if first else datetime.strptime('19:00','%H:%M').time(),key=key+'end')
                        days=st.number_input('ימי זמינות',1,14,max(1,len(slots)),key=key+'days')
                        a,b=datetime.combine(day,start,TIMEZONE),datetime.combine(day,end,TIMEZONE)
                        if b<=a:
                            valid=False
                            st.error('שעת הסיום חייבת להיות אחרי שעת ההתחלה')
                        else:
                            revised_prefs=UserPreferences(available_slots=[AvailabilitySlot(start_at=a+timedelta(days=i),end_at=b+timedelta(days=i)) for i in range(days)])
                    if value['errors']: st.info('בדקי את מועד האירוע ואת שעות הזמינות. ניתן לשנות אותם וללחוץ על תיקון.')
                    changed=revised_prefs!=prefs or edited!=[e.model_dump(mode='json') for e in plan.events]
                    if changed: st.info('יש ללחוץ על תיקון כדי לחשב מחדש את התוכנית לפני אישור.')
                    if st.button('אישור',disabled=bool(value['errors']) or changed or not valid): graph.invoke(Command(resume={'action':'approve'}),cfg); st.rerun()
                    if st.button('תיקון',disabled=not valid or state.get('reviews',0)>=2): graph.invoke(Command(resume={'action':'change','feedback':feedback,'events':edited,'preferences':revised_prefs.model_dump(mode='json')}),cfg); st.rerun()
                    if state.get('reviews',0)>=2: st.caption('מכסת התיקונים הסתיימה. אפשר להתחיל מחדש.')
            elif state.get('status')=='approved':
                plan=StudyPlan.model_validate(state['plan'])
                if not st.session_state.mode.startswith('Demo'): repo.save(st.session_state.thread,plan)
                st.success('Approved (demo is not saved)' if st.session_state.mode.startswith('Demo') else 'Approved and saved')
                st.download_button('הורדת יומן',export_calendar(plan),'study.ics','text/calendar')
            else: st.info('Stopped. Start over to try again.')
    except Exception as exc: st.error(f'Execution failed: {type(exc).__name__}. Check configuration and start over.')
