import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def on_created(self,event):
	if event.is_directory:
	    print event.event_type,event.src_path
	else :
	    print event.event_type,event.src_path
	
		
    def on_deleted(self,event):
	if event.is_directory:
	    print event.event_type,event.src_path
	else :
	    print event.event_type,event.src_path

    def on_modified(self,event):
	if not event.is_directory:
	    print event.event_type,event.src_path
	

    def on_moved(self,event):
	print "move",event.src_path,event.dest_path


if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path="/home/lab8/Python/craw", recursive=True)
    observer.start()
    """
    try:
	print "started myWatch"
	while True:
	    time.sleep(1)
    except KeyboardInterrupt:
	observer.stop()
    observer.join()
    """
    observer2 = Observer()
    observer2.schedule(event_handler, path="/home/lab8/Python/train-db", recursive=True)
    observer2.start()

    try:
	print "started myWatch"
	while True:
	    time.sleep(1)
    except KeyboardInterrupt:
	observer.stop()
	observer2.stop()
    observer.join()
    observer2.join()