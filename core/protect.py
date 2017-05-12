#coding=utf8
import time
import os
import sys
import shutil
import lib.lib_hash
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



def printlog(log,msg,leave="debug"):
    imap={"info":log.info,"debug":log.debug,"error":log.error}
    print msg
    imap[leave](msg)
########################################################################
class myprotect(object):
    """
    防篡改保护类
    每一个observe由模块启动一个线程进行监控保护,其事件队列在一个observe中是单线程处理
    当多个保护目录启动了多个observe时为多线程
    """

    #----------------------------------------------------------------------
    def __init__(self,conf,module,log=None):
        """Constructor"""
        self.paths=conf['protect']['dir'].split(';')
        self.log=log
        self.conf=conf
        self.module=module
        self.observer=[]
        self.setprotect()
        self.flag=1

    def setprotect(self):
        #启动observe,添加保护目录
        for path in self.paths:
            if not os.path.isdir(path):
                continue
            observer = Observer()
            storage=self.module.getstorageclass(self.conf,self.log)
            handler = MyHandler(self.conf,storage,path,self.log)
            observer.schedule(handler, path=path, recursive=True)
            self.observer.append(observer)
            print "add protect dir with %s" %path
            self.log.info("add protect dir with %s" %path)
            

    def start(self):
        #开始保护
        for observer in self.observer:
            observer.start()    
            print "started protect....."
            print "You can run it backgroud..."
    
          
class MyHandler(FileSystemEventHandler):
    
    def __init__(self,conf,storage,path,log):
        self.storage=storage
        self.path=path #本地被保护目录
        self.log=log
        self.backupmeta=None
        self.storage.sethome(path,0)
        self.storage.setprotect(path)
        self.backupmeta=self.storage.loadmeta()
        
        if not self.backupmeta:
            printlog(log,"load backup metedata fail form remote with %s" %self.path,'error')
            exit()
            
    def ignore(self,path):
        if path.endswith((".swp",".swpx","4913")):
            return True
        
    
    def on_created(self,event):
        if event.is_directory:
            print event.event_type,event.src_path
            node=self.storage.getnodewithlocal(event.src_path)
            if not node:
                print "ALERT:illegal create dir %s,remove it" %event.src_path
                shutil.rmtree(event.src_path)
        else :
            print "file create:",event.event_type,event.src_path
            

    def on_deleted(self,event):
        if event.is_directory:
            print "dir delete:",event.event_type,event.src_path
        else :
            print event.event_type,event.src_path
            if self.ignore(event.src_path):return 
            node=self.storage.getnodewithlocal(event.src_path)
            if node:
                print "ALERT:illegal delete file %s,restore it" %event.src_path
                self.storage.restorefile(node,event.src_path)      

    def on_modified(self,event):
        if event.is_directory:
            return
        print "file modify:",event.event_type,event.src_path
        if self.ignore(event.src_path):return 
        node=self.storage.getnodewithlocal(event.src_path)
        if not node:
            print "ALERT: illegal create file %s,remove it" %event.src_path
            os.remove(event.src_path)
            return
        fsize=os.path.getsize(event.src_path)   
        
        if node['__size']!=fsize:
            print "ALERT: illegal modify file %s,restore it" %event.src_path
            self.storage.restorefile(node,event.src_path) 
        
        if node["__hash"]: 
            md5=lib.lib_hash.CalcMD5(event.src_path)
            if node['__hash']!=md5:
                print "ALERT: illegal modify file %s,restore it" %event.src_path
                self.storage.restorefile(node,event.src_path)
        else:
            if node['__mtime']!=os.stat(event.src_path).st_mtime:
                print "ALERT: illegal modify file %s,restore it" %event.src_path
                self.storage.restorefile(node,event.src_path) 
            
    
    def on_moved(self,event):
        print "move",event.src_path,event.dest_path
        if event.src_path==event.dest_path[:-1] and event.dest_path[-1]=="~":return
        node=self.storage.getnodewithlocal(event.src_path)
        if node:
            print "ALERT: illegal move file %s to %s,restore it" %(event.src_path,event.dest_path)
            shutil.move(event.dest_path, event.src_path)
