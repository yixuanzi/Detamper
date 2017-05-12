#coding=utf8
import os
import sys
import logging
import sqlite3
import md5
import base64
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn


import lib.lib_config


from random import Random
def random_str(randomlength=32):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str
########################################################################
class serverdb:
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.con=None
        self.cu=None
        self.getdb()
        
    def initdb(self):
        self.con=sqlite3.connect('db/server.db')
        self.cu=self.con.cursor()        
        self.cu.execute("create table token (tokens char(50) primary key)")
        self.cu.execute("create table user (name char(20) primary key,passwd char(50),perm tinyint)") #perm 权限字段，[控制，备份，下载，删除]
        self.con.commit() 
        
    def getdb(self):
        if not os.path.exists('db/server.db'):
            self.db=self.initdb()    
            return
        self.con=sqlite3.connect('db/server.db')
        self.cu=self.con.cursor()
        
    def execsql(self,sql):
        self.cu.execute(sql)
        self.con.commit() 
        return self.cu.fetchall()
    
    def has_token(self,token):
        rs=self.execsql('select * from token where tokens="%s"' %token)
        if len(rs)>0:
            return True
        return False
    
    def addtoken(self,token):
        self.execsql('insert into token values ("%s")' %token)
    
    def __delete__(self):
        if self.cu:
            self.cu.commit() 
            self.cu.close()    
        if self.con:
            self.con.close()

########################################################################
class user:
    """"""

    #----------------------------------------------------------------------
    def __init__(self,conf,db):
        """Constructor"""
        self.conf=conf
        self.serverdb=db
        self.init()
    
    def init(self):
        os.system("groupadd sftp")
        os.system("mkdir %s" %self.conf['server']['path'])
    
    def encrypasswd(self,passwd):
        return md5.md5(passwd+"OCTA_GGS").hexdigest()
    def setpaswd(self,user,passwd):
        return os.system("passwd %s << EOF\n%s\n%s\nEOF" %(user,passwd,passwd)) #设置密码
    
    def changepwd(self,user,passwd,passwd_new):
        self.serverdb.execsql('update user set passwd="%s" where name="%s"' %(passwd_new,user))
        #flag=os.system("passwd %s << EOF\n%s\n%s\n%sEOF" %(user,passwd,passwd_new,passwd_new)) #更新密码
        return self.setpaswd(user,passwd_new)
    
    def checkpwd(self,user,passwd):
        rs=self.serverdb.execsql('select * from user where name="%s" and passwd="%s"' %(user,passwd))
        if rs:
            return True
        return False
    
    def createuser(self,user,passwd): #创建用户
        home=self.conf['server']['path']+'/'+user
        self.serverdb.execsql('insert into user values("%s","%s","%d")' %(user,passwd,0b1111)) #全权限
        os.system("mkdir %s" %home)
        os.system("mkdir %s/%s" %(home,self.conf['server']['uroot']))
        os.system("useradd -g sftp -d %s -s /bin/false %s" %(home,user))
        self.setpaswd(user, passwd)
        os.system("chown %s:sftp %s/%s" %(user,home,self.conf['server']['uroot']))
        
    def deleteuser(self,user): #删除用户
        home=self.conf['server']['path']+'/'+user
        os.system("rm -rf %s" %home)
        os.system("userdel %s" %user)
        self.serverdb.execsql('delete from user where name="%s"' %user)
        return True
    
    def checkpath(self,user,path):
        home=self.conf['server']['path']+'/'+user
        if path.find(home)==0:
            return True
        return False
