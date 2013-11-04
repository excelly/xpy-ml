from ex import *
from ex.ml.svmutil import *

import sdss_info as sinfo

def usage():
    print('''
classify the objects using svm

python [--feature=SpectrumS1-Color] [--weighted=1] [--svm_options='-t 0 -c 100 -m 1000'] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=', 'feature=', 'weighted=', 'svm_options='])
    poolsize=opts.get('--poolsize', 1)
    feature_names=opts.get('--feature', 'SpectrumS1-Color')
    weighted = int(opts.get('--weighted', 1))
    svm_options = opts.get('--svm_options', '-t 0 -c 100 -m 1000')

    sb = SIMBAD()
    feature, info = GetFeatures(feature_names)
    sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes = sb.GetSIMBADLabels(5)
    labels = sb.LabelData(info['specObjID'], sb_specObjID, sb_objType)
    lidx=find(labels >= 0)[0]
    n_class=arguniqueInt(labels[lidx]).size

    run_id = sinfo.GetClassifierRunID(feature_names, 'svm_' + ('w' if weighted else 'uw'), 'star')

    # handling weights
    if weighted:
        class_weights = 1.0/sqrt(class_sizes)
        class_weights = class_weights/class_weights.sum()*class_weights.size
        for i in range(n_class):
            svm_options += ' -w{0} {1}'.format(i, class_weights[i])
    log.info('SVM options: {0}'.format(svm_options))

    # cross-validation
    t_cv, p_cv=svm_CV(5,feature[lidx],labels[lidx],svm_options,poolsize)
    acc_cv=(labels[lidx] == t_cv).sum()*1.0/t_cv.size
    log.info('Cross-validation accuracy: {0}'.format(acc_cv))

    # training
    log.info('Training the classifier')
    model = svm_train_ex(labels[lidx], feature[lidx], svm_options)

    # training error
    t_tr, acc_tr, p_tr = svm_predict_ex(labels[lidx], feature[lidx], model, svm_options)
    acc_tr = acc_tr[0]
    log.info('Training accuracy {0}'.format(acc_tr))

    tag = '[{0}][{1}][{2}][{3:0.3}-{4:0.3}]'.format(feature_names, weighted, n_class, acc_tr, acc_cv)
    classifier_file='classifier_svm_{0}.pkl'.format(tag)
    log.info('Saving the classifier to {0}'.format(classifier_file))
    svm_save_model(classifier_file, model)

    # prediction
    log.info('Predicting the whole data set')
    t, acc, p=svm_predict_ex(zeros(len(feature)), feature, model, svm_options)
    # use the cv accuracy instead of training accuracy
    t[lidx] = t_cv
    p[lidx] = p_cv

    pred_file='classified_svm_{0}.pkl'.format(tag)
    log.info('Saving prediction result to {0}'.format(pred_file))
    SavePickle(pred_file, {'specObjID':info['specObjID'], 
                           'predicted':[sb_objType_name[tt] for tt in t], 'prob':p, 
                           'runID':run_id})
