#coding=utf8
import os
import sys
import shutil
import pickle
########################################################################
class local(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self,conf,log=None):
        """Constructor"""
        self.conf=conf
        self.log=log
        self.rootp=conf['local']['path']+'/'+conf['system']['host']
        self.home=""
        self.protect=""
        if not os.path.exists(self.rootp):
            self.mkdir(self.rootp)
        self.backupdt={"__type":0}
        
    def getbackupname(self,path):
        return os.path.split(path)[1]
        
    def setprotect(self,path):
        self.protect=path
        
    def sethome(self,path):
        name=self.getbackupname(path)
        home=self.rootp+'/'+name
        self.home=home
        
    def put(self,src):
        self.sethome(src)
        if not self.isexist(self.home):
            self.mkdir(self.home)
        #if not self.isexist(self.home+'/.backupmeta'):
        #self.firstput(src,self.home)
        self.updateput(src)
        self.storemeta()
            
    
    def getcurrenttree(self,relapath):
        if not relapath:
            return self.backupdt
        nodes=relapath.split('/')
        nodes.remove('')
        current=self.backupdt
        try:
            for node in nodes:
                current=current[node]
        except Exception:
            #print sys.exc_info()[1]
            #self.log.error("have a error in getcurrenttree")
            return None
        return current
            
    def updateput(self,src):
        dlist=os.walk(src)
        for r,d,f in dlist:
            relapath=r[len(src):] #取相对路径
            current=self.getcurrenttree(relapath)
            cup=self.home+relapath
            if current!=None:
                for di in d:
                    if not self.isexist(cup+'/'+di)==1:
                        self.mkdir(self.home+relapath+'/'+di) 
                        current[di]={"__type":0}
                for fi in f:
                    localfp=r+'/'+fi
                    tp=os.stat(localfp).st_mtime
                    if (not self.isexist(cup+'/'+fi)) or  tp!=current[fi]['__mtime']:
                        fsize=os.path.getsize(localfp)
                        self.putfile(localfp,self.home+relapath+'/'+os.path.split(localfp)[1])
                        if fsize/1024/1024 < self.conf['system']['ihash']:
                            md5=lib.lib_hash.CalcMD5(localfp)
                        else:   
                            md5=None
                        current[fi]={"__type":1,"__mtime":tp,"__hash":md5,"__size":fsize}
        

    def storemeta(self):
        f=open('/tmp/detamper.pkl','wb')
        pickle.dump(self.backupdt,f)
        f.close()
        self.putfile("/tmp/detamper.pkl",self.home+'/.backupmeta')
        
    def loadmeta(self):
        if self.getfile(self.home+'/.backupmeta','/tmp/detamper.pkl')==-1:
            return None
        f=open('/tmp/detamper.pkl','rb')
        self.backupdt=pickle.load(f)
        f.close()
        return self.backupdt
    
    def getnodewithlocal(self,localp):
        relapath=localp[len(self.protect):] #取相对路径
        current=self.getcurrenttree(relapath)
        return current
    
    def putfile(self,src,dst):
        shutil.copy(src,dst)
    
    def get(self,src,dst):
        pass
    
    def getfile(self,src,dst):
        if self.isexist(src):
            shutil.copy(src,dst)
            return
        return -1
    
    def restorefile(self,node,localp):
        try:
            d=os.path.split(localp)[0]
            if not os.path.isdir(d):
                os.makedirs(d)  
        except Exception:
            print "create dir fail"
            print sys.exc_info()[1]
            
        relapath=localp[len(self.protect):] #取相对路径
        remotepath=self.home+relapath
        self.getfile(remotepath,localp)
        node['__mtime']=os.stat(localp).st_mtime
        
    def isexist(self,path):
        return os.path.exists(path)
    
    def mkdir(self,path):
        try:
            os.mkdir(path)
        except Exception:
            print sys.exc_info()[1]
    
    def __delete__(self):
        self.storemeta()
        
        
def getstorageclass(conf,log):
    if conf.has_key('local'):
        return local(conf,log)  
    