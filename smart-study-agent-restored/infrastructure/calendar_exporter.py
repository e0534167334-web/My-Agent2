from datetime import datetime,timedelta,timezone

def export_calendar(plan):
    from icalendar import Calendar,Event
    cal=Calendar(); cal.add('prodid','-//Smart Study Agent//EN'); cal.add('version','2.0')
    for e in plan.events:
        item=Event(); item.add('uid',e.id+'@smart-study'); item.add('summary',e.title); item.add('dtstamp',datetime.now(timezone.utc)); item.add('dtstart',e.start_at.astimezone(timezone.utc)); item.add('dtend',(e.end_at or e.start_at+timedelta(hours=1)).astimezone(timezone.utc)); cal.add_component(item)
    for i,s in enumerate(plan.study_sessions):
        item=Event(); item.add('uid',f'{s.event_id}-{i}@smart-study'); item.add('summary','Study: '+next(e.title for e in plan.events if e.id==s.event_id)); item.add('dtstamp',datetime.now(timezone.utc)); item.add('dtstart',s.start_at.astimezone(timezone.utc)); item.add('dtend',s.end_at.astimezone(timezone.utc)); cal.add_component(item)
    return cal.to_ical()
