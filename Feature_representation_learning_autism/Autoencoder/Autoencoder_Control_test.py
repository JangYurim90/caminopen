import os
import skimage.io
import skimage.transform
from scipy import io
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from tqdm import tqdm, tqdm_notebook
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from os.path import join
import torch
from torch import nn
import ast
from ast import literal_eval

path='/camin1/yrjang/Autism classification/abide2/diff/Schaefer_200/'
file_list=os.listdir(path)
file_list_py=[file for file in file_list if file.endswith('_DC.mat')]
conZ_1r=[]
for i in file_list_py:
    mat_file=io.loadmat(path+i)
    connmat=mat_file['diff_ConnMat']
    conZ_1r.append(connmat)
conZ_1r=np.array(conZ_1r)

file=pd.read_excel('/camin1/yrjang/Autism classification/abide2/subjects.xlsx')

# Age & Site & Sex control
grp = file['Gk_II'].values
age = file['Ak_II'].values
sex = file['GENDER_II'].values
site = file['Sk_II'].values

grp_ = np.where(grp=='ASD', 1, grp)
grp_ = np.where(grp_=='CONTROL', 2, grp_)
grp = grp_.astype('int64')

sex_ = np.where(sex=='M', 1, sex)
sex_ = np.where(sex_=='F', 2, sex_)
sex = sex_.astype('int64')

site_ = np.where(site=='TCD', 1, site)
site_ = np.where(site_=='NYU', 2, site_)
site = site_.astype('int64')

NumSubj = np.size(grp)

NumROI=200
ConnMatZ2 = np.zeros((np.size(file_list_py), NumROI,NumROI))
ConnMatZ2_reg = np.zeros((np.size(file_list_py), NumROI,NumROI))

for nr1 in range(0,NumROI):
    for nr2 in range(0,NumROI):
        x = np.transpose([age, sex,site])
        y = np.expand_dims(conZ_1r[:,nr1,nr2], axis=1)
        lm = LinearRegression()
        lm.fit(x,y)
        ConnMatZ2_reg[:,nr1,nr2] = np.squeeze(y - lm.predict(x))

feat2=ConnMatZ2_reg

#Flatten
hemi=[]
hemi2=[]
for num in range(0,84):
    for Left in range(0,100):
        if i == 99:
            break
        for j in range (0+Left,99):
            hemi.append(feat2[num][Left][j+1])
    for right in range (100,200):
        if i == 199:
            break
        for r in range (100+(right-100),199):
            hemi.append(feat2[num][right][r+1])
    hemi2.append(hemi)
    hemi=[]
x=np.array(hemi2)
df_con1=[x[i] for i in range(0,84)]

file['data']=df_con1



# Autoencoder code
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm

fea_orig = 9900   #[630, 420, 200, 120]
fea1 = 7700
fea2 = 5500
fea3 = 2930
fea4 = 900
fea5 = 200


# LeakyReLU ReLU Tanh
# Tanh 고정 제일 performance 좋음

class AutoEncoder(nn.Module):
    def __init__(self):
        super(AutoEncoder, self).__init__()
        self.dropout = nn.Dropout(p=0.3 )
        self.encoder1 = nn.Sequential(
            nn.Linear(fea_orig, fea1),
            nn.Tanh())

        self.encoder2 = nn.Sequential(
            nn.Linear(fea1, fea2),
            nn.Tanh())

        self.encoder3 = nn.Sequential(
            nn.Linear(fea2, fea3),
            nn.Tanh())
        self.encoder4 = nn.Sequential(
            nn.Linear(fea3, fea4),
            nn.Tanh())
        self.encoder5 = nn.Sequential(
            nn.Linear(fea4, fea5),
            nn.Tanh())

        self.decoder5 = nn.Sequential(
            nn.Linear(fea5, fea4),
            nn.Tanh())

        self.decoder4 = nn.Sequential(
            nn.Linear(fea4, fea3),
            nn.Tanh())

        self.decoder3 = nn.Sequential(
            nn.Linear(fea3, fea2),
            nn.Tanh())

        self.decoder2 = nn.Sequential(
            nn.Linear(fea2, fea1),
            nn.Tanh())
        self.decoder1 = nn.Sequential(
            nn.Linear(fea1, fea_orig))

    #             nn.Tanh())

    def forward(self, x):
        x = self.dropout(x)
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)
        latent = self.encoder5(e4)
        d5 = self.decoder5(latent)
        d4 = self.decoder4(d5)
        d3 = self.decoder3(d4)
        d2 = self.decoder2(d3)
        x = self.decoder1(d2)

        return x, latent

