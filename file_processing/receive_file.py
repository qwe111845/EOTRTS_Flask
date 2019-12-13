# -*- coding: utf-8 -*-
import os
import threading


def check_exist(sid):
    path = r'C:\Users\lin\Desktop\Django_Apache\EOTRTS_Flask\record//'
    path_list = os.listdir(path)
    have_dir = False
    for item in path_list:
        if item == sid:
            have_dir = True
        else:
            pass
    if not have_dir:
        os.mkdir(path + sid, 0x0755)
        print('Dir not found! make new dir ' + sid)


