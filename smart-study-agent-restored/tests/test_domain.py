from datetime import datetime,timedelta
from config import TIMEZONE
from domain.models import Event,EventType,Priority,StudyPlan,UserPreferences,StudySession
from domain.policies import get_reminder_offsets,make_reminders,get_reminder_warnings
from domain.validators import validate_plan
NOW=datetime(2030,1,10,8,tzinfo=TIMEZONE)
def event(**kw):
    return Event(title='Exam',event_type=EventType.EXAM,start_at=NOW+timedelta(days=10),**kw)
def test_high(): assert len(get_reminder_offsets(event(priority=Priority.HIGH)))==3
def test_disabled(): assert not make_reminders([event(reminder_enabled=False)],NOW)
def test_valid():
    e=event(); assert not validate_plan(StudyPlan(events=[e],reminders=make_reminders([e],NOW)),UserPreferences(),NOW)
def test_missing(): assert validate_plan(StudyPlan(events=[event()]),UserPreferences(),NOW)
def test_late():
    e=event(); e.start_at=NOW+timedelta(hours=1); assert get_reminder_warnings(e,NOW); assert len(make_reminders([e],NOW))==1
def test_timezone(): assert Event(title='x',event_type='task',start_at=datetime(2030,1,1)).start_at.tzinfo==TIMEZONE
def test_unavailable():
    e=event(); p=StudyPlan(events=[e],reminders=make_reminders([e],NOW),study_sessions=[StudySession(event_id=e.id,start_at=NOW+timedelta(hours=1),end_at=NOW+timedelta(hours=2))]); assert 'Study session outside available hours' in validate_plan(p,UserPreferences(),NOW)
def test_repository(tmp_path):
    from infrastructure.repository import Repository
    r=Repository(tmp_path/'test.db'); e=event(); p=StudyPlan(events=[e],reminders=make_reminders([e],NOW)); r.save('1',p); r.save('1',p); assert len(r.events())==1
    due=r.due('2031-01-01T00:00:00+00:00'); assert len(due)==2; r.delivered(due[0][0]); assert len(r.due('2031-01-01T00:00:00+00:00'))==1


def test_scheduler_deadline_and_availability():
    from datetime import datetime, timedelta
    from config import TIMEZONE
    from domain.models import Event, UserPreferences, AvailabilitySlot, StudyPlan
    from domain.policies import schedule_sessions, make_reminders
    from domain.validators import validate_plan
    now = datetime(2030, 1, 10, 8, tzinfo=TIMEZONE)
    e = Event(title='Python submission', event_type='task', start_at=now+timedelta(days=1), preparation_hours=1.25)
    prefs = UserPreferences(available_slots=[AvailabilitySlot(start_at=now+timedelta(hours=2),end_at=now+timedelta(hours=4)), AvailabilitySlot(start_at=e.start_at+timedelta(hours=2),end_at=e.start_at+timedelta(hours=4))])
    sessions = schedule_sessions([e],prefs,now)
    assert len(sessions)==1
    assert sessions[0].end_at-sessions[0].start_at==timedelta(minutes=75)
    assert not validate_plan(StudyPlan(events=[e],study_sessions=sessions,reminders=make_reminders([e],now)),prefs,now)
    assert schedule_sessions([e],UserPreferences(available_slots=prefs.available_slots[1:]),now)==[]
