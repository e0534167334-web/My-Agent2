from datetime import timedelta, timezone
from domain.policies import get_reminder_offsets
from config import TIMEZONE

def validate_plan(plan,preferences,now,existing=()):
    now=now.replace(tzinfo=TIMEZONE) if now.tzinfo is None else now.astimezone(TIMEZONE)
    errors=[]
    events={e.id:e for e in plan.events}
    if not events: errors.append('No events')
    if len(events)!=len(plan.events): errors.append('Duplicate event IDs')
    for slot in preferences.available_slots:
        if slot.end_at<=slot.start_at: errors.append('Invalid availability')
    for e in plan.events:
        if e.start_at<=now: errors.append(f'Event is in the past: {e.title}')
        if e.end_at and e.end_at<=e.start_at: errors.append('Invalid event duration')
        rs=[r for r in plan.reminders if r.event_id==e.id]
        if not e.reminder_enabled and rs: errors.append('Reminders disabled')
        for o in get_reminder_offsets(e):
            t=e.start_at-o
            if t>now and not any(r.remind_at==t for r in rs): errors.append(f'Missing reminder: {e.title}')
        hours=sum(max(0,(s.end_at.astimezone(timezone.utc)-s.start_at.astimezone(timezone.utc)).total_seconds()/3600) for s in plan.study_sessions if s.event_id==e.id)
        if hours+1e-8<e.preparation_hours: errors.append(f'Insufficient preparation time: {e.title}')
    for r in plan.reminders:
        e=events.get(r.event_id)
        if e is None: errors.append('Reminder has no matching event')
        elif r.remind_at>=e.start_at: errors.append('Reminder must precede event')
        if r.remind_at<=now: errors.append('Reminder time has already passed')
    sessions=sorted(plan.study_sessions,key=lambda s:s.start_at)
    for i,s in enumerate(sessions):
        e=events.get(s.event_id)
        if e is None: errors.append('Study session has no matching event')
        elif s.end_at>e.start_at: errors.append('Study session ends after event starts')
        if s.end_at<=s.start_at or s.start_at<now: errors.append('Invalid study session duration or time')
        if not any(a.start_at<=s.start_at and s.end_at<=a.end_at for a in preferences.available_slots): errors.append('Study session outside available hours')
        if any(s.start_at<t.end_at and s.end_at>t.start_at for t in sessions[:i]): errors.append('Overlapping study sessions')
        for x in [*plan.events,*existing]:
            if s.start_at<(x.end_at or x.start_at+timedelta(hours=1)) and s.end_at>x.start_at: errors.append(f'Study session overlaps event: {x.title}')
    return errors
