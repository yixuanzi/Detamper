#coding=utf8
import os
import sys
import shutil
import pickle
import paramiko
import json
import random

import lib.lib_hash
########################################################################
class sftp(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self,conf,log=None):
        """Constructor"""
        self.conf=conf
        self.log=log
        self.rootp=conf['server']['path']+'/'+conf['system']['host']
        self.home=""
        self.protect=""
        self.sftp=None
        if not self.login(conf['server']['host'],int(conf['server']['port']),conf['server']['user'],conf['server']['password']):
            log.error("login sftp fail,please check sftp info")
            raise Exception("LoginFail")
        if not self.isexist(self.rootp):
            self.mkdir(self.rootp)
        self.backupdt={"__type":0,"__current":None}
        self.conf['system']['ihash']=int(self.conf['system']['ihash'])
    
    def login(self,host,port,user,passwd):
        sf = paramiko.Transport((host,port))
        try:
            sf.connect(username = user,password = passwd)
        except Exception:
            return False
        self.sftp = paramiko.SFTPClient.from_transport(sf)
        return True
        
        
    def getbackupname(self,path):
        return os.path.split(path)[1]
    

        
    def setprotect(self,path):
        self.protect=path
        
    def sethome(self,path,bk=1): #是否备份模式
        #设置home目录，设置备份名映射
        namemap=self.getnamemap()
        #非备份模式设置home
        if not bk:
            if namemap:
                for k,v in namemap.iteritems():
                    if path==v:
                        self.home=self.rootp+'/'+k
                        return
                raise Exception("NotBackup")
            raise Exception("NotBackup")
        
        if not namemap:
            name=self.getbackupname(path)
            home=self.rootp+'/'+name
            self.backupdt['__current']=self.rootp+'/'+name
            self.home=home  
            self.savenamemap({name:path})
        else:
            name=self.getbackupname(path)
            mname=name
            while ((mname in namemap.keys()) and path!=namemap[mname]): #当出现重复命名的备份时，判定是否是已备份路径
                mname=name+str(random.randint(1,20)) #若不是，尝试产生新备份名
            name=mname
            home=self.rootp+'/'+name
            self.backupdt['__current']=self.rootp+'/'+name
            self.home=home  
            namemap[name]=path
            self.savenamemap(namemap)            
        
    def deletebackup(self,rpcserver,backupname):
        nmap=self.getnamemap()
        if backupname in nmap.keys():
            nmap.pop(backupname)
            #self.sftp.rmdir(self.rootp+'/'+backupname) #只能删除空目录 ,使用服务器远程删除策略
            rs=rpcserver.deldir(self.conf['server']['user'],self.conf['server']['password'],self.rootp+'/'+backupname)
            if rs['flag']!=0:
                return rs
            self.savenamemap(nmap)
            return 0
        raise Exception("NotBK")
    
    def put(self,src):
        self.sethome(src)
        if not self.isexist(self.home):
            self.mkdir(self.home)
        if not self.isexist(self.home+'/.backupmeta'):
            self.firstput(src)
            self.storemeta()
        else:
            self.loadmeta()
            self.updateput(src)
            self.storemeta()
    
    def getcurrenttree(self,relapath):
        if not relapath:
            return self.backupdt
        nodes=relapath.split('/')
        try:
            nodes.remove('')
        except Exception:
            pass
        current=self.backupdt
        try:
            for node in nodes:
                current=current[node]
        except Exception:
            #print sys.exc_info()[1]
            #self.log.error("have a error in getcurrenttree")
            return None
        return current
    
  
    def firstput(self,src):
        dlist=os.walk(src)
        for r,d,f in dlist:
            relapath=r[len(src):] #取相对路径
            current=self.getcurrenttree(relapath)
            cup=self.home+relapath
            if current!=None:
                for di in d:
                    self.mkdir(cup+'/'+di)
                    current[di]={"__type":0,"__current":current['__current']+'/'+di}
                for fi in f:
                    #r=storage.sftp.stat('octa/test/test/a').st_size  1024*1024 M单位 5M
                    localfp=r+'/'+fi
                    self.putfile(localfp,self.home+relapath+'/'+os.path.split(localfp)[1])
                    fsize=os.path.getsize(localfp)
                    if fsize/1024/1024 < self.conf['system']['ihash']:
                        md5=lib.lib_hash.CalcMD5(localfp)
                    else:
                        md5=None
                    current[fi]={"__type":1,"__mtime":os.stat(localfp).st_mtime,"__hash":md5,"__size":fsize}
        
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
                        current[di]={"__type":0,"__current":current['__current']+'/'+di}
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
        try:
            meta=self.sftp.open(self.home+'/.backupmeta')
        except Exception:
            self.log.error('open .backupmeta file fail')
            return
        self.backupdt=pickle.load(meta)
        meta.close()
        return self.backupdt
    
    def getnodewithlocal(self,localp):
        relapath=localp[len(self.protect):] #取本地相对路径
        current=self.getcurrenttree(relapath)
        return current
    
    def putfile(self,src,dst):
        try:
            self.sftp.put(src,dst)
        except Exception:
            self.log.error('put file fail %s to %s' %(src,dst))
            self.log.error(str(sys.exc_info()[1]))
    

    def getfile(self,src,dst):
        #下载文件，src，dst都为绝对路径
        try:
            d=os.path.split(dst)[0]
            if not os.path.isdir(d):
                os.makedirs(d)  
        except Exception:
            print "create dir fail"
            print sys.exc_info()[1]
            
        if self.isexist(src):
            self.sftp.get(src,dst)
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
    
    
    def isexistfile(self,path):
        pl=os.path.split(path)
        if pl[1] in self.sftp.listdir(pl[0]):
            return True
        return False
        
    def isexist(self,path):
        #是否存在路径，0不存在，1目录，2文件
        try: 
            self.sftp.listdir(path)
            return 1
        except Exception:
            if self.isexistfile(path):
                return 2
            else: 
                return 0
            
    def download(self,backup,dst,remotep=''):
        nmap=self.getnamemap()
        if ((not nmap) or (not (backup in nmap.keys()))):
            raise Exception("NotBK")
        self.home=self.rootp+'/'+backup
        if self.backupdt["__current"]==None:
            self.loadmeta()        
        self.download4obj(remotep,remotep,dst)
    
    def download4obj(self,root,current,dst,node=None):
        if not node:
            node=self.getcurrenttree(current)
            if not node:
                raise Exception("NotDir")
        if node["__type"]==0: #下载目录
            for k,v in node.iteritems():
                if len(k)<3 or k[:2]!="__":#下载文件，过滤属性字段
                    if v["__type"]==1:
                        rela=current[len(root):] #相对下载路径
                        self.getfile(node["__current"]+'/'+k,dst+rela+'/'+k)
                    elif v["__type"]==0:
                        self.download4obj(root,current+'/'+k,dst,v) #递归下载
        else:#单个下载文件
            name=os.path.split(current)[1]
            self.getfile(self.home+'/'+current,dst+'/'+name)

    def mkdir(self,path):
        try:
            self.sftp.mkdir(path)
        except Exception:
            print sys.exc_info()[1]
    
    def __delete__(self):
        self.storemeta()
        
    def getnamemap(self):
        if self.isexist(self.rootp+'/'+'name.map'):
            f=self.sftp.open(self.rootp+'/name.map')
            dt=f.read().strip()
            f.close()
            return json.loads(dt)
        return None
    
    def savenamemap(self,dt):
        #保持备份名映射数据
        f=self.sftp.open(self.rootp+'/name.map','w')
        f.write(json.dumps(dt))
        f.close()
        
def getstorageclass(conf,log):
    if conf.has_key('server'):
        return sftp(conf,log)  
    