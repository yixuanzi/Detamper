#coding=utf8
import importlib
import protect


def printlog(log,msg,leave="debug"):
    imap={"info":log.info,"debug":log.debug,"error":log.error}
    print msg
    imap[leave](msg)
    

##当整个删除监控目录时,只能恢复一次,因watchdog机制,后续事件监控失效
def work_backup(conf,log):
        #备份模式
    module=importlib.import_module("core.%s" %conf['system']['storage'])
    storage=module.getstorageclass(conf,log)
        
    for p in conf['protect']['dir'].split(';'):
        if p:   
            storage.put(p)
            printlog(log,"Put protect dir to %s succfully" %storage.rootp,'info')
        
def work_protect(conf,log):    
    #保护模式   
    module=importlib.import_module("core.%s" %conf['system']['storage'])     
    myprotect=protect.myprotect(conf,module,log)
    myprotect.start()
    return myprotect
    