def fit(model, dataloader, layer, loss_show=True):
    model.eval()
    running_loss = 0.0
    running_KLD_loss = 0.0

    y_list = []
    y_hat_list = []
    x_list = []
    x_hat_list = []
    recon_loss_list = []
    reg_loss_list = []
    vae_loss_list = []

    total_predict = []
    total_y_pred = []
    cla_loss_list = []
    latent_test_list = []

    alpha = 1
    for i, data in enumerate(dataloader):
        x = data[0]
        x = x.to(device)
        #x = x.view(x.size(0), -1)


        #         y = data[1]
        #         y = y.to(device)
        #         y = y.view(y.size(0), -1)
        #             print('y',y)
        if layer == 'AE':
            x_hat, latent_test = model(x.float())
            recon_loss = criterion(x.float(), x_hat.float())
            loss = recon_loss

            x_list.append(x)
            x_hat_list.append(x_hat)
            recon_loss_list.append(recon_loss.item())
            latent_test_list.append(latent_test)
        #         del y

        del x
        torch.cuda.empty_cache()


    #         print('output',output[:,:3])
    #         print('data',data[:,:3])

    test_loss = running_loss / len(dataloader.dataset)
    if loss_show:
        print(f"Train Loss: {test_loss:.4f}")


    return test_loss, x_list, x_hat_list,  recon_loss_list,  latent_test_list

from copy import deepcopy
from torch.optim import Adam, lr_scheduler
cor_test_500=[]
p_test_500=[]
for n in range(0,100):
    # ASD / Control data split
    file_asd = file[file['Gk_II'] == 'ASD']
    file_con = file[file['Gk_II'] == 'CONTROL']

    train1_asdf, val_asdf = train_test_split(file_asd, train_size=0.75, shuffle=True, random_state=5)
    train_asdf, test_asdf = train_test_split(train1_asdf, train_size=0.75, shuffle=True, random_state=5)

    train_asd_d_ = []
    train_asd_d = train_asdf['data'].values
    val_asd_d = val_asdf['data'].values
    test_asd_d = test_asdf['data'].values

    train1_conf, val_conf = train_test_split(file_con, train_size=0.75, shuffle=True, random_state=2)
    train_conf, test_conf = train_test_split(train1_conf, train_size=0.75, shuffle=True, random_state=2)

    train_con_d = train_conf['data'].values
    val_con_d = val_conf['data'].values
    test_con_d = test_conf['data'].values

    # Data_loader
    batch_size = 2
    asd_train_loader = DataLoader(train_asd_d, batch_size=batch_size, shuffle=True, drop_last=True)
    asd_val_loader = DataLoader(val_asd_d, batch_size=batch_size, shuffle=True, drop_last=True)
    asd_test_loader = DataLoader(test_asd_d, batch_size=batch_size, shuffle=True, drop_last=True)

    con_train_loader = DataLoader(train_con_d, batch_size=batch_size, shuffle=True, drop_last=True)
    con_val_loader = DataLoader(val_con_d, batch_size=batch_size, shuffle=True, drop_last=True)
    con_test_loader = DataLoader(test_con_d, batch_size=batch_size, shuffle=True, drop_last=True)

    layer = 'AE'

    model = AutoEncoder().to(device='cuda')


    lr = 0.0001
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    main_path = "/camin1/yrjang/Autism classification/Checkpoint_auto/model"
    save_path = join(main_path, 'log_c')

    optimizer = torch.optim.ASGD(model.parameters(), lr=lr, weight_decay=0.1)
    lr_decay = lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.95)
    criterion = nn.MSELoss(reduction='sum')

    load_test_model = join(save_path,'_best_AE_epoch420.pkl')
    model.load_state_dict(torch.load(load_test_model),strict=False)



    test_epoch_loss, x_test, x_hat_test, recon_loss_list_test, latent_test = fit(model, con_test_loader, layer, loss_show=True)

    x_test_n = []
    x_hat_test_n = []
    # x_n=[]
    # x_hat_n=[]
    for i in range(0, 3):
        x_n = []
        x_hat_n = []
        for num in range(0, 9900):
            x_n.append(x_test[i][num].cpu().detach().numpy().tolist())
            x_hat_n.append(x_hat_test[i][num].cpu().detach().numpy().tolist())
        x_test_n.append(x_n)
        x_hat_test_n.append(x_hat_n)


    import scipy.stats as stats
    from sklearn.metrics import mean_absolute_error, r2_score

    mean_cor = []
    mean_pvalue = []
    for num in range(0, np.array(x_test_n).shape[0]):
        cor, p = stats.pearsonr(x_test_n[num], x_hat_test_n[num])
        mean_cor.append(cor)
        mean_pvalue.append(p)
    cor_m = np.mean(mean_cor)
    p_m = np.mean(mean_pvalue)

    cor_test_500.append(cor_m)
    p_test_500.append(p_m)
    print("-------------------------------------")
    print(n)
    print("correlation coefficient : ", cor_m, "p-value : ", p_m)
    print("r2_score : ", r2_score(x_test_n,x_hat_test_n))
    print("MAE : ", mean_absolute_error(x_test_n, x_hat_test_n))

print("------test-------")
print("cor_test : ",cor_test_500)
print("cor_test mean: ",np.mean(cor_test_500))
print("cor_test std : ",np.std(cor_test_500))
print("end")
