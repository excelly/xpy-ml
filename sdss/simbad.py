from ex import *
from feature import GetFeatures
import settings

class SIMBAD:
    '''handling all simbad related work
    '''

    def __init__(self, db_file = None):

        if db_file is None:
            db_file = settings.sdss_dir + '/sdss.db3'

        self.db_file = db_file

    def GetSIMBADLabels(self, class_size_thresh = 5):
        '''from the data base get simbad label data

        return (specObjID, dist, objType, objType_name, class_sizes)
        '''

        log.info('Getting SIMBAD labels')

        db = GetDB(self.db_file, 100)
        cur=db.execute('SELECT specObjID, dist, obj_type, spec_type from simbad').fetchall()
        sb_specObjID, sb_dist, sb_objType, sb_specType = unzip(cur)
        sb_specObjID=arr(sb_specObjID, dtype=int64)
        sb_dist=arr(sb_dist)
        sb_objType_name=list(set(sb_objType))

        # find out the size of each class
        sb_objType=arr(EncodeList(sb_objType, sb_objType_name), int32)
        class_sizes=accumarray(sb_objType, 1, len(sb_objType_name))

        if class_size_thresh is None or class_size_thresh == 1:
            return (sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes)
        else:
            return self.DropSmallClasses(sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes, class_size_thresh)

    def DropSmallClasses(self, sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes, class_size_thresh):
        '''drop classes that have small sizes. take the output of
        GetSIMBADLabels() and return the same things
        '''
    
        n = sb_objType.size

        filter=class_sizes >= class_size_thresh
        log.info('{0} types are dropped due to small sizes:\n{1}'.format(NOT(filter).sum(), [sb_objType_name[i] for i in find(NOT(filter))[0]]))
        sb_objType_name=[sb_objType_name[i] for i in find(filter)[0]]
        class_sizes=class_sizes[filter]

        # clean
        idx = set(find(filter)[0])
        idx = arr([sb_objType[i] in idx for i in range(n)])
        sb_objType = EncodeArray(sb_objType[idx], find(filter)[0].astype(sb_objType.dtype))

        return (sb_specObjID[idx], sb_dist[idx], sb_objType, sb_objType_name, class_sizes)

    def LabelData(self, spec_ids, sb_spec_ids, sb_objType):
        '''label a set of objects using the output of GetSimbadLabels()
        '''

        labels=EncodeArray(spec_ids, sb_spec_ids);
        lidx=find(labels >= 0)[0]
        labels[lidx]=sb_objType[labels[lidx]]
        return labels

    def GetLabeledObjects(self, feature_names, data_file = 'data_labeled_simbad_{0}.pkl', min_class_size = 5):
        '''return only the objects that are labeled by simbad
        '''

        data_file = data_file.format(feature_names)
        if os.path.exists(data_file):
            log.info('Loading data from {0}'.format(data_file))
            data=LoadPickles(data_file)
        else:
            # get features
            feature, info = GetFeatures(feature_names)

            # get the simbad labels
            sb_specObjID, sb_dist, sb_objType, sb_objType_name, class_sizes = self.GetSIMBADLabels(min_class_size)
    
            # labeling
            labels = self.LabelData(info['specObjID'], sb_specObjID, sb_objType)
            lidx=find(labels >= 0)[0]
            info['labeled'] = lidx

            data = {'features':feature[lidx], 'labels':labels[lidx],
                    'class_names':sb_objType_name, 'class_sizes':class_sizes,
                    'info':info}
            SavePickle(data_file, data)

        return (data['features'], data['labels'], data['class_names'], data['class_sizes'], data['info'])
