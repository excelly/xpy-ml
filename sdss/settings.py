sdss_dir = '/auton/data/sdss/dr7/'
data_dir = ''

# code for features
feature_code={
    'spectrum': 1,
    'continuum': 2,
    'spectrums1': 3,
    'continuums1': 4,
    'lines': 5,
    'spectrum-color': 6,
    'continuum-color': 7,
    'spectrums1-color': 8,
    'continuums1-color': 9,
    }

similarity_code = {
    'l2': 1
    }

# code for scorers
scorer_code={
    'pca_rec_err': 1,
    'pca_accum_err': 2,
    'pca_dist': 3,
    'pca_dist_out': 4,
    'pca_accum_dist_out': 5,
    'drmf_rec_err': 6,
    'drmf_accum_err': 7,
    'drmf_dist': 8,
    'drmf_dist_out': 9,
    'drmf_accum_dist_out': 10,
    'rpca_aprx': 11,
    'drmf_aprx': 12,
    'knn_mean_dist':13,
    'knn_max_dist':14
    }

# code for classifiers
classifier_code={
    'mlr_uw': 1,
    'mlr_w': 2,
    'svm_uw': 3,
    'svm_w': 4
    }

# code for data sources
spec_cln_code={
    'star': 1,
    'galaxy': 2,
    'quasar': 3
    }
spec_cln_code_inv={
    1: 'star',
    2: 'galaxy',
    3: 'quasar'
    }

# get the ID of a run
def GetDetectionRunID(feature, scorer, spec_cln):
    f=feature_code[feature.strip().lower()]
    s=scorer_code[scorer.strip().lower()]
    c=spec_cln_code[spec_cln.strip().lower()]

    return int(f*1e6 + s*1e3 + c)

def GetClassificationRunID(feature, classifier, spec_cln):
    f=feature_code[feature.strip().lower()]
    s=classifier_code[classifier.strip().lower()]
    c=spec_cln_code[spec_cln.strip().lower()]

    return int(f*1e6 + s*1e3 + c)

sp_masks={
    'SP_MASK_OK'           :0x000,      
    'SP_MASK_NOPLUG'       :0x001,    #  Fiber not listed in plugmap file
    'SP_MASK_BADTRACE'     :0x002,    #  Bad trace from routine TRACE320CRUDE    
    'SP_MASK_BADFLAT'      :0x004,    #  Low counts in fiberflat 
    'SP_MASK_BADARC'       :0x008,    #  Bad arc solution
    'SP_MASK_MANYBADCOL'   :0x010,    #  More than 10% pixels are bad columns    
    'SP_MASK_MANYREJECT'   :0x020,    #  More than 10% pixels are rejected in extraction 
    'SP_MASK_LARGESHIFT'   :0x040,    #  Large spatial shift between flat and object position
    'SP_MASK_NEARBADPIX'   :0x10000,  #  Bad pixel within 3 pixels of trace      
    'SP_MASK_LOWFLAT'      :0x20000,  #  Flat field less than 0.5
    'SP_MASK_FULLREJECT'   :0x40000,  #  Pixel fully rejected in extraction      
    'SP_MASK_PARTIALREJ'   :0x80000,  #  Some pixels rejected in extraction      
    'SP_MASK_SCATLIGHT'    :0x100000, #  Scattered light significant     
    'SP_MASK_CROSSTALK'    :0x200000, #  Cross-talk significant  
    'SP_MASK_NOSKY'        :0x400000, #  Sky level unknown at this wavelength    
    'SP_MASK_BRIGHTSKY'    :0x800000, #  Sky level > flux + 10*(flux error)      
    'SP_MASK_NODATA'       :0x1000000,#  No data available in combine B-spline   
    'SP_MASK_COMBINEREJ'   :0x2000000,#  Rejected in combine B-spline    
    'SP_MASK_BADFLUXFACTOR':0x4000000,#  Low flux-calibration or flux-correction factor  
    'SP_MASK_BADSKYCHI'    :0x8000000,#  Chi^2 > 4 in sky residuals at this wavelength   
    'SP_MASK_REDMONSTER'   :0x10000000,#  Contiguous region of bad chi^2 in sky residuals 
    'SP_MASK_EMLINE'       :0x40000000 #  Emission line detected here 
    }

