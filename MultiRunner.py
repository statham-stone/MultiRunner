# author:Statham
# time:2018-03-21
# email:statham dot stone at gmail DOTcom
# This package is dedicated to my girlfriend 10L.
# ALL RIGHTS RESERVED

import itertools
import os
import pickle
import random
import traceback
import time

class MultiRunner():
    def __init__(self,ini_dir="./ini/",result_dir="./results/",max_error_times=5,if_log=True):
        if ini_dir[-1]!="/":
            ini_dir+="/"
        if result_dir[-1]!="/":
            result_dir+="/"
        self.ini_dir=ini_dir
        self.max_error_times=max_error_times
        self.result_dir=result_dir
        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        self.if_log=if_log

    def _get_ini_handle(self):
        os.mknod(self.ini_dir+"generate_ini_handle_prepara")
        if os.path.exists(self.ini_dir+"generate_ini_handle_got"):
            return 0            
        try:
            os.rename(self.ini_dir+"generate_ini_handle_prepara",self.ini_dir+"generate_ini_handle_got")
            return 1
        except Exception:
            return 0    

    def generate_ini(self,args_list,reserve_old_ini=True,show_ini=False):
        if not os.path.exists(self.ini_dir):
            os.mkdir(self.ini_dir)
        else:
            if len(os.listdir(self.ini_dir))>0:
                if reserve_old_ini:
                    if self.if_log:
                        print("Ini files already generated.")
                    return
                else:
                    if self.if_log:
                        print("There are old ini files to be deleted.\nPlease delete the old ini files manually and try again.")
                    return
        count=1
        if self._get_ini_handle()==0:
            return

        for i in itertools.product(*args_list):
            if show_ini:
                print(i)
            pickle.dump(i,open(self.ini_dir+str(count)+"_to_run","w"))
            count+=1
        count-=1
        
        os.remove(self.ini_dir+"generate_ini_handle_got")
        if os.path.exists(self.ini_dir+"generate_ini_handle_prepara"):
            os.remove(self.ini_dir+"generate_ini_handle_prepara")
        if self.if_log:
            print("All "+str(count)+" ini files generated.")
        
    def _find_files(self,_type):
        all_files=filter(lambda x:x[0]!=".",os.listdir(self.ini_dir))
        return filter(lambda x:x[-len(_type):]==_type,all_files)
        
    def _return_a_para(self):
        this_para=[]
        while(this_para==[] and len(self._find_files("_to_run"))>0):
            choises=self._find_files("_to_run")
            if len(choises)==0:
                return [],-1
            else:
                my_choise=choises[random.randint(0,len(choises)-1)]
                new_name=self.ini_dir+my_choise[:-7]+"_running"
                try:
                    os.rename(self.ini_dir+my_choise,new_name)      
                    this_para=pickle.load(open(new_name,"r"))
                    return this_para,new_name
                except OSError:
                    pass
                
        #below is for this situation: 3 node is running, node 1 is very slow and  node 2 3 are fast,only 1 job running in node1
        while(this_para==[] and len(self._find_files("_running"))>0 and len(self._find_files("_to_run"))==0):
            choises=self._find_files("running")
            this_choise=choises[random.randint(0,len(choises)-1)]
            this_para=pickle.load(open(self.ini_dir+this_choise,"r"))
            return this_para,self.ini_dir+this_choise
        
        return [],-1
    
    def run(self,main_function,if_torch_use_best_nvidia_gpu=0,error_wait_time=10):
        error_time=0
        import numpy as np  
        if if_torch_use_best_nvidia_gpu:       
            import torch
        if if_torch_use_best_nvidia_gpu and torch.cuda.is_available():
            all_lines=[]
            all_percent=[]
            for i in os.popen("nvidia-smi"):
                all_lines.append(i)
            all_lines=filter(lambda x:x.find("MiB")>-1,all_lines)
            num=np.array(map(lambda y:float(y[0][:-3])/float(y[1][:-3]),filter(lambda j:len(j)==2,map(lambda x:filter(lambda k:k.find("MiB")>-1,x.split(" ")),all_lines)))).argmin()
            torch.cuda.set_device(num)
            if self.if_log:
                print("Use gpu: "+str(num))

        while(error_time<self.max_error_times): 
            find_a_para,para_path=self._return_a_para()
            if find_a_para==[]:
                if self.if_log:
                    print("All finished, no new task to run.")
                break
            else:
                try:
                    result=main_function(*find_a_para)
                    if os.path.isfile(para_path[:-8]+"_finished"):
                        if self.if_log:
                            print("This job is already done by others")
                    else:# maybe running by others at the same time
                        pickle.dump(result,open(self.result_dir+para_path[len(self.ini_dir):-8],"w"))
                        try:
                            os.rename(para_path,para_path[:-8]+"_finished")
                        except Exception:
                            try:
                                os.rename(para_path[:-8]+"_to_run",para_path[:-8]+"_finished") 
                            except Exception:
                                pass

                except Exception:
                    error_time+=1
                    if self.if_log:
                        print("Error info:")
                        traceback.print_exc()
                        print("Error! Total error times: "+str(error_time))
                        time.sleep(error_wait_time*random.random())
                    try:
                        os.rename(para_path,para_path[:-8]+"_to_run")
                        if self.if_log:
                            print("Rename"+para_path+" to "+para_path[:-8]+"_to_run")
                    except Exception: #changed to finished or torun by others
                        if self.if_log:
                            print("This job is already done or reverted by others")
                    
            if error_time>=self.max_error_times:
                if self.if_log:
                    print("Too many error times, break.")