###################################################################
class MyObject:
    """"""

    #----------------------------------------------------------------------
    def __init__(self,conf,log):
        """Constructor"""
        self.conf=conf
        self.log=log
        self.serverdb=serverdb()
        self.user=user(conf,self.serverdb)
    
    def sayHello(self):
        return "say hello test"
    
    def register(self,user,passwd,token):
        if not self.serverdb.has_token(token):
            return {"flag":1,"msg":"token not vaild"}
        try:
            passwd=self.user.encrypasswd(passwd)
            self.user.createuser(user,passwd)
            self.serverdb.execsql('delete from token where tokens="%s"' %token)
            return {"flag":0,"msg":"create user %s succfully" %user,"encrypwd":base64.encodestring(passwd).strip()}
        except Exception:
            e=str(sys.exc_info()[1])
            return {"flag":1,"msg":e}
    
    def changpwd(self,user,passwd,passwd_new):
        try:
            passwd=self.user.encrypasswd(passwd)
            passwd_new=self.user.encrypasswd(passwd_new)
            if self.user.checkpwd(user,passwd):
                self.user.changepwd(user, passwd, passwd_new)
                return {"flag":0,"msg":"%s passwd change succfully" %user,"encrypwd":base64.encodestring(passwd).strip()}
            return {"flag":1,"msg":"user/passwd not vaild"}
        except Exception:
            e=str(sys.exc_info()[1])
            return {"flag":2,"msg":e}
    
    def checkuser(self,user,passwd):
        try:    
            passwd=self.user.encrypasswd(passwd)
            if self.user.checkpwd(user,passwd):
                return {"flag":0,"msg":"user,passwd is vaild"}
            return {"flag":1,"msg":"user/passwd not vaild"}
        except Exception:  
            e=str(sys.exc_info()[1])   
            return {"flag":2,"msg":e}          
    
    def getuserperm(self,user,passwd):
        try:    
            passwd=self.user.encrypasswd(passwd)
            if self.user.checkpwd(user,passwd):
                rs=self.serverdb.execsql('select name,perm from user where name="%s"' %user)
                return {"flag":0,"msg":"get user perm succfully","perm":rs}
            return {"flag":1,"msg":"user/passwd not vaild"}
        except Exception:  
            e=str(sys.exc_info()[1])   
            return {"flag":2,"msg":e}  
        
    def setuserperm(self,m_user,m_passwd,user,perm):
        try:    
            if perm>0b1111:
                raise Exception("PermNotVaild")
            if self.checkmanage(m_user,m_passwd):#self.user.checkpwd(user,passwd):
                self.serverdb.execsql('update user set perm="%d" where name="%s"' %(perm,user))
                return {"flag":0,"msg":"set user perm succfully"}
            return {"flag":1,"msg":"user/passwd not vaild"}
        except Exception:  
            e=str(sys.exc_info()[1])   
            return {"flag":2,"msg":e}  
    
    def checkmanage(self,mu,mp):
        if self.conf['server']['manage_user']==mu and self.conf['server']['manage_passwd']==mp:
            return True
        return False
    
    def addtoken(self,m_user,m_passwd,token):
        if not self.checkmanage(m_user,m_passwd):
            return {"flag":1,"msg":"manage user/paswd not vaild"}
        try:
            self.serverdb.addtoken(token)
            return {"flag":0,"msg":"add token %s to db succfully" %token}
        except Exception:
            e=str(sys.exc_info()[1])
            print e
            return {"flag":1,"msg":e}
    
    def gettokenlist(self,m_user,m_passwd):
        if not self.checkmanage(m_user,m_passwd):
            return {"flag":1,"msg":"manage user/paswd not vaild"}        
        try:
            rs=self.serverdb.execsql("select tokens from token")
            return {"flag":0,"msg":"get token list succfully","token":rs}
        except Exception:
            e=str(sys.exc_info()[1])
            print e        
            
    def getuserlist(self,m_user,m_passwd):
        if not self.checkmanage(m_user,m_passwd):
            return {"flag":1,"msg":"manage user/paswd not vaild"}        
        try:
            rs=self.serverdb.execsql("select name from user")
            return {"flag":0,"msg":"get user list succfully","user":rs}
        except Exception:
            e=str(sys.exc_info()[1])
            print e        
            
    def deldir(self,user,passwd,remotep):
        passwd=self.user.encrypasswd(passwd)
        if not self.user.checkpwd(user, passwd):
            return {"flag":1,"msg":"user,passwd is not vaild"}
        if not self.user.checkpath(user,remotep):
            return {"flag":2,"msg":"Canot del the dir"}
        os.system("rm -rf %s" %remotep)
        return {"flag":0,"msg":"delete %s succfully" %remotep}

    def deleteuser(self,m_user,m_passwd,user):
        if not self.checkmanage(m_user,m_passwd):
            return {"flag":1,"msg":"manage user/paswd not vaild"}   
        try:
            self.user.deleteuser(user)
            return {"flag":0,"msg":"delete %s succfully" %user}
        except Exception:
            e=str(sys.exc_info()[1])
            return {"flag":2,"msg":e}
#========================================================================
class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):pass

if __name__ == "__main__":
    #新建xml-rpc服务器,单线程RPC
    try:
        os.mkdir('/var/log/detamper')
    except Exception:
        pass
    logging.basicConfig(
        level=logging.DEBUG,
        filename='/var/log/detamper/server.log',
        datefmt='%Y %b %d %H:%M:%S',
        format="%(levelname)s: %(asctime)s %(message)s",
        filemode='a',
    )    
    log = logging.getLogger('detamper_server')
    conf=lib.lib_config.ReadIni('conf/server.ini').get_with_dict()
    try:
        obj = MyObject(conf,log)
    except Exception:
        print sys.exc_info()[1]
        exit()
        
    server = SimpleXMLRPCServer((conf['server']['host'], int(conf['server']['port'])), allow_none=True)
    server.register_instance(obj)
    print "Listening on %s port %s....." %(conf['server']['host'], conf['server']['port'])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "exit rpc server!!!"