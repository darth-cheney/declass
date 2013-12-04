"""
Grid Search this is thus far for dark censors
"""
import redactometer
import pandas
import itertools
import time
import numpy as np

def gridsearch(param_grid, train, img_root, metric, censor_type="dark"):
    """Lorem Ipsum"""
    #no cross-val simple param setting
    train = train[train.redaction_type == censor_type]

    combos = [{key: value for (key, value) in zip(param_grid, values)} 
             for values in itertools.product(*param_grid.values())]

    #I believe this is not the efficient way. (Dataframes should not be iterated)

    max_score = 0
    argmax = []  
    print "number combos", len(combos)

    for combo in combos:
        #boolean
        if metric == 'is_censored':
            score = boolean_scoring(train, img_root, combo)

        #are we able to get the right number of blobs?
        if metric == 'total_censor':
            score = count_scoring(train, img_root, combo)

        #update
        if score >= max_score:
            max_score = score
            argmax.append(combo) 
    return argmax, max_score     

def complete_search(training, img_dir, metric, min_start, min_stop, max_start, max_stop, step):
    #range is inclusive
    min_range = np.arange(min_start, min_stop, step)
    max_range = np.arange(max_start, max_stop, step)
    param_grid = {'min_width_ratio' : min_range,
                'max_width_ratio': max_range,
                'min_height_ratio': min_range,
                'max_height_ratio': max_range}
    return gridsearch(param_grid, training, img_dir, metric)

def eval(test, params, img_root, metric, censor_type="dark"):
    """Evaluation results on test set"""

    if metric == "is_censored":
        return boolean_scoring(test, img_root, params)

    if metric == "total_censor":
        return count_scoring(test, img_root, params)

def boolean_scoring(data, url, params):
    """does not filter by censor type yet"""
    correct = sum((len(redactometer.censor_dark(url + i, **params)[1]) > 0) \
       == data.ix[i]['is_censored'] for i in data.index)
    score = float(correct)/float(len(data.index))
    return score

def count_scoring(data, url, params):
    """does not filter by censor type yet"""
    correct = sum(len(redactometer.censor_dark(url + i, **params)[1]) \
                == data.ix[i]['total_censor'] for i in data.index)
    imgs = [(i, len(redactometer.censor_dark(url + i, **params)[1]), data.ix[i]['total_censor']) for i in data.index if len(redactometer.censor_dark(url + i, **params)[1]) \
                == data.ix[i]['total_censor']]
    
    score = float(correct)/float(len(data.index))
    #if correct > 10:
    #    print params, correct, score
    
    return score, correct, imgs

