from node import Node
import sys
import numpy as np
import math
import random

class Tree(object):
    def __init__(self, random_forest = False):
        self.root = None
        self.random_forest = random_forest

    # It receives a binarized training dataset
    def fit(self, predictors, X, y):
        root = self.fit_helper(predictors, X, y)
        self.root = root

    def predict(self, data_point):
        return self.predict_helper(self.root, data_point)

    def predict_helper(self, node, data_point):
        if node.c != -1:
            return node.c, node.confidence
        if data_point[node.op] == 0:
            return self.predict_helper(node.kids[0], data_point)
            
        return self.predict_helper(node.kids[1], data_point)    
    
    def fit_helper(self, remaining_predictors, remaining_X, remaining_y):  
        # If the remaining_training_data all belong to same class, then stop
        if not remaining_predictors or self.all_equal(remaining_y):
            return self.get_leaf(remaining_y)
            
        # Out of all predictors remaining_X_j and values s, we need to find j and s such that entropy is minimized
        # In this case, since the predictors are binary, we don't need to find s since we only have one choice of branching
        j, new_remaining_predictors = self.get_best_predictor(remaining_predictors, remaining_X, remaining_y)
        
        if j == -1:
            return self.get_leaf(remaining_y)
        
        # Now all training examples with remaining_X_j = 0 will belong to the left subtree, and remaining_X_j = 1 to the right subtree
        left_X, right_X, left_y, right_y = self.split_data_based_on_predictor(remaining_X, remaining_y, j)
        
        left_node = self.fit_helper(new_remaining_predictors, left_X, left_y)
        right_node = self.fit_helper(new_remaining_predictors, right_X, right_y)
        
        current_node = Node(kids=[left_node, right_node], op=j)
        return current_node

    def get_leaf(self, y):
        counts = np.bincount(y)
        confidence = sum(y) / len(y)
        return Node(c = np.argmax(counts), confidence = confidence)
        
    """ 
    Return the predictor among predictors which maximizes the information gain (minimizes the entropy) for data X and y
    """
    def get_best_predictor(self, predictors, X, y):
        max_information_gain = 0
        best_predictor = -1
        remaining_predictors = predictors[:]
        sample_of_predictors = random.sample(predictors, int(math.sqrt(len(predictors)))) if self.random_forest else predictors
        
        for predictor in sample_of_predictors:
            # Split data based on predictor
            left_X, right_X, left_y, right_y = self.split_data_based_on_predictor(X, y, predictor)
            
            if len(left_X) == 0 or len(right_X) == 0:
                remaining_predictors.remove(predictor)
                continue
            
            information_gain = self.get_information_gain(y, left_y, right_y)

            if information_gain > max_information_gain:
                max_information_gain = information_gain
                best_predictor = predictor
           
        if best_predictor != -1:
            remaining_predictors.remove(best_predictor)
        
        return best_predictor, remaining_predictors

    def get_information_gain(self, y, left_y, right_y):
        root_entropy = self.get_list_cross_entropy(y)
        left_child_entropy = self.get_list_cross_entropy(left_y)
        right_child_entropy = self.get_list_cross_entropy(right_y)

        proportion_left = float(len(left_y)) / float(len(y))
        proportion_right = float(len(right_y)) / float(len(y))

        return root_entropy - (proportion_left * left_child_entropy + proportion_right * right_child_entropy)
            
    def get_list_cross_entropy(self, ys):
        # An empty list has 0 entropy
        if len(ys) == 0:
            return 0
        
        proportion_of_ones = float(sum(ys)) / len(ys)
        proportion_of_zeros = 1 - proportion_of_ones
        
        if proportion_of_ones == 0 or proportion_of_zeros == 0:
            return 0
        
        entropy = - proportion_of_zeros * np.log2(proportion_of_zeros) - proportion_of_ones * np.log2(proportion_of_ones)

        return entropy


    def split_data_based_on_predictor(self, X, y, j):
        left_filter = (X[:, j] == 0)
        right_filter = np.logical_not(left_filter)

        left_X = X[left_filter, :]
        right_X = X[right_filter, :]
        
        left_y = y[left_filter]
        right_y = y[right_filter]

        return left_X, right_X, left_y, right_y

    # Returns True if all elements in y are 0 or if all elements are 1
    def all_equal(self, y):
        return sum(y) == 0 or sum(y) == len(y)