from ex import *

def SelectInitialSet(labels, n_per_class):
    '''select the first instances from each class as the intial labeled set
    '''

    k = arguniqueInt(labels).size
    result = []
    counts = zeros(k, int32)
    for ind in range(len(labels)):
        cls = labels[ind]
        if counts[cls] < n_per_class:
            result.append(ind)
            counts[cls] += 1
            if len(result) >= n_per_class * k:
                break
    return result
