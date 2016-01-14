from parser import Move, Turn, Game, Parser
import time,sys
from sklearn import neighbors, datasets, linear_model
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.naive_bayes import BernoulliNB

import matplotlib.pyplot as plt


def knn(training_features,training_labels,validation_features):
	n_neighbors = 40
	weights = 'uniform'
	knn = neighbors.KNeighborsRegressor(n_neighbors, weights=weights)
	y_ = knn.fit(training_features,training_labels).predict(validation_features)
	return y_

def lr(training_features, training_labels, validation_features):
	regr = linear_model.LinearRegression()
	y_ = regr.fit(training_features,training_labels).predict(validation_features)
	return y_

def tree(training_features,training_labels,validation_features):
	clf_1 = DecisionTreeRegressor(max_depth = 6)
	y_ = clf_1.fit(training_features,training_labels).predict(validation_features)
	return y_

def forest(training_features,training_labels,validation_features):
	clf = RandomForestRegressor(n_estimators =79)
	y_ = clf.fit(training_features,training_labels).predict(validation_features)
	return y_

def knnO(training_features,training_labels,validation_features,n_neighbors):
	weights = 'uniform'
	knn = neighbors.KNeighborsRegressor(n_neighbors, weights=weights)
	y_ = knn.fit(training_features,training_labels).predict(validation_features)
	return y_

def treeO(training_features,training_labels,validation_features,mx):
	clf_1 = DecisionTreeRegressor(max_depth = mx)
	y_ = clf_1.fit(training_features,training_labels).predict(validation_features)
	return y_

def forestO(training_features,training_labels,validation_features,mx):
	clf = RandomForestRegressor(n_estimators =mx)
	y_ = clf.fit(training_features,training_labels).predict(validation_features)
	return y_

def ensemble1(training_features,training_labels,validation_features):
	knn = neighbors.KNeighborsRegressor(40,weights='uniform')
	lr = linear_model.LinearRegression()
	tree = DecisionTreeRegressor(max_depth = 6)
	y_knn = knn.fit(training_features,training_labels).predict(validation_features)
	y_tree = tree.fit(training_features,training_labels).predict(validation_features)
	y_lr = lr.fit(training_features,training_labels).predict(validation_features)

	y_ = []
	for i in range(len(y_knn)):
		y_.append((y_knn[i]+y_tree[i]+y_lr[i])/3)
	#lr knn and tree
	return y_
	
def ensemble2(training_features,training_labels,validation_features):
	#lr knn forest
	knn = neighbors.KNeighborsRegressor(40,weights='uniform')
	lr = linear_model.LinearRegression()
	forest = RandomForestRegressor(n_estimators = 79)
	y_knn = knn.fit(training_features,training_labels).predict(validation_features)
	y_forest = forest.fit(training_features,training_labels).predict(validation_features)
	y_lr = lr.fit(training_features,training_labels).predict(validation_features)

	y_ = []
	for i in range(len(y_knn)):
		y_.append((y_knn[i]+y_forest[i]+y_lr[i])/3)
	return y_
	


def ensemble3(training_features,training_labels,validation_features):
	#lr forest
	#lr knn forest
	lr = linear_model.LinearRegression()
	forest = RandomForestRegressor(n_estimators = 79)
	y_forest = forest.fit(training_features,training_labels).predict(validation_features)
	y_lr = lr.fit(training_features,training_labels).predict(validation_features)

	y_ = []
	for i in range(len(y_forest)):
		y_.append((y_forest[i]+y_lr[i])/2)
	return y_

def ensemble4(training_features,training_labels,validation_features):
	#lr forest
	#lr knn forest tree
	tree = DecisionTreeRegressor(max_depth = 6)
	knn = neighbors.KNeighborsRegressor(40,weights='uniform')
	lr = linear_model.LinearRegression()
	forest = RandomForestRegressor(n_estimators = 79)
	y_forest = forest.fit(training_features,training_labels).predict(validation_features)
	y_lr = lr.fit(training_features,training_labels).predict(validation_features)
	y_knn = knn.fit(training_features,training_labels).predict(validation_features)
	y_tree = tree.fit(training_features,training_labels).predict(validation_features)
	y_ = []
	for i in range(len(y_forest)):
		y_.append((y_tree[i]+y_knn[i]+y_forest[i]+y_lr[i])/4)
	return y_

def ensemble5(training_features,training_labels,validation_features):
	#tree,knn,frest
	tree = DecisionTreeRegressor(max_depth = 6)
	knn = neighbors.KNeighborsRegressor(40,weights='uniform')
	forest = RandomForestRegressor(n_estimators = 79)
	y_forest = forest.fit(training_features,training_labels).predict(validation_features)
	y_knn = knn.fit(training_features,training_labels).predict(validation_features)
	y_tree = tree.fit(training_features,training_labels).predict(validation_features)
	y_ = []
	for i in range(len(y_forest)):
		y_.append((y_tree[i]+y_knn[i]+y_forest[i])/3)
	return y_

def svm(training_features,training_labels,validation_features):
	clf = SVR()
	y_ = clf.fit(training_features,training_labels).predict(validation_features)
	return y_

def nb(training_features,training_labels,validation_features):
	gnb = BernoulliNB()
	y_ = gnb.fit(training_features,training_labels).predict(validation_features)
	return y_

def perceptron(training_features,training_labels,validation_features):
	p = linear_model.Perceptron()
	y_ = p.fit(training_features,training_labels).predict(validation_features)
	return y_