bad_mask_names=[
    'SP_MASK_BADTRACE',     #  Bad trace from routine TRACE320CRUDE  
    'SP_MASK_BADFLAT',      #  Low counts in fiberflat
    'SP_MASK_BADARC',       #  Bad arc solution  
    'SP_MASK_NEARBADPIX',   #  Bad pixel within 3 pixels of trace    
    'SP_MASK_LOWFLAT',      #  Flat field less than 0.5    
    'SP_MASK_FULLREJECT',   #  Pixel fully rejected in extraction    
    'SP_MASK_SCATLIGHT',    #  Scattered light significant 
    'SP_MASK_CROSSTALK',    #  Cross-talk significant    
    'SP_MASK_BRIGHTSKY',    #  Sky level > flux + 10*(flux error)    
    'SP_MASK_NODATA',       #  No data available in combine B-spline 
    'SP_MASK_COMBINEREJ',   #  Rejected in combine B-spline
    'SP_MASK_BADSKYCHI',    #  Chi^2 > 4 in sky residuals at this wavelength   
    'SP_MASK_REDMONSTER'   #  Contiguous region of bad chi^2 in sky residuals 
    ]

bad_mask=0
for name in bad_mask_names:
    bad_mask |= sp_masks[name]

z_statuses={
    'NOT_MEASURED' : 0, # Not yet measured   
    'FAILED'       : 1, # Redshift measurement failed  
    'INCONSISTENT' : 2, # Xcorr & emz redshifts both high-confidence but inconsistent
    'XCORR_EMLINE' : 3, # Xcorr plus consistent emz redshift measurement   
    'XCORR_HIC'    : 4, # z determined from x-corr with high confidence    
    'XCORR_LOC'    : 5, # z determined from x-corr with low confidence
    'EMLINE_XCORR' : 6, # Emz plus consistent xcorr redshift measurement   
    'EMLINE_HIC'   : 7, # z determined from em-lines with high confidence  
    'EMLINE_LOC'   : 8, # z determined from em-lines with low confidence   
    'MANUAL_HIC'   : 9, # z determined "by hand" with high confidence 
    'MANUAL_LOC'   : 10, # z determined "by hand" with low confidence  
    'XCORR_4000BREAK': 11, # Xcorr redshift determined when EW(4000break) > 0.95
    'ABLINE_CAII'  : 12 # Redshift determined from average of CaII triplet fits
    }

bad_z_status_names=[
    'NOT_MEASURED', # Not yet measured   
    'FAILED',       # Redshift measurement failed  
    'INCONSISTENT' # Xcorr & emz redshifts both high-confidence but inconsistent
    ]
bad_z_status=[z_statuses[ss] for ss in bad_z_status_names]

z_warnings={
    'Z_WARNING_OK'           :0x000,  # no warnings   
    'Z_WARNING_NO_SPEC'      :0x001,  # no spec  
    'Z_WARNING_NO_BLUE'      :0x002,  # no blueside   
    'Z_WARNING_NO_RED'       :0x004,  # no redside    
    'Z_WARNING_NOT_GAL'      :0x010,  # classification does not match galaxy target 
    'Z_WARNING_NOT_QSO'      :0x020,  # classification does not match qso target    
    'Z_WARNING_NOT_STAR'     :0x040,  # classification does not match star target   
    'Z_WARNING_GAL_COEF'     :0x080,  # strange galaxy coefficients  
    'Z_WARNING_EMAB_INC'     :0x100,  # emission and absorbtion redshifts inconsistent  
    'Z_WARNING_AB_INC'       :0x200,  # absorbtion redshifts inconsistent ,multiple peaks
    'Z_WARNING_EM_INC'       :0x400,  # emission redshifts inconsistent  
    'Z_WARNING_HIZ'          :0x800,  # redshift is   high 
    'Z_WARNING_LOC'          :0x1000,  # confidence is low  
    'Z_WARNING_LOW_SNG'      :0x2000,  # signal to noise is low in g' 
    'Z_WARNING_LOW_SNR'      :0x4000,  # signal to noise is low in r' 
    'Z_WARNING_LOW_SNI'      :0x8000,  # signal to noise is low in i' 
    'Z_WARNING_4000breakd'   :0x10000,  # EW(4000break) > 0.95    
    'Z_WARNING_CL_MAN'       :0x20000,  # classification set manually 
    'Z_WARNING_Z_MAN'        :0x40000  # redshift set manually 
    }

