import xmlrpclib

server = xmlrpclib.ServerProxy("http://localhost:1234")

print server.sayHello()

server.backup('sftp','123456','/home/lab8/Git/octa_detamper/test')
server.protect('sftp','123456','/home/lab8/Git/octa_detamper/test')
server.stoprotect('sftp','123456')
server.getstatus('sftp','123456')