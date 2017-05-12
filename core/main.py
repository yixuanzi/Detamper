#coding=utf8
import paramiko
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import sys
import copy

import handle_client
import sftp
        
class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):pass
#=============================
class MyObject:
    def __init__(self,conf,log):
        self.conf=conf
        self.log=log
        self.status={'backuping':0,'protecting':'','downloading':0}
        self.myprotect=None
        self.sftp=sftp.sftp(conf,log)
        self.rpcserver = xmlrpclib.ServerProxy("http://%s" %self.conf['server']['rpcserver'])
        
    def checkup(self,user,passwd):
        #本地校验 用户名，密码校验
        rs=self.rpcserver.checkuser(user,passwd) #远程校验
        if rs['flag']==0:
            return True 
        return False
    
    def sayHello(self):
        return "hello xmlprc"
    
    def __getperm(self,user,passwd):
        rs=self.rpcserver.getuserperm(user,passwd)
        if rs['flag']==0:
            return rs['perm'][0][1]
        else:
            return rs
        
    def backup(self,user,passwd,localp):
        #备份
        if not self.checkup(user, passwd):
            return {"flag":1,"msg":"user,passwd is vaild"}
        
        if self.status['backuping']:
            return {"flag":1,"msg":"detamper is backuping,please wait"}
        
        perm=self.__getperm(user, passwd)
        if type(perm)==dict: #返回异常
            return perm
        if perm & 0b0100 ==0:#校验权限
            return {"flag":5,"msg":"you have not backup perm"}
        try:
            self.status['backuping']=1
            self.conf['protect']['dir']=localp            
            handle_client.work_backup(self.conf,self.log)
            self.status['backuping']=0
            return {"flag":0,"msg":"backup %s to server succfully" %localp}
        except Exception:
            self.status['backuping']=0
            e=str(sys.exc_info()[1])
            if e=="LoginFail":
                return {"falg":4,"msg":"login the server fail"}
            print e
    
    
    def protect(self,user,passwd,localp,boot=0): #当启动保护，不需校验
        #保护，防篡改
        if boot:
            pass
        else:
            if not self.checkup(user, passwd):
                return {"flag":1,"msg":"user,passwd is vaild"}
        if self.status['protecting']:
            return {"flag":2,"msg":"protect model is enable","path":self.status['protecting']}
        
        nmap=self.sftp.getnamemap()
        if (not nmap) or (localp not in nmap.values()):
            return {"flag":5,"msg":"protect dir have not backup"}
        
        self.conf['protect']['dir']=localp
        try:
            self.myprotect=handle_client.work_protect(self.conf,self.log)
            self.status['protecting']=localp
            return {"flag":0,"msg":"protect model is start succfully","path":self.status['protecting']}
        except Exception:
            e=str(sys.exc_info()[1])
            self.status['protecting']=""
            if e=="NotBackup":
                return {"flag":3,"msg":"protect dir have not backup"}
            elif e=="LoginFail":
                return {"falg":4,"msg":"login the server fail"}
            
    def getstatus(self,user,passwd):
        #获取当前状态
        if not self.checkup(user, passwd):
            return {"flag":1,"msg":"user,passwd is vaild"}
        user=copy.copy(self.conf['server'])
        user.pop('password')
        return {"status":self.status,"backup":self.sftp.getnamemap(),"user":user}
    
    def changepwd(self,user,passwd,passwd_new):
        #调用服务端远程rpc
        return self.rpcserver.changpwd(user,passwd,passwd_new)
    
    def deletebackup(self,user,passwd,backup_name):
        if not self.checkup(user, passwd):
            return {"flag":1,"msg":"user,passwd is vaild"}
        if self.status['protecting']:
            return {"flag":2,"msg":"protect model is enable"}
        
        perm=self.__getperm(user, passwd)
        if type(perm)==dict: #返回异常
            return perm
        if perm & 0b0001 ==0:#校验权限
            return {"flag":5,"msg":"you have not delete perm"}        
        
        try:
            rs=self.sftp.deletebackup(self.rpcserver,backup_name)
            if rs!=0:
                return rs
            return {"flag":0,"msg":"delete %s succfully" %backup_name}
        except Exception:
            e=str(sys.exc_info()[1])
            if e=="NotBK":
                return {"flag":1,"msg":"have not this backup name"}
            print e
    
    def download(self,user,passwd,backup,dst,remote=''):
        if not self.checkup(user, passwd):
            return {"flag":1,"msg":"user,passwd is vaild"}     
        if self.status['downloading']:
            return {"flag":2,"msg":"A download task is going"}
        
        perm=self.__getperm(user, passwd)
        if type(perm)==dict: #返回异常
            return perm
        if perm & 0b0010 ==0:#校验权限
            return {"flag":5,"msg":"you have not download perm"}
        
        try:
            self.status['downloading']=1
            self.sftp.download(backup,dst,remote)
            self.status['downloading']=0
            return {"flag":0,"msg":"download %s %s succfully" %(backup,remote)}    
        except Exception:
            self.status['downloading']=0
            e=str(sys.exc_info()[1])
            return {"flag":3,"msg":e}
            
    def stoprotect(self,user,passwd):
        if not self.checkup(user, passwd):
            return {"flag":1,"msg":"user,passwd is vaild"} 
        if not self.status['protecting']:
            return {"flag":2,"msg":"protect model is not enable"}
        
        perm=self.__getperm(user, passwd)
        if type(perm)==dict: #返回异常
            return perm
        if perm & 0b1000 ==0:#校验权限
            return {"flag":5,"msg":"you have not control perm"}
        
        if self.myprotect:
            for observer in self.myprotect.observer:
                observer.stop()    
                observer.join()
            self.status['protecting']=''
            return {"flag":0,"msg":"stop protect model succfully"}
        return {"flag":3,"msg":"protect class not vaild"}
        
#========================================================================
def main(conf,log):
    #新建xml-rpc服务器
    try:
        obj = MyObject(conf,log)
    except Exception:
        print "login server or connect rpc server fail!!!"
        print sys.exc_info()[1]
        exit()
    if conf.has_key('boot') and int(conf['boot']['enable'])>0:
        print obj.protect('', '',conf['boot']['protect'],boot=1)  
    server = ThreadXMLRPCServer((conf['system']['listen'], int(conf['system']['port'])), allow_none=True)
    server.register_instance(obj)
    print "Listening on %s port %s" %(conf['system']['listen'],conf['system']['port'])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "exit rpc server!!!"