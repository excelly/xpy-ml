from ex import *

def GetDetailPage(spec_id):
#    return "http://sdss.lib.uchicago.edu/dr7/en/tools/explore/obj.asp?sid={0}".format(spec_id)
    return "http://cas.sdss.org/astro/en/tools/explore/obj.asp?sid={0}".format(spec_id)

def GetSpectrumImage(spec_id):
#    return "http://sdss.lib.uchicago.edu/dr7/en/get/specById.asp?id={0}".format(spec_id)
    return "http://cas.sdss.org/astro/en/get/specById.asp?id={0}".format(spec_id)

def GenObjFigure(rd, spec_id, size):
    detail_page=GetDetailPage(spec_id)
    image_url=GetSkyImage(rd, size=size)
    spectrum_url=GetSpectrumImage(spec_id)

    html='''
<a href="{0}" target="_blank"><img src="{1}" border="0" width="{3}"></a>
<br>
<a href="{2}" target="_blank"><img src="{2}" border="0" width="{3}"></a>
'''.format(detail_page, image_url, spectrum_url, size)

    return html

def GetClusterImage(rd, size=400):
    '''get the image of a cluster. rd is the [ra, dec] of objects in
    this cluster
    '''

    center=rd.mean(0)
    theta=(rd.max(0) - rd.min(0)).max()

    return GetSkyImage(center, 0, theta*0.55, size)

def GenHtmlCluster(spec_ids, rdz, score, cluster_info, object_info):
    n=len(spec_ids)
        
    # cluster 
    cluster_image=GetClusterImage(rdz[:,:2], 400)
    html='''<table border="0"><tr>
<td valign="top">
<img src="{0}" border="0"><br>
<small>Size={1}, Score={2}<br>{3}<small>
</td>
<td valign="top">'''.format(cluster_image, n, score, cluster_info)

    # members
    members=[GenObjFigure(rdz[i], spec_ids[i], 100) for i in range(n)]
    for i in range(n):
        html+='''<div style="float:left">{0}<br>
<small>[{1:.3},{2:.3},{3:.3}]<br>{4}</small>
</div>'''.format(members[i], rdz[i][0], rdz[i][1], rdz[i][2], object_info[i])
    html+="</td></tr></table>"

    return html

def GenReportCluster(clusters, scores, spec_ids, rdz,
                     cluster_info=None, object_info=None, 
                     ncluster=20):
    '''clusters: list of clusters. each cluster is a list of object
    indeces.
    scores: score of each cluster
    spec_ids: spec_id of objects
    rdz: array of object locations. each row is [ra, dec, z]
    cluster_info: any info to show for clusters
    object_info: any info to show for objects
    ncluster: number of clusters in the report
    '''

    if cluster_info is None: 
        cluster_info=arr(['']*len(clusters))
    else:
        cluster_info=arr(cluster_info)
    if object_info is None: 
        object_info=arr(['']*len(spec_ids))
    else:
        object_info=arr(object_info)

    ncluster=min(ncluster, len(clusters))
    sidx=np.argsort(scores)[::-1]
    
    html_an='<html><body>'
    for i in range(ncluster):
        cluster=clusters[sidx[i]]
        block=GenHtmlCluster(spec_ids[cluster], rdz[cluster], scores[sidx[i]], cluster_info[sidx[i]], object_info[cluster])
        html_an+=block
    html_an+="</body></html>"

    html_all='<html><body>'
    for i in range(0,len(clusters),int(np.round(len(clusters)/ncluster))):
        cluster=clusters[sidx[i]]
        block=GenHtmlCluster(spec_ids[cluster], rdz[cluster], scores[sidx[i]], cluster_info[sidx[i]], object_info[cluster])
        html_all+=block
    html_all+="</body></html>"

    return (html_an, html_all)

def GenReportIndividual(spec_id, scores, rdz, nobj=50):

    ii=np.argsort(scores)[::-1]
    scores=scores[ii]
    spec_id=spec_id[ii]
    rdz=rdz[ii]

    html_an='<html><body>\n'
    for i in range(nobj):
        html_an+='<div style="float:left">{0}<br><small>ID={1}<br>Score={2:.3e}</small></div>'.format(GenObjFigure(rdz[i], spec_id[i], 200), spec_id[i], float(scores[i]))
    html_an+='</body></html>'

    html_all='<html><body>\n'
    for i in range(0, len(scores), int(np.round(len(scores)*1./nobj))):
        html_all+='<div style="float:left">{0}<br><small>ID={1}<br>Score={2:.3e}</small></div>'.format(GenObjFigure(rdz[i], spec_id[i], 200), spec_id[i], float(scores[i]))
    html_all+='</body></html'

    return (html_an, html_all)

def GenObjList(spec_ids, rdz, info, row_size=0):
    '''get a list of objects.
    '''

    n=len(spec_ids)
    check(n == rdz.shape[0], 'wrong rdz')
            
    parts=[]
    for i in range(n):
        parts.append('<div style="float:left">{0}<br><small>ID={1}<br>{2}</small></div>'.format(GenObjFigure(rdz[i], spec_ids[i], 150), spec_ids[i], info[i]))

    if row_size > 0:
        pp=Partition(parts, row_size)
        html=''
        for i in range(len(pp)):
            html+='<table width="100%" border="0"><tr><td>'
            html+='\n'.join(pp[i])
            html+='</td></tr></table>'
    else:
        html='<table width="100%" border="0"><tr><td>'
        html+='\n'.join(html)
        html+='</td></tr></table>'

    return html
