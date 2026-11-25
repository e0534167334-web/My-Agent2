from datetime import timedelta
from domain.models import EventType, Priority, Reminder

def get_reminder_offsets(event):
    if not event.reminder_enabled: return []
    if event.event_type == EventType.EXAM:
        days = [7,2,1] if event.priority == Priority.HIGH else [2,1]
    elif event.event_type == EventType.PROJECT and event.priority == Priority.HIGH:
        days = [7,3,1]
    elif event.event_type == EventType.MEETING:
        return [timedelta(hours=1)]
    else: days=[1]
    return [timedelta(days=d) for d in days]

def get_reminder_warnings(event,now):
    return [f'Not enough advance notice: {event.title} ({o})' for o in get_reminder_offsets(event) if event.start_at-o <= now]

def make_reminders(events,now):
    result=[]
    for e in events:
        times={e.start_at-o for o in get_reminder_offsets(e) if e.start_at-o>now}
        if get_reminder_warnings(e,now) and now<e.start_at:
            times.add(now+min(timedelta(minutes=1),(e.start_at-now)/2))
        result.extend(Reminder(event_id=e.id,remind_at=t,message=e.title) for t in sorted(times))
    return result


def schedule_sessions(events, preferences, now, existing=()):
    """Earliest deadline first; allocate only real available time."""
    from datetime import timezone
    from domain.models import StudySession
    def utc(t):
        return t.astimezone(timezone.utc)
    busy = [(utc(e.start_at), utc(e.end_at or e.start_at + timedelta(hours=1))) for e in [*events, *existing]]
    result = []
    for e in sorted(events, key=lambda e: (e.start_at, e.id)):
        remaining = timedelta(hours=e.preparation_hours)
        for slot in sorted(preferences.available_slots, key=lambda a: a.start_at):
            start = max(utc(slot.start_at), utc(now))
            end = min(utc(slot.end_at), utc(e.start_at))
            if remaining <= timedelta(0): break
            for a, b in sorted(busy + [(end, end)]):
                if b <= start: continue
                stop = min(a, end, start + remaining)
                if stop > start:
                    result.append(StudySession(event_id=e.id, start_at=start, end_at=stop))
                    busy.append((start, stop))
                    remaining -= stop - start
                start = max(start, b)
                if start >= end or remaining <= timedelta(0): break
    return result
