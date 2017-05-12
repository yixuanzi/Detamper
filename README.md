#octa_detamper 一个防篡改软件
###Author：guoguisheng
###Date:2017-05-02
###Email：guoguisheng@8lab.cn
###Version:2.0.0

#概述
detamper,是一个基于cs模式的防篡改程序，服务端采用sftp进行备份恢复，支持本地测试</br>
包含服务器和客户端，整个系统通过RPC接口对外提供服务

#Server
##config
编辑conf/server.ini,根据其中的详细描述配置

##request
sftp server

##exec 
```python
python detamper_server.py
```

##服务端接口
	1.账户申请注册（user,passwd,token)=>(user,passwd)
	2.添加token(m_user,m_passwd,token)=>flag_status
	3.当前有效token(m_user,m_passwd)=>list(token)
	4.修改密码（user,passwd)=>flag_status
	5.返回用户列表（m_user,m_passwd)=>list(user)
	6.删除用户（m_user,m_passwd,user)=>flag_status


------------
#Client
##config
编辑conf/server.ini,根据其中的详细描述配置


##request
python lib:watchdog 

##客户端接口
	1.修改密码（user,passwd,passwd_new)=>flag_status
	2.获取当前状态（user,passwd)=>status_json
	3.备份更新（user,passwd,localp)=>flag_status(backup_name)
	4.防篡改保护(user,passwd,localp)=>flag_status
	5.停止防篡改保护(user,passwd)=>flag_status
	6.下载备份文件(user,passwd,backup_name,dst,remote_path)=>flag_status
	7.删除备份（user,passwd,backup_name)=>flag_status

##exec
python detamper.py
