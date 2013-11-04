from ex import *
from ex.pp import *

from ex.ml.logistic import MultiLogistic
from ex.ml.nbayes import NBayes
from ex.ml.active import *
from ex.ml.pca import PCA

from simbad import *
import sdss_info as sinfo

def usage():
    print('''
test actively learning on sdss

python [--feature=SpectrumS1-Color] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

def LabelNextUncertainty(model, features, labels, lidx, measure, true_labels, guess_labels):
    pidx = L2I(NOT(lidx))
    t, p, P = model.Predict(features[pidx])
    uncert = arr([measure(pp) for pp in P])
    midx = argmax(uncert)
    result = pidx[midx]

    true_labels.append(labels[result])
    guess_labels.append(argmax(P[midx]))

    return result

def LabelNextMinERisk(model, features, labels, lidx, measure, exp_type, true_labels, guess_labels, candi_per_round = 10, prob_thresh = 0.1):
    pidx = L2I(NOT(lidx)) # pool
    uidx = pidx.copy()
    pidx = pidx[RI(candi_per_round, pidx.size)]
    lidx = L2I(lidx)

    options = deepcopy(model.options)
    options['init'] = model
    options['epsilon'] = 1e-3
    n_class = len(model.ulabels)

    if exp_type is None:
        P = model.Predict(features[pidx])[2]
    elif exp_type == 'uniform':
        P = ones((len(pidx), n_class))/n_class
    elif exp_type == 'truth':
        P = zeros((len(pidx), n_class))
        for ind in range(len(pidx)): P[ind, labels[pidx[ind]]] = 1

    # drop small possibilities
    for pp in P: pp[pp < pp.max()*prob_thresh] = 0
    P = Normalize(P, 's1', 'row')[0]

    # data used for tentative training
    trL = resize(labels[lidx], len(lidx) + 1)
    trF = resize(features[lidx], (len(lidx) + 1, features.shape[1]))

    erisk = zeros(len(pidx))
    mm = model.__class__()
    for ind in range(len(pidx)):
        log.debug('Trying pool instance {0} with {1}/{2} labels'.format(ind, (P[ind] > 1e-5).sum(), n_class))

        trF[-1] = features[pidx[ind]]
        uidx_e = uidx[uidx != pidx[ind]]
        for jnd in range(n_class):
            if P[ind, jnd] < 1e-5: continue

            trL[-1] = jnd
            mm.Train(trF, trL, options)
            tP = mm.Predict(features[uidx_e])[2]
            erisk[ind] += P[ind, jnd]*measure(tP)
            
    midx = argmin(erisk)
    result = pidx[midx]
    log.debug('Predicted Min risk: {0}'.format(erisk[midx]))

    true_labels.append(labels[result])
    guess_labels.append(argmax(P[midx]))

    return result

def LabelNextRandom(model, features, labels, lidx, true_labels, guess_labels):
    lidx = L2I(NOT(lidx))
    return lidx[RI(1, len(lidx))]


def LabelNextLeastConfident(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextUncertainty(model, features, labels, lidx, lambda p: 1 - p.max(), true_labels, guess_labels)

def Margin(p):
    p = sort(p)
    return p[-1] - p[-2]

def LabelNextLeastMargin(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextUncertainty(model, features, labels, lidx, lambda p: -Margin(p), true_labels, guess_labels)

def LabelNextMaxEntropy(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextUncertainty(model, features, labels, lidx, Entropy, true_labels, guess_labels)

def LabelNextMinEError(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: (1 - tP.max(1)).mean(), None, true_labels, guess_labels)

def LabelNextMinEEntropy(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: arr([Entropy(p) for p in tP]).mean(), None, true_labels, guess_labels)

def LabelNextMinUEError(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: (1 - tP.max(1)).mean(), 'uniform', true_labels, guess_labels)

def LabelNextMinUEEntropy(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: arr([Entropy(p) for p in tP]).mean(), 'uniform', true_labels, guess_labels)

def LabelNextMinTEError(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: (1 - tP.max(1)).mean(), 'truth', true_labels, guess_labels)

def LabelNextMinTEEntropy(model, features, labels, lidx, true_labels, guess_labels):
    return LabelNextMinERisk(model, features, labels, lidx, 
                             lambda tP: arr([Entropy(p) for p in tP]).mean(), 'truth', true_labels, guess_labels)

algs = [LabelNextRandom, LabelNextLeastConfident, LabelNextLeastMargin, LabelNextMaxEntropy, LabelNextMinEError, LabelNextMinEEntropy, LabelNextMinTEError, LabelNextMinTEEntropy, LabelNextMinUEError, LabelNextMinUEEntropy]
alg_names = ['Rand', 'Min Conf', 'Min Margin', 'Max Entropy', 'Min E Error', 'Min E Entropy', 'Min TE Error', 'Min TE Entropy', 'Min UE Error', 'Min UE Entropy']

def TruncateClass(labels, class_sizes, max_size):
    r = zeros(len(labels), dtype = bool)
    for ind in range(len(class_sizes)):
        idx = L2I(labels == ind)
        r[idx[RI(max_size, len(idx))]]= True
    return r

def GetPerformance(model, features = None, labels = None, init_samples = None, n_rounds = None):

    if istuple(model) or islist(model):
        model, features, labels, init_samples, n_rounds = model

    # balance the classes by reducing the majority class
    idx = TruncateClass(labels, class_sizes, max_class_size)
    features = features[idx]
    labels = labels[idx]

    run_id = int32(os.getpid() + time.time())
    n, dim = features.shape
    k = arguniqueInt(labels).size
    n_rounds = min(n_rounds, n - k)

    # randomize
    random.seed(run_id)
    ridx = random.permutation(n)
    features = features[ridx]
    labels = labels[ridx]
    lidx = I2L(SelectInitialSet(labels, init_samples), n)
    
    def iGetPerformance(LabelNext): # the internal runner
        ilidx = lidx.copy()

        nn = n_rounds
        if LabelNext in [LabelNextMinEError, LabelNextMinEEntropy, LabelNextMinUEError, LabelNextMinUEEntropy]: 
            nn = min(nn, 100)

        accs = zeros((nn, 3))
        ent = zeros((nn, 3))
        conf = zeros((nn, 3))
        margin = zeros((nn, 3))
        nexts = zeros(nn, dtype = int32)
        
        true_labels = []
        guess_labels = []
        for ind in range(nn):
            model.Train(features[ilidx], labels[ilidx], {'lam':lam, 'init':model, 'epsilon':1e-5, 'verbose':False})

            # performances
            t, dummy, tp = model.Predict(features)

            tmp = t == labels
            accs[ind] = (tmp.mean(), tmp[ilidx].mean(), tmp[NOT(ilidx)].mean())
            
            tmp = arr([Entropy(it) for it in tp])
            ent[ind]=(tmp.mean(), tmp[ilidx].mean(), tmp[NOT(ilidx)].mean())

            tmp = arr([it.max() for it in tp])
            conf[ind]=(tmp.mean(), tmp[ilidx].mean(), tmp[NOT(ilidx)].mean())

            tmp = arr([Margin(it) for it in tp])
            margin[ind]=(tmp.mean(), tmp[ilidx].mean(), tmp[NOT(ilidx)].mean())
            
            nexts[ind]=LabelNext(model, features, labels, ilidx, true_labels, guess_labels)
            ilidx[nexts[ind]] = True

            log.info('-- Round {5}. Acc = {0:0.3}/{1:0.3}/{2:0.3}, Object {3} <{4}> selected'.format(accs[ind,0], accs[ind,1], accs[ind,2], nexts[ind], class_names[labels[nexts[ind]]], ind))

            if poolsize == 1:
                subplot(gcf(), 221);                cla()
                pca.Visualize(features[ilidx], labels[ilidx])
                xlim(xl); ylim(yl);
                subplot(gcf(), 222);                cla()
                pca.Visualize(features, [Entropy(pp) for pp in tp])
                subplot(gcf(), 223);                cla()
                pca.Visualize(features, labels)
                subplot(gcf(), 224);                cla()
                pca.Visualize(features, t)
                draw()

        true_labels = arr(true_labels)
        guess_labels = arr(guess_labels)

        return (accs.ravel(), ent.ravel(), conf.ravel(), margin.ravel(), nexts, true_labels, guess_labels)

    results = [iGetPerformance(alg) for alg in algs]
    return results

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=', 'feature=', 'weighted=',
                               'max_class_size=', 'n_rounds=', 
                               'n_try=', 'n_init=', 'lam=', 'classifier='])
    poolsize=int(opts.get('--poolsize', 1))
    feature_names=opts.get('--feature', 'SpectrumS1-Color')
    max_class_size=int(opts.get('--max_class_size', 1e4))
    n_rounds=int(opts.get('--n_rounds', 100))
    n_try=int(opts.get('--n_try', 12))
    n_init=int(opts.get('--n_init', 1))
    weighted = bool(opts.get('--weighted', 0))
    lam = float(opts.get('--lam', 1e-1))
    classifier = opts.get('--classifier', 'MultiLogistic')

    # idx = [0, 1, 7]
    # algs = [algs[i] for i in idx]
    # alg_names = [alg_names[i] for i in idx]
    algs = algs[:-2]
    alg_names = alg_names[:-2]

    sb = SIMBAD()
    features, labels, class_names, class_sizes, info = sb.GetLabeledObjects(feature_names, min_class_size = 5)

    if poolsize == 1:
        pca = PCA.Train(features)
        tmp = pca.Project(features)
        xl = GetRange(tmp[:,0])
        yl = GetRange(tmp[:,1])
        fig = figure()

    n_rounds = min(n_rounds, max_class_size - n_init)
    model = eval(classifier + '()')
    tag = '[%g][%d][%d][%d][%d][%s]' % (lam, n_init, n_rounds, max_class_size, n_try, model.__class__.__name__)

    jobs = [(model, features, labels, n_init, n_rounds)]*n_try
    results = ProcJobs(GetPerformance, jobs, poolsize)
    results = unzip(results)

    mats = []
    for ind in range(len(algs)):
        results[ind] = unzip(results[ind])
        r = results[ind]

        r = {'accs':vstack(r[0]), 'ents':vstack(r[1]), 'confs':vstack(r[2]), 'margins':vstack(r[3]), 'nexts':vstack(r[4]), 'tl':vstack(r[5]), 'gl':vstack(r[6]), 'name':alg_names[ind]}
        mats.append(r)

    SaveMat('active_stat_{0}.mat'.format(tag), 
            {'data':arr(mats, dtype=np.object)})
