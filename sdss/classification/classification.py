from ex import *

def Reweight(labels, class_weights = None):
    '''reweight the samples for unbalanced data
    '''

    if class_weights is None:
        n_class = uniqueInt(labels).size
        class_sizes = accumarray(labels, 1, n_class)
        class_weights = 1/class_sizes

    weights = class_weights[labels]
    weights = weights/weights.sum()*len(weights)
    return weights
    