bad_z_warning_names=[
    'Z_WARNING_NO_SPEC',      # no spec  
    'Z_WARNING_NOT_GAL',      # classification does not match galaxy target 
    'Z_WARNING_NOT_QSO',      # classification does not match qso target    
    'Z_WARNING_NOT_STAR',     # classification does not match star target   
    'Z_WARNING_GAL_COEF',     # strange galaxy coefficients  
    'Z_WARNING_EMAB_INC',     # emission and absorbtion redshifts inconsistent  
    'Z_WARNING_AB_INC',       # absorbtion redshifts inconsistent ,multiple peaks
    'Z_WARNING_EM_INC',       # emission redshifts inconsistent  
    'Z_WARNING_LOW_SNG',      # signal to noise is low in g' 
    'Z_WARNING_LOW_SNR',      # signal to noise is low in r' 
    'Z_WARNING_LOW_SNI'      # signal to noise is low in i' 
    ]

bad_z_warning=0
for name in bad_z_warning_names:
    bad_z_warning |= z_warnings[name]

classes={
    'SPEC_UNKNOW' :0,
    'SPEC_STAR'   :1,
    'SPEC_GALAXY' :2,
    'SPEC_QSO'    :3,
    'SPEC_HIZ_QSO':4, # high redshift QSO, z>2.3, Ly-alpha finding code is triggered
    'SPEC_SKY'    :5, 
    'STAR_LATE'   :6, # star dominated by molecular bands, Type M or later  
    'GAL_EM'      :7  # emission line galaxy -- not set by the code         
    }

emission_lines={
    1033.82:	    'OVI',
    1215.67:	    'Ly.a',
    1240.81:	    'NV',
    1305.53:	    'OI',
    1335.31:	    'CII',
    1399.8:	    'SiIV+OIV',
    1549.48:	    'CIV',
    1640.4:	    'HeII',
    1665.85:	    'OIII',
    1857.4:	    'AlIII',
    1908.734:	    'CIII',
    2326:	    'CII',
    2439.5:	    'NeIV',
    2799.117:	    'MgII',
    3346.79:	    'NeV',
    3426.85:	    'NeV',
    3727.092:	    'OII',
    3729.875:	    'OII',
    3798.976:	    'H.h',
    3836.47:	    'H.y',
    3889:	    'HeI',
    3934.777:	    'K',
    3969.588:	    'H',
    4072.3:	    'SII',
    4102.89:	    'H.d',
    4305.61:	    'G',
    4341.68:	    'H.g',
    4364.436:	    'OIII',
    4862.68:	    'H.b',
    4960.295:	    'OIII',
    5008.24:	    'OIII',
    5176.7:	    'Mg',
    5895.6:	    'Na',
    6302.046:	    'OI',
    6365.536:	    'OI',
    6549.86:	    'NII',
    6564.61:	    'H.a',
    6585.27:	    'NII',
    6709.6:	    'Li',# different than the original spec
    6718.29:	    'SII',
    6732.67:	    'SII',
    8500.36:	    'CaII',
    8544.44:	    'CaII',
    8664.52:	    'CaII'
    }

line_features=['6709.6', '6564.6', '6585.3', '6549.9', '4341.7', '5895.6', '3969.6', '6365.5', '6732.7', '5176.7', '6718.3', '3836.5', '4305.6', '8664.5', '4364.4', '8544.4', '3934.8', '8500.4', '4960.3', '6302.0', '3889.0', '4072.3', '5008.2', '4102.9', '4862.7']
