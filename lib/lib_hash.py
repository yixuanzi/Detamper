import hashlib
import os,sys


def CalcMD5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        return md5obj.hexdigest()
        
    
    
def CalcMD54h(fp):
    md5obj=hashlib.md5()
    md5objupdate(fp.read())
    return md5obj.hexdigest()