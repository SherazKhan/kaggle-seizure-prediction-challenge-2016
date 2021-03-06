import numpy as np
import json
import os
from scipy.io import loadmat
from pandas import DataFrame
from sklearn.preprocessing import StandardScaler
from config_name_creator import create_fft_data_name
from sklearn import linear_model

def load_train_data_lasso(data_path, subject):
    read_dir = data_path + '/' + subject
    filenames = sorted(os.listdir(read_dir))

    train_filenames = []
    for filename in filenames:
        train_filenames.append(filename)
    n = len(train_filenames)
    datum = loadmat(read_dir + '/' + train_filenames[1], squeeze_me=True)
    x = np.zeros(((n,) + datum['data'].shape), dtype='float32')
    y = np.zeros(n, dtype='int8')

    filename_to_idx = {}
    for i, filename in enumerate(train_filenames):
        datum = loadmat(read_dir + '/' + filename, squeeze_me=True)
        x[i] = datum['data']
        y[i] = 1 if filename.endswith('_1.mat') else 0
        filename_to_idx[subject + '/' + filename] = i

    return {'x': x, 'y': y, 'filename_to_idx': filename_to_idx}

def reshape_data(x, y=None):
    n_examples = x.shape[0]
    n_timesteps = x.shape[1]
    n_features=x.shape[2]


    x_new = x.reshape((n_examples * n_timesteps,n_features ))
    if y is not None:
        y_new = np.repeat(y, n_timesteps) ## expanding the sample size
        return x_new, y_new
    else:
        return x_new


def load_test_data(data_path, subject):
    read_dir = data_path + '/' + subject
    data, id = [], []
    filenames = sorted(os.listdir(read_dir))
    #filenames=filenames[1:]
    for filename in sorted(filenames): #key=lambda x: int(re.search(r'(\d+).mat', x).group(1))):
        if '.mat' in filename:
            data.append(loadmat(read_dir + '/' + filename, squeeze_me=True))
            id.append(filename)

    n_test = len(data)
    x = np.zeros(((n_test,) + data[0]['data'].shape), dtype='float32')
    for i, datum in enumerate(data):
        x[i] = datum['data']

    return {'x': x, 'id': id}

def train(subject, data_path, plot=False):
    d = load_train_data_lasso(data_path, subject)
    x, y = d['x'], d['y']
    print 'n_preictal', np.sum(y)
    print 'n_inetrictal', np.sum(1-y)
    n_channels = x.shape[1]
    n_fbins = x.shape[2]

    x, y = reshape_data(x, y)
    x[np.isneginf(x)] = 0
    data_scaler = StandardScaler()
    x = data_scaler.fit_transform(x) ## Normalizaiton
    logreg = linear_model.LogisticRegression(penalty='l2',C=0.6)
    logreg.fit(x, y)
    return logreg, data_scaler

def predict(subject, model, data_scaler, data_path):
    d = load_test_data(data_path, subject)
    x_test, id = d['x'], d['id']
    n_test_examples = x_test.shape[0]
    n_timesteps = x_test.shape[1]

    x_test = reshape_data(x_test)
    x_test[np.isneginf(x_test)] = 0
    x_test = data_scaler.transform(x_test)

    pred_1m = model.predict_proba(x_test)[:,1]


    pred_10m = np.reshape(pred_1m, (n_test_examples, n_timesteps))
    pred_10m = np.mean(pred_10m, axis=1)
    ans = zip(id, pred_10m)
    #df = DataFrame(data=ans, columns=['File', 'Class'])
    return ans

## you need to do change the window size to 50s in kaggle_SETTINGS.json
with open('kaggle_SETTINGS_more.json') as f:
    settings_dict = json.load(f)
data_path= settings_dict['path']['processed_data_path'] + '/combine'+ create_fft_data_name(settings_dict)
submission_path=settings_dict['path']['submission_path']+'/'

def get_prediction():
    train_subjects=['train_1','train_2','train_3']
    test_subjects=['test_1_new','test_2_new','test_3_new']

    pred=[]
    for i in range(3):
        model,data_scaler=train(train_subjects[i],data_path)
        singpred=predict(test_subjects[i],model,data_scaler,data_path)
        pred=pred+singpred
    df = DataFrame(data=pred, columns=['File', 'Class'])
    return df
#generate dataframe
df=get_prediction()
df.to_csv(submission_path+"Feng_glmmorefeature.csv",index=False, header=True)
