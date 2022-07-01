# -*- coding: utf-8 -*-
"""intent_classification_helper..py
helper functions for the intent classification case study
"""

import pandas as pd
import re
import nltk
import os
import numpy as np
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import WordNetLemmatizer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from imblearn.over_sampling import RandomOverSampler
import json
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
import joblib
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import roc_auc_score
import tensorflow as tf
from tensorflow import keras
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras import Sequential
from keras.layers import Conv1D
from keras.layers import GlobalMaxPooling1D
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Embedding
from keras.callbacks import ModelCheckpoint
from keras import callbacks

def preprocess_text(df, text_index, to_lowercase=True, remove_html_tags=True, remove_html_list=['<br />'], remove_nonword_chars=True, remove_stopwords=True, stowords_language='english', 
                        customized_stopwords=None, lemmatize=False):
    print('\n')
    print('Start text preprocessing: ')
    text_lst = df[text_index].tolist()
    if to_lowercase:
      print('--------------------------')
      print('Converting to lowercase...')
      for i in range(len(text_lst)):
        text_lst[i] = text_lst[i].strip().lower()

    if remove_html_tags:
      print('--------------------------')
      print('Removing html tags...')
      for i in range(len(text_lst)):
        text_lst[i] = re.sub(r'<br />', '', text_lst[i])

    if remove_nonword_chars:
      print('--------------------------')
      print('Removing nonword characters...')
      for i in range(len(text_lst)):
        text_lst[i] = re.sub(r'[\W]', ' ', text_lst[i])
    
    if remove_stopwords:
      print('--------------------------')
      print('Removing stopwords...')
      if customized_stopwords==None:
        nltk.download('stopwords')
        nltk.download('wordnet')
        stop_words = nltk.corpus.stopwords.words(stowords_language)
      else:
        stop_words = customized_stopwords
      for i in range(len(text_lst)):
        tokens = WordPunctTokenizer().tokenize(text_lst[i])
        tokens_cleaned = [i for i in tokens if i not in stop_words]
        text_lst[i] = ' '.join(tokens_cleaned)
      
    text_df = pd.DataFrame(text_lst, columns=[text_index])
    df[text_index] = text_df
    
    print('Text preprocessing completed.')
    print('\n')

def random_foreset_classifier(num_features, n_estimators=100, max_depth=None):
  model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
  model.fit(x_train, y_train)

  path = '/content/drive/MyDrive/nlp_datasets/CLINC150/models/'
  if not os.path.isdir(path):
    os.mkdir(path)

  #joblib.dump(model, os.path.join(path, 'random_foreset_n_estimators={}_max_depth={}.json'.format(n_estimators, max_depth)))
  joblib.dump(model, os.path.join(path, 'random_foreset_{}_features_n_estimators={}_max_depth={}.json'.format(num_features, n_estimators, max_depth)))
  return model

# evaluate the model and save result 
def evaluate_model(model, name, x_test, y_test, num_features):
  print('evaluate the model: ', name)
  prediction = model.predict(x_test)
  prediction = np.argmax(prediction, axis=1)
  y_true = np.argmax(y_test, axis=1)

  accuracy_score_val = accuracy_score(y_true, prediction)
  balanced_accuracy = balanced_accuracy_score(y_true, prediction)
  weighted_precision = precision_score(y_true, prediction, average='weighted')
  weighted_recall = recall_score(y_true, prediction, average='weighted')
  weighted_f1_score_val = f1_score(y_true, prediction, average='weighted')
  macro_f1_score_val = f1_score(y_true, prediction, average='macro')
  #roc_auc = roc_auc_score(y_test, model.predict_proba(x_test), multi_class='ovr') # use multi_class='ovr' or multi_class='ovo'?

  print("accuracy score: ", accuracy_score_val)
  print("balanced accuracy score: ", balanced_accuracy)
  print("weighted precision: ", weighted_precision)
  print("weighted recall: ", weighted_recall)
  print("weighted f1 score: ", weighted_f1_score_val)
  print("macro f1 score: ", macro_f1_score_val)
  #print("roc-auc: ", roc_auc)
  
  path = '/content/drive/MyDrive/nlp_datasets/CLINC150/models/'
  if not os.path.isdir(path):
    os.mkdir(path)

  #eval_path = os.path.join(path, 'evaluation.csv')
  eval_path = os.path.join(path, 'evaluation_cnn.csv')
  if not os.path.isfile(eval_path):
    eval_result = pd.DataFrame({'model': [name], 'accuracy score': [accuracy_score_val], 'balanced accuracy score': [balanced_accuracy],
                                'weighted precision': [weighted_precision], 'weighted recall': [weighted_recall],
                                'weighted f1 score': [weighted_f1_score_val], 'macro f1 score': [macro_f1_score_val], 'num_features': [num_features]})
    eval_result.to_csv(eval_path, index=False)
  else:
    eval_result = pd.read_csv(eval_path, error_bad_lines=False, engine='python', encoding='utf-8')
    eval_result = eval_result.append({'model': name, 'accuracy score': accuracy_score_val, 'balanced accuracy score': balanced_accuracy,
                                      'weighted precision': weighted_precision, 'weighted recall': weighted_recall,
                                      'weighted f1 score': weighted_f1_score_val, 'macro f1 score': macro_f1_score_val, 'num_features': num_features}, ignore_index=True)
    eval_result.to_csv(eval_path, index=False)

# cnn
def cnn(x_train_cnn, y_train_cnn, batch_size=32, epochs=20, validation_data, feature_numbers):
  model = Sequential()
  #model.add(Embedding(input_dim=len(tokenizer.word_index) + 1, output_dim=64, input_length=input_length))
  #model.add(Conv1D(filters=512, kernel_size=3, activation='relu'))
  model.add(Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(x_train_cnn.shape[1], 1)))

  model.add(GlobalMaxPooling1D())
  model.add(Dense(units=256, activation='relu'))
  model.add(Dropout(0.2))
  model.add(Dense(units=150, activation='sigmoid'))
  model.compile(optimizer='adam', loss='CategoricalCrossentropy', metrics=['accuracy'])

  # path = '/content/drive/MyDrive/nlp_datasets/CLINC150/models/'
  # path = os.path.join(path, 'cnn_{}_features'.format(feature_numbers))
  # if not os.path.isdir(path):
  #   os.mkdir(path)

  #checkpoint = ModelCheckpoint(filepath=path, monitor='val_accuracy')

  #model.fit(x_train_cnn, y_train_cnn, batch_size=batch_size, epochs=epochs, validation_data=validation_data, callbacks=[checkpoint])
  model.fit(x_train_cnn, y_train_cnn, batch_size=batch_size, epochs=epochs, validation_data=validation_data)

  return model