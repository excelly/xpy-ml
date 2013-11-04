from ex import *
from ex.pp import *

from ex.ml.logistic import MultiLogistic
from ex.ml.nbayes import NBayes
from ex.ml.active import *
from ex.ml.pca import PCA

import sdss_info as sinfo
from classification_active import algs, alg_names, TruncateClass, Margin

def usage():
    print('''
test actively learning on toy data

python [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

def GetPerformance(model, features = None, labels = None, init_samples = None, n_rounds = None):

    if istuple(model) or islist(model):
        model, features, labels, init_samples, n_rounds = model

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

            if poolsize == 2:
                subplot(gcf(), 221);                cla()
#                pca.Visualize(features[ilidx], labels[ilidx])
                scatter(features[ilidx,0], features[ilidx,1], c = labels[ilidx])
                xlim(xl); ylim(yl);
                subplot(gcf(), 222);                cla()
#                pca.Visualize(features, [Entropy(pp) for pp in tp])
                scatter(features[:,0], features[:,1], c = [Entropy(pp) for pp in tp], vmin = 0, vmax = loge(tp.shape[1]))
                xlim(xl); ylim(yl);
                subplot(gcf(), 223);                cla()
#                pca.Visualize(features, labels)
                model.Plot(GetRange(features[:,0]), GetRange(features[:,1]), 'label')
#                xlim(xl); ylim(yl);
                subplot(gcf(), 224);                cla()
#                pca.Visualize(features, t)
                model.Plot(GetRange(features[:,0]), GetRange(features[:,1]), 'prob')
#                xlim(xl); ylim(yl);
                draw()

        true_labels = arr(true_labels)
        guess_labels = arr(guess_labels)

        return (accs.ravel(), ent.ravel(), conf.ravel(), margin.ravel(), nexts, true_labels, guess_labels)

    results = [iGetPerformance(alg) for alg in algs]
    return results

def Simulation():
    from ex.ml.gmm import GMM
    offset = 100
    gmm = GMM(arr([1, 1, 1, 1]), arr([[0., -1.], [0, 1], [1, 0], [2, 0]]) + offset, eye(2)*3e-2)
    features, labels = gmm.GenerateSample(1000)
    class_names = ['1', '2', '3', '4']
    class_sizes = [(labels == i).sum() for i in range(4)]

    return (features, labels, class_names, class_sizes, None)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=', 'weighted=','n_rounds=', 'n_try=', 'n_init=', 'lam=', 'classifier='])
    poolsize=int(opts.get('--poolsize', 1))
    n_rounds=int(opts.get('--n_rounds', 10))
    n_try=int(opts.get('--n_try', 1))
    n_init=int(opts.get('--n_init', 1))
    weighted = bool(opts.get('--weighted', 0))
    lam = float(opts.get('--lam', 1e-3))
    classifier = opts.get('--classifier', 'MultiLogistic')

    model = eval(classifier + '()')
    tag = '[%g][%d][%d][%d][%s]' % (lam, n_init, n_rounds, n_try, model.__class__.__name__)

    features, labels, class_names, class_sizes, info = Simulation()

    idx = [0, 1, 7]
    algs = [algs[i] for i in idx]
    alg_names = [alg_names[i] for i in idx]

    if poolsize == 1:        
        fig = figure()
        xl = GetRange(features[:,0])
        yl = GetRange(features[:,1])
    
    jobs = [(model, features, labels, n_init, n_rounds)]*n_try
    results = ProcJobs(GetPerformance, jobs, poolsize)
    results = unzip(results)

    mats = []
    for ind in range(len(algs)):
        results[ind] = unzip(results[ind])
        r = results[ind]

        r = {'accs':vstack(r[0]), 'ents':vstack(r[1]), 'confs':vstack(r[2]), 'margins':vstack(r[3]), 'nexts':vstack(r[4]), 'tl':vstack(r[5]), 'gl':vstack(r[6]), 'name':alg_names[ind]}
        mats.append(r)

    SaveMat('active_sim_stat.mat', 
            {'data':arr(mats, dtype=np.object)})

    show()
