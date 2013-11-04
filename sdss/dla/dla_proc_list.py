from ex import *
import utils

InitLog()

db = GetDB('/auton/home/lxiong/data/sdss/dr7/sdss.db3')

qso = []
total = 0
with xFile('qso.lst') as i:
    for line in i:
        sp = line.split(' ')
        sp = [s for s in sp if len(s) > 0]
        plate, mjd, fiber, name, z1 = sp[:5]
        sid, ra, dec, z2 = utils.LookupMPF(db, mjd, plate, fiber)
        if sid is None:
            log.warn('{0}-{1}-{2} {3} X'.format(mjd,plate,fiber,name))
        else:
            qso.append((sid, ra, dec, z2, name, z1, mjd, plate, fiber))
            total += 1
log.info('{0}/{1} qso found'.format(len(qso), total))

qso = ['%d, %0.4f, %0.4f, %0.5f, %s, %s, %s, %s, %s' % r for r in qso]
with xFile('qso_id.csv', 'w') as o:
    o.writelines("\n".join(qso))

dla = []
total = 0
with xFile('dla.lst') as i:
    for line in i:
        name, z1 = line.split(' ')[:2]
        ra1, dec1 = utils.NameToRD(name)
        z1 = float(z1)
                    
        match = utils.LookupRDZ(db, (ra1, dec1), 1e-2)
        if match is None:
            log.warn('%s (%0.4f, %0.4f) not found'%(name, ra1, dec1))
        else:
            sid, ra2, dec2, z2, err = match
            dla.append((sid, ra2, dec2, z2, err, name, ra1, dec1, z1))
            total += 1
            log.info('%s found with error %0.5f'%(name, err))
log.info('{0}/{1} dla found'.format(len(dla), total))

dla = ['%d, %0.4f, %0.4f, %0.4f, %0.5f, %s, %0.4f, %0.4f, %0.5f' % r for r in dla]
with xFile('dla_id.csv','w') as o:
    o.writelines("\n".join(dla))

db.close()
