#coding=utf8
import os
import sys
import logging
import time
import getopt
import base64

import lib.lib_config
import core.main
log = logging.getLogger('detamper')

def use():
    print "Python detamper.py [-m backup]"
    print "-m :work model, backup|protect"
    exit()

def setconf(conf,options):
    for kv in options:
        if kv[0]=='-m':
            conf['system']['model']=kv[1]
        if kv[0]=='-u':
            conf['server']['user']=kv[1]
        if kv[0]=='-p':
            conf['server']['password']=kv[1]
        else:
            log.error("have not map options with "+str(kv))

if __name__ == "__main__":
    #远程必须创建相应的根目录
    try:
        os.mkdir('/var/log/detamper')
    except Exception:
        pass
    logging.basicConfig(
        level=logging.DEBUG,
        filename='/var/log/detamper/message.log',
        datefmt='%Y %b %d %H:%M:%S',
        format="%(levelname)s: %(asctime)s %(message)s",
        filemode='a',
    )    
    conf=lib.lib_config.ReadIni('conf/detamper.ini').get_with_dict()

    if not conf:
        log.error("Can't parse config file,check conf/detamper.ini")
        exit()
    try:
        options,args=getopt.getopt(sys.argv[1:],"m:h")
    except Exception:
        log.error(sys.exc_info()[1])
    #setconf(conf,options)
    conf['server']['password']=base64.decodestring(conf['server']['password'])
    core.main.main(conf,log)
    