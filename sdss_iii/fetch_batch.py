#! /auton/home/lxiong/local/bin/python

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
print 'Pyplot backend:', plt.get_backend()

import smtplib
from email.mime.text import MIMEText
def SendNotice(title, msg):
    sender = 'auton.sdss@gmail.edu'
    receiver = 'excelly@gmail.com'

    msg = MIMEText(msg)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = receiver

    s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    s.login('auton.sdss', 'sdss@auton')
    try:
        s.sendmail(sender, receiver, msg.as_string())
    except ex:
        print ex
    finally:
        s.quit()

from ex import *
from ex.ioo import *
from ex.pp import *
import sdss.utils as utils

InitLog()
email_msg = ''

###### setup
stamp = utils.GetStamp()

code_dir = '/auton/home/lxiong/h/python/sdss_iii'
working_dir = code_dir + '/working'
data_dir = working_dir + '/data'
proc_dir = '/auton/home/lxiong/data/sdss/III_1'
run = 'v5_6_0'

spall_fits = '%s/spAll-%s.fits' % (data_dir, run)
restframe_fits = '%s/spectra_restframe_%s.fits' % (working_dir, stamp)

try:
    os.chdir(code_dir)
###### download data
    import sdss_iii.fetch_download as fetch_download
    fetch_download.main(working_dir, run, stamp)

###### initial consolidation
    import sdss_iii.fetch_make_fits as fetch_make_fits
    fetch_make_fits.main(working_dir, stamp, run, 4)
    if not os.path.exists(restframe_fits):
        raise RuntimeError('Cannot find FITS data: %s.' % restframe_fits)

###### draw figures
    import sdss_iii.fetch_make_figures as fetch_make_figures
    fetch_make_figures.main(working_dir, stamp, run, 4)
    cmd = 'rsync -a --include="*" %s/figures/ sdss:/home/lxiong/www/images/iii_spec' % working_dir
    log.info(cmd)
    if os.system(cmd) != 0: log.warning('Failed to sync the images')

    os.chdir(proc_dir)
###### data processing
    import sdss_iii.proc_transform_data as proc_transform_data
    proc_transform_data.main('%s/spectra_restframe_*.fits' % working_dir, 
                             500, 4)

###### extract features
    log.info('Removing old feature files')
    os.system('rm feature_*.pkl feature_*.mat -rf')
    import sdss_iii.feature as feature
    feature.main()

###### apply detectors
    import sdss_iii.detect as detect
    log.info('Removing old detection results')
    os.system('rm %s -rf' % detect.output_dir)
    MakeDir(detect.output_dir)
    jobs = [('Spectrum', 'pca'), ('SpectrumS1', 'pca'), 
            ('Spectrum', 'robust'), ('SpectrumS1', 'robust'),
            ('Spectrum', 'knn'), ('SpectrumS1', 'knn')]
    tmp = []
    for fn, det in jobs: tmp.extend([(fn, cln, det) for cln in (1,2,3)])
    jobs = tmp
    ProcJobs(detect.DoDetection, jobs, 6, chunk_size = 1)

###### export to website
    os.chdir('%s/web_report' % code_dir)

    import sdss_iii.web_report.web_import_scores as score_importer
    score_importer.main('%s/detection_results/scores_*.pkl' % proc_dir, 0.2)

    import sdss_iii.web_report.web_import_similarity as sim_importer
    sim_importer.main('%s/similarity_*.pkl' % proc_dir)
finally:
###### send notice
    with open('/auton/home/lxiong/h/python/sdss_iii/cronjob.log') as input:
        email_msg += input.read()
    SendNotice('SDSS III batch job %s' % stamp, email_msg)
