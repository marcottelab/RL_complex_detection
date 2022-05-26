# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 18:38:35 2019

@author: Meghana
"""

from numpy import savetxt as np_savetxt
from sklearn.metrics import average_precision_score as sklearn_metrics_average_precision_score
from matplotlib import use as mpl_use
mpl_use('Agg')     # Issues warning on spyder - don't worry abt it
from tpotClassi import tpot_classi
from logging import info as logging_info
from testClassi import calc_metrics
from testClassi import analyze_sizewise_accuracies

def train_classi(model_name,inputs,X_pos,y_pos,X,y,X_neg,y_neg):
    scaler = None
    model_type = inputs['model_type']
    out_comp_nm = inputs['dir_nm'] + inputs['out_comp_nm']

    if(model_type == "tpot"):
        logging_info("Training model... %s",str(model_type))

        from sklearn.pipeline import make_pipeline

        if(model_name == "tpot_select"):
            clf = tpot_classi(inputs)
        elif(model_name == "SVM"):
            logging_info("Training model... %s",str(model_name))
            # Imports from tpot output             
            from sklearn.preprocessing import StandardScaler
            #from sklearn.svm import LinearSVC
            from sklearn.svm import SVC

            # Pipeline from tpot 
            #clf = make_pipeline(StandardScaler(), LinearSVC(random_state=0, tol=1e-5))
            # Cross validate with C vals - default is 1
            # LinearSVC does not have a predict_proba function 
            clf = make_pipeline(StandardScaler(), SVC(kernel='linear',probability=True,random_state=0, tol=1e-5))
        elif(model_name == "estimator_SVM"):

            from sklearn.ensemble import GradientBoostingClassifier
            from sklearn.feature_selection import SelectFwe, f_classif
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline, make_union
            #from sklearn.svm import LinearSVC
            from tpot.builtins import StackingEstimator
            from xgboost import XGBClassifier

            # Score on the training set was:0.968003998605
            #clf = make_pipeline(StackingEstimator(estimator=GradientBoostingClassifier(learning_rate=0.1, max_depth=9, max_features=0.05, min_samples_leaf=2, min_samples_split=17, n_estimators=100, subsample=1.0)),SelectFwe(score_func=f_classif, alpha=0.02),StackingEstimator(estimator=LogisticRegression(C=1.0, dual=True, penalty="l2")),StackingEstimator(estimator=XGBClassifier(learning_rate=0.001, max_depth=7, min_child_weight=16, n_estimators=100, nthread=1, subsample=0.65)),LinearSVC(C=1.0, dual=True, loss="squared_hinge", penalty="l2", tol=0.001))

            clf = make_pipeline(StackingEstimator(estimator=GradientBoostingClassifier(learning_rate=0.1, max_depth=9, max_features=0.05, min_samples_leaf=2, min_samples_split=17, n_estimators=100, subsample=1.0)),SelectFwe(score_func=f_classif, alpha=0.02),StackingEstimator(estimator=LogisticRegression(C=1.0, dual=True, penalty="l2")),StackingEstimator(estimator=XGBClassifier(learning_rate=0.001, max_depth=7, min_child_weight=16, n_estimators=100, nthread=1, subsample=0.65)),SVC(kernel='linear',probability=True,C=1.0,tol=0.001))
        elif(model_name == "log_reg"):
            logging_info("Training model... %s",str(model_name))
            # Imports from tpot output             
            from sklearn.ensemble import ExtraTreesClassifier
            from sklearn.linear_model import LogisticRegression
            from tpot.builtins import StackingEstimator, ZeroCount

            # Pipeline from tpot 
            # Score on humap was:0.986160063433
            clf = make_pipeline(ZeroCount(),StackingEstimator(estimator=ExtraTreesClassifier(bootstrap=False, criterion="entropy", max_features=0.6, min_samples_leaf=4, min_samples_split=6, n_estimators=100)),    LogisticRegression(C=15.0, dual=False, penalty="l2"))

        elif(model_name == "extra_trees"):
            from sklearn.ensemble import ExtraTreesClassifier
            from tpot.builtins import StackingEstimator

            from sklearn.pipeline import make_pipeline, make_union
            from sklearn.preprocessing import Normalizer
            from sklearn.preprocessing import FunctionTransformer
            from copy import copy

            # Score on the training set was:0.948305771055
            clf = make_pipeline(make_union(FunctionTransformer(copy),make_pipeline(StackingEstimator(estimator=ExtraTreesClassifier(bootstrap=False, criterion="gini", max_features=0.25, min_samples_leaf=8, min_samples_split=11, n_estimators=100)),Normalizer(norm="l1"))),StackingEstimator(estimator=ExtraTreesClassifier(bootstrap=False, criterion="entropy", max_features=0.75, min_samples_leaf=15, min_samples_split=18, n_estimators=100)),ExtraTreesClassifier(bootstrap=True, criterion="entropy", max_features=0.85, min_samples_leaf=5, min_samples_split=4, n_estimators=100))

        else: # Random forest
            logging_info("Training model... %s",str(model_name))
            # Imports from tpot output             
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.feature_selection import VarianceThreshold
            from sklearn.preprocessing import PolynomialFeatures

            # Pipeline from tpot 
            # Score on humap was:0.986160063433
            clf = make_pipeline(VarianceThreshold(threshold=0.05),PolynomialFeatures(degree=2, include_bias=False, interaction_only=False),RandomForestClassifier(bootstrap=False, criterion="entropy", max_features=0.35, min_samples_leaf=1, min_samples_split=11, n_estimators=100)
)

        clf.fit(X, y)

        logging_info("Finished Training model")
        logging_info("Evaluating training accuracy...")
        #Training accuracy


        acc_overall_train = clf.score(X,y)
        acc_pos_train = clf.score(X_pos,y_pos)
        acc_neg_train = clf.score(X_neg,y_neg)

        res_pos = clf.predict(X_pos)
        res = clf.predict(X_neg)

        n_pos = len(X_pos)
        n_neg = len(X_neg)

        acc, acc_neg, Recall, Precision, F1_score = calc_metrics(res,res_pos,n_neg, n_pos)
        analyze_sizewise_accuracies(X_pos, res_pos, X_neg, res,
                                    out_comp_nm + '_size_wise_accuracies_train.png')
        train_fit_probs = clf.predict_proba(X)[:,1]
        train_aps = sklearn_metrics_average_precision_score(y,train_fit_probs)
        with open(out_comp_nm+'_metrics.out',"a") as fid:
            print("Training set average precision score = %.3f" % train_aps,file = fid)


        model = clf

        if hasattr(model, 'decision_function'):
            score = model.decision_function(X_neg)
            np_savetxt(out_comp_nm+'_train_neg_score.out',score)
            score = model.decision_function(X_pos)
            np_savetxt(out_comp_nm+'_train_pos_score.out',score)

    elif(model_type == "NN"):

        # Standardizing the feature matrix 
        from sklearn import preprocessing
        scaler = preprocessing.StandardScaler().fit(X)

        X = scaler.transform(X)

        # Scaling X_pos and X_neg as well now for testing with them later
        X_pos = scaler.transform(X_pos)
        X_neg = scaler.transform(X_neg)

        import tensorflow as tf
        from tensorflow import keras

        #tf.enable_eager_execution() # Fix ensuing errors


        logging_info("Training model... %s",str(model_type))

        # multi-layer perceptron
        #for most problems, one could probably get decent performance (even without a second optimization step) by setting the hidden layer configuration using just two rules: (i) number of hidden layers equals one; and (ii) the number of neurons in that layer is the mean of the neurons in the input and output layers.
        print()
        dims = X.shape
        n_feats = dims[1]
        n_classes = 2
        logging_info("No. of nodes in input layer = %s", str(n_feats))
        logging_info("No. of nodes in output layer (since softmax) = %s", str(n_classes))
        hidden_nodes = int((n_feats + n_classes)/2)
        logging_info("No. of nodes in the one hidden layer = %s", str(hidden_nodes))
        model = keras.Sequential([keras.layers.Dense(n_feats, activation = tf.nn.relu),keras.layers.Dense(hidden_nodes, activation = tf.nn.relu), keras.layers.Dense(n_classes, activation = tf.nn.softmax)])
        #model = keras.Sequential([keras.layers.Dense(n_feats, activation = tf.nn.relu), keras.layers.Dense(n_classes, activation = tf.nn.softmax)])
        model.compile(optimizer='adam',loss = 'sparse_categorical_crossentropy',metrics=['accuracy'])
        N_epochs = 1000
        model.fit(X, y, epochs = N_epochs,verbose=0)
        with open(out_comp_nm+'_metrics.out',"a") as fid:
            print("No. of epochs = ",N_epochs,file = fid)

        logging_info("Finished Training model")
        logging_info("Evaluating training accuracy...")
        loss_overall, acc_overall_train = model.evaluate(X,y,verbose=0)
        loss_pos, acc_pos_train = model.evaluate(X_pos,y_pos,verbose=0)
        loss_neg, acc_neg_train = model.evaluate(X_neg,y_neg,verbose=0)
    else:
        print("Model type not found")


    logging_info("Finished Evaluating training accuracy.")
    with open(out_comp_nm+'_metrics.out',"a") as fid:
        print("Accuracy overall train = %.3f" % acc_overall_train,file = fid)
        print("Accuracy positive train = %.3f" % acc_pos_train,file = fid)
        print("Accuracy negative train = %.3f" % acc_neg_train,file = fid)
        print("Train Precision = %.3f" % Precision, file=fid)
        print("Train Recall = %.3f" % Recall, file=fid)
        print("Train F1 score = %.3f" % F1_score, file=fid)
    return model, scaler