import csv
import time
import numpy as np


from copy import deepcopy
from operator import mul
from AS import AnalyticsServer
from CSP import CSProvider
from DO import DOwner
from QueryEngine import QueryParsing

import _pickle as cPickle

mask=[]
mpk = None


def multi(multiplicands,num_DO):
    global mask
    s=len(multiplicands[0])
    mask=[[] for x in range(s//2)]
    extra=[]
    if(s%2==1):
       extra=[[] for x in range()]
       for i in range(num_DO):
           extra.append(multiplicands[i][s-1])
    intmdt_pro=[[] for x in range(s//2)]  
    pks=[[]for x in range(s)]    
    for i in range(s//2):
        for j in range(num_DO):
            mask[i].append(np.random.randint(10000,20000))
         
            c=mul(multiplicands[j][i*2],multiplicands[j][i*2+1])
            c+=mask[i][j]
            pks[i*2].append(multiplicands[j][i*2].sigma)
            pks[i*2+1].append(multiplicands[j][i*2+1].sigma)
            intmdt_pro[i].append(c)
    return intmdt_pro,extra,pks

def multi2(intmdt_pro,extra):
        global mask,mpk
        n=len(intmdt_pro)
        for i in range(n):
             for j in range(num_DO):
                 intmdt_pro[i][j].hm-=mask[i][j]
        mask=[[] for x in range(n//2+1)]
        intmdt_pro_out=[[] for x in range(n//2 + 1)]
        pks=[[] for x in range(n+2)]
        if(n%2==1 and len(extra) > 0):
             for i in range(self.num_DO):
                 mask[n//2].append(random.randint(10000,20000))
                 temp=mul(extra[i],intmdt_pro[n-1][i])
                 temp+=mpk.encrypt(mask[n//2][i])
                 intmdt_pro_out[n//2].append(temp)
                 pks[n][i]=extra[i].sigma
                 pks[n+1][i]=intmdt_pro[n-1][i].sigma
             extra=[]
        elif(n%2==1 and len(extra)==0):
             for i in range(num_DO):
                 extra.append(intmdt_pro[n-1][i])


        for i in range(n//2):
            for j in range(num_DO):
                temp=mul(intmdt_pro[i*2][j],intmdt_pro[i*2+1][j])
                mask[i].append(random.randint(10000,20000))
                temp=temp+mpk.encrypt(mask[i][j])
                intmdt_pro_out[i].append(temp)
                pks[i*2][j]=intmdt_pro[i*2][j].sigma
                pks[i*2+1][j]=intmdt_pro[i*2+1][j].sigma
        
        return intmdt_pro_out,extra,pks

def evaluate_CP(inputfile, num_DO, attr1,attr2,e):
    """
    compute 
    :param inputfile : Data file 
    :param num_DOs: the number of Data Owners
    :param attr1:Cross Product attributes
    :param attr2:Cross Product attributes
    :param e: the privacy budget
    :return : return noisy count for Q
    """
    global mpk, mask
    domain_s=[1,1,20,100]
    domain_e=[2,100,25,120]
    l=3
    D=[[] for i in range(num_DO)]
    #Generate Dataset

    
    with open(str(inputfile)) as csv_file:
     csv_reader = csv.reader(csv_file, delimiter=',')
     line_count = 0
     i=0    
     for row in csv_reader:
        if(line_count<num_DO):
           D[line_count]=row
           line_count=line_count+1
        else:
           break
       

    '''Start Secure protocol computation'''
    n_length=2048
	
 

    # declare CSP & MLE & DOwners
    csp = CSProvider()
    As = AnalyticsServer()
    DOwners = []
    for index in range(num_DO):
        DOwners.append(DOwner(D[index],domain_s,domain_e))
   




    print('Phase 1 : Protocol Laplace-DO')  
    # declare Crypto Service Provider(CSP) & Phase1 step1
    start_P11 = time.time()
    csp.key_gen(n_length)
    end_P11 = time.time()

    # publish public_key to AS & Downers
    mpk=csp.get_MPK()
    As.set_PK(csp.get_MPK())
    for d_owner in DOwners:
        d_owner.set_MPK(csp.get_MPK())    

    # Phase1 step2
    start_P12 = time.time()     
    for d_owner in DOwners:
        d_owner.computeEnc_X()
    end_P12 = time.time()

    # Phase2 Step 1
    print('Phase 2 : Protocol CrossProduct-AS')
    start_P21 = time.time()
    pk=[]
    for d_owner in DOwners:
        enc_Xi = d_owner.getEnc_X()
        pk.append(d_owner.getEnc_Seed())
        #as merges enc_Xi
        As.add_enc_X(enc_Xi,num_DO)
    end_P21 = time.time()
    
    
    print ('Export As Encrypted Data...')
    cPickle.dump(As,open("./10000-as.pkl","wb"))
    cPickle.dump(csp,open("./10000-csp.pkl","wb"))


    #aspk=As.getpk()
    #for d_owner in DOwners:
        #pks.append(d_owner.getpk)
        
    #AS Cros Product
    start_P22 = time.time()
    pk1,pk2,newTable=As.CrossProduct2(attr1,attr2)
    end_P22 = time.time()
    
    #AS Projection
    start_P23 = time.time()
    enc_X_afterProjection=As.ProjectionT(newTable,[l-2],l-1)
    end_P23 = time.time()
    
    
    #CSP Gen LabProduct
    start_P24 = time.time()
    C=csp.generate_labEncProduct2(enc_X_afterProjection,pk1,pk2,num_DO)
    end_P24 = time.time()
    
    #AS gen Groupby
    start_P25 = time.time()
    C=As.generateEncCount_GroupBy(enc_X_afterProjection)
    end_P25 = time.time()
    
    #AS add noise
    start_P26 = time.time()
    C1=As.Laplace_vectorLHE(e,C)
    end_P26 = time.time()
    
    #CSP add noise
    start_P27 = time.time()
    C2=csp.Lap_mul_decrypt(C1,pk1,pk2,num_DO,e) 
    end_P27 = time.time()
    
    #The following to return accuracy 
    C3 = csp.mul_decrypt(C,pk1,pk2,num_DO)
    #C3 is the real count
    #C2 is the noisy count
    #print (C2)
    #print (C3)
    
    l1_err = 0
    for i in range(len(C2)):
        l1_err += abs(int(C2[i]) - int(C3[i]))
        
    return l1_err
    
    '''
    
    print('Runtime(KeyGen) = ', end_P11 - start_P11)
    print('Runtime(DO_ComputeEncX) = ', (end_P12 - start_P12)/num_DO )
    print('Runtime(AS_MergeEncX) = ', end_P21 - start_P21)
    print('Runtime(AS_Cros_Product) = ', end_P22 - start_P22)
    print('Runtime(AS_Projection) = ', end_P23 - start_P23)
    print('Runtime(CSP_Gen_LabProduct) = ', end_P24 - start_P24)
    print('Runtime(AS_Gen_Groupby) = ', end_P25 - start_P25)
    print('Runtime(AS_add_noise) = ', end_P26 - start_P26)
    print('Runtime(CSP_add_noise) = ', end_P27 - start_P27)
    '''
    
    #test_stub
    '''
    reps = 10
    for i in range(10):
        e = 0.1 + 0.2*i
        err_arr = np.zeros(reps)
        for k in range(reps):
            C1=As.Laplace_vectorLHE(e,C)
            C2=csp.Lap_mul_decrypt(C1,pk1,pk2,num_DO,e)
            l1_err = 0
            for j in range(len(C2)):
                l1_err += abs(int(C2[j]) - int(C3[j]))
            err_arr[k] = l1_err
        print('Privacy Parameter = ', e)
        print('Avg L1 Err = ', np.mean(err_arr))
        print('Std L1 Err = ', np.std(err_arr))
        print(' ')
    '''
        
        
        

