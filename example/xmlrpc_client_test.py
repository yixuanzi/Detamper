
# coding: utf-8

# In[72]:

import xmlrpclib

server = xmlrpclib.ServerProxy("http://localhost:8088")

server.sayHello()


# In[73]:

import xmlrpclib

serverx = xmlrpclib.ServerProxy("http://localhost:12345")

serverx.sayHello()


# In[83]:

server.getstatus('sftp','123456')


# In[76]:

server.download('sftp','123456','test','/tmp/tt','')


# In[81]:

server.stoprotect('sftp','123456')


# In[79]:

server.protect('sftp','123456','/home/lab8/Git/octa_detamper/test')


# In[82]:

server.backup('sftp','123456','/home/lab8/Desktop')


# In[84]:

server.changepwd('sftp','123456','12345678')


# In[103]:

serverx.register("test2","123456","jxust")


# In[113]:

serverx.getuserlist('admin','123456')


# In[112]:

serverx.deleteuser("admin","123456",'test1')


# In[100]:

serverx.addtoken('admin','123456','jxust')


# In[101]:

serverx.gettokenlist('admin','123456')


# In[ ]:

serverx.changpwd('test1','123456','12345678')

