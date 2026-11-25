from datetime import datetime,timezone
from infrastructure.repository import Repository

def main():
    import ctypes
    repo=Repository()
    for id,message in repo.due(datetime.now(timezone.utc).isoformat()):
        # Acknowledge before marking delivered; a crash can repeat an alert.
        result=ctypes.windll.user32.MessageBoxW(0,message,'Smart Study Agent',0x40|0x40000)
        if result: repo.delivered(id)
if __name__=='__main__': main()
