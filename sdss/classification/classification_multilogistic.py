from ex import *
from ex.ml.logistic import MultiLogistic

from simbad import *
from classification import *
import sdss_info as sinfo

def usage():
    print('''
classify the objects using multinomial logistic regression

python [--feature=SpectrumS1-Color] [--weighted=1] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=', 'feature=', 'weighted='])
    poolsize=opts.get('--poolsize', 1)
    feature_names=opts.get('--feature', 'SpectrumS1-Color')
    weighted = int(opts.get('--weighted', 1))
    lam = float(opts.get('--lam', 0.1))

    feature, info = GetFeatures(feature_names)

    sb = SIMBAD()
    sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes = sb.GetSIMBADLabels(5)
    labels = sb.LabelData(info['specObjID'], sb_specObjID, sb_objType)
    lidx=find(labels >= 0)[0]
    n_class=arguniqueInt(labels[lidx]).size

    # weights of samples. the weight should be the inverse of the class
    # sizes in the population, **not the labeled set but here we have
    # no choice
    weights = Reweight(labels[lidx], 1./sqrt(class_sizes)) if weighted else None

    run_id = sinfo.GetClassifierRunID(feature_names, 'mlr_' + ('w' if weighted else 'uw'), 'star')

    options = {'lam':lam, 'weighted':weighted, 'maxIter':500, 'epsilon':1e-7, 'verbose':50}
    # cross-validation
    model = MultiLogistic()
    t_cv, p_cv = model.CV(10, feature[lidx], labels[lidx], 
                          options, True, poolsize)
    acc_cv = (labels[lidx] == t_cv).sum()*1.0/t_cv.size
    log.info('Cross-validation accuracy: {0}'.format(acc_cv))

    # training
    log.info('Training the classifier')
    model.Train(feature[lidx], labels[lidx], options)
    # training error
    t_tr, p_tr = model.Predict(feature[lidx])[:2]
    acc_tr = (t_tr == labels[lidx]).sum()*1.0/t_tr.size
    log.info('Training accuracy {0}'.format(acc_tr))

    sys.exit(0)

    tag = '[{0}][{1}][{2}][{3:0.3}-{4:0.3}]'.format(feature_names, weighted, n_class, acc_tr, acc_cv)
    classifier_file='classifier_mlr_{0}.pkl'.format(tag)
    log.info('Saving the classifier to {0}'.format(classifier_file))
    SavePickle(classifier_file, model)

    # prediction
    log.info('Predicting the whole data set')
    t, p=model.Predict(feature)[:2]
    # use the cv accuracy instead of training accuracy
    t[lidx] = t_cv
    p[lidx] = p_cv

    pred_file='classified_mlr_{0}.pkl'.format(tag)
    log.info('Saving prediction result to {0}'.format(pred_file))
    SavePickle(pred_file, {'specObjID':info['specObjID'], 
                           'predicted':[sb_objType_name[tt] for tt in t], 'prob':p, 
                           'runID':run_id})
