<?php

require_once('../base.php');

function GetMainDB()
{
  return new SQLite3('/home/lxiong/www/db/iii_web.db3');
}

function GetSimDB()
{
  return new SQLite3('/home/lxiong/www/db/iii_sim.db3');
}

function Stamp_ToDate($stamp)
{
  $s = strval($stamp);
  return sprintf('%s/%s/%s %s', substr($s,2,2), substr($s,4,2),
		 substr($s,0,2),substr($s,6,2));
}

function GetUniqueStamps($db)
{
  $list = QueryArray($db, 'SELECT DISTINCT stamp
FROM object_info
ORDER BY stamp DESC');

  $results = array();
  for ($i = 0; $i < count($list); $i ++)
    array_push($results, $list[$i][0]);

  return $results;
}

function SpectrumURL($pmf)
{
  $plate = substr($pmf,0,4);
  return sprintf('http://www.autonlab.org/sdss/images/iii_spec/%s/figure-%s.png', $plate, PMF_DashForm($pmf));
}

function DetailsURL($ra, $dec)
{
  // return sprintf('http://cas.sdss.org/astro/en/tools/explore/obj.asp?ra=%f%%20&dec=%f', $ra, $dec);
  return sprintf('http://skyserver.sdss3.org/dr8/en/tools/explore/obj.asp?ra=%f&dec=%f', $ra, $dec);
}
function SimbadURL($ra, $dec)
{
  return sprintf('http://simbad.u-strasbg.fr/simbad/sim-coo?Radius=1&CooEqui=2000&Radius.unit=arcmin&CooFrame=FK5&submit=submit%%20query&CooEpoch=2000&CooDefinedFrames=none&Coord=%f%%20%f', $ra, $dec);
}
function NedURL($ra, $dec)
{
  return sprintf('http://ned.ipac.caltech.edu/cgi-bin/nph-objsearch?search_type=Near+Position+Search&in_csys=Equatorial&in_equinox=J2000.0&obj_sort=Distance+to+search+center&lon=%fd&lat=%fd&radius=1.0', $ra, $dec);
}
function DetailsURL_PMF($pmf)
{
  return sprintf('http://skyserver.sdss3.org/dr8/en/tools/explore/obj.asp?plate=%d&mjd=%d&fiber=%d', intval(substr($pmf,0,4)), intval(substr($pmf,4,5)), intval(substr($pmf,9,4)));
}

function PhotoURL($ra, $dec)
{
  // return sprintf('http://casjobs.sdss.org/ImgCutoutDR7/getjpeg.aspx?ra=%f&dec=%f&scale=0.2&width=250&height=250', $ra, $dec);
  return sprintf('http://skyservice.pha.jhu.edu/DR8/ImgCutout/getjpeg.aspx?ra=%f&dec=%f&scale=0.2&width=200&height=200', $ra, $dec);
}

// get the html snippet for an object's images
function GenObjectImages($pmf, $ra, $dec, $im_height)
{
  $spec = SpectrumURL($pmf);
  $photo = PhotoURL($ra, $dec);
  $details = DetailsURL($ra, $dec);

  $html = sprintf('<a href="%s" target="_blank"><img src="%s" border="0" height="%d" id="img_photo"></a>', $details, $photo, $im_height);
  $html .= sprintf('<a href="%s" target="_blank"><img src="%s" border="0" height="%d" id="img_spectrum"></a>', $spec, $spec, $im_height);
  return $html;
}

// generate the description html for an object
function GenObjectDescription($info)
{
  $subcla = $info['subcla'];
  $pos = strpos($subcla, '(');
  if ($pos != false) $subcla = substr($subcla, 0, $pos-1);

  return sprintf('
%s - %s, 
<a href="%s" target="_blank">SIMBAD</a>, 
<a href="%s" target="_blank">NED</a>
<br>
<span style="font-size:12;">
%s Score: %0.4g (#%d) <br>
Observed: %s, Processed: %s
</span>',
		 $info['cla'], $subcla, 	
		 SimbadURL($info['ra'], $info['dec']),
		 NedURL($info['ra'], $info['dec']),
		 PMF_DashForm($info['pmf']), 
		 $info['score'], $info['rank'],
		 MJD2YMD($info['mjd']),
		 Stamp_ToDate($info['stamp']));
}

function GenCommentList($labels) 
{
  if (count($labels) == 0)
    return 'No comment yet. ';
  
  $html = '';
  for ($i = 0 ; $i < count($labels) ; $i ++) {
    $l = $labels[$i];
    $html .= sprintf('<div class="label_item"><a href="../membership/web_user_profile.php?email=%s" target="_blank">%s</a>: [%d] %s.</div>', str_replace('@', '%40', $l['author']), $l['author'], $l['rating'], $l['comment']);
  }
  return $html;
}

function GetObjectList($db, $det_run_id, $mjd, $stamp, $label_filter, 
		       $sort_order, $page, $page_size)
{
  // sort
  if($sort_order == 'rand') {
    $mami = QueryArray($db, 'SELECT max(score) as ma, min(score) as mi from object_score WHERE run_id == '.$det_run_id); 
    $ma = $mami[0]['ma']; $mi = $mami[0]['mi'];
    $q = (rand()+1.0) / (getrandmax() + 1.0);
    $thresh = pow($q*0.9, 5)*($ma - $mi) + $mi;
    $order_clause = ' AND s.score < '.$thresh.' ORDER BY s.score DESC';
  } else {
    $order_clause = ' ORDER BY s.score '.$sort_order;
  }

  // mjd date
  if ($mjd == 'all')
    $mjd_clause = '';
  else {
    $today = date('Ymd');
    $mjd_cut = YMDtoMJD(intval(substr($today,0,4)), 
			intval(substr($today,4,2)),
			intval(substr($today,6,2))) - $mjd;
    $mjd_clause = ' AND info.mjd >= '.$mjd_cut;
  }

  // stamp
  if ($stamp == 'all')
    $stamp_clause = '';
  elseif ($stamp == 'recent') {
    $stamp = QueryScalar($db, 'SELECT max(stamp) FROM object_info');
    $stamp_clause = ' AND info.stamp == '.$stamp;
  } else {
    $stamp_clause = ' AND info.stamp == '.$stamp;
  }

  // label filter
  if ($label_filter == 'all') {
    $label_clause = '';
  } else {
    $label_clause = ' AND s.pmf '.($label_filter=='unrated'?'NOT':'').' IN (SELECT pmf FROM object_label)';
  }

  // pager
  $pager_clause = ' LIMIT '.(($page - 1)*$page_size).', '.$page_size;

  // assemble
  $cmd = '
SELECT s.pmf as pmf
FROM object_score as s
'.($stamp_clause == '' && $mjd_clause == '' ? '' : 'INNER JOIN object_info as info ON s.pmf = info.pmf').'
WHERE s.run_id = '.$det_run_id.$stamp_clause.$mjd_clause.$label_clause.$order_clause.$pager_clause;

  return QueryArray($db, $cmd, false);
}

function GetObjectData($db, $pmf, $det_run_id)
{
  // basic info
  $cmd = 'SELECT pmf, z, ra, decl as dec, stamp, mjd, cla, subcla, sdss_id 
FROM object_info WHERE pmf = '.$pmf;
  $info = QueryArray($db, $cmd, false); 
  if (count($info) == 0) {
    return NULL;
  } else {
    $info = $info[0];
  }

  // scores
  $cmd = 'SELECT score, rank FROM object_score WHERE pmf = '.$pmf.' AND run_id = '.$det_run_id;
  $score = QueryArray($db, $cmd, false);
  if (count($score) == 0) { // no label
    $score = array('score'=>0,'rank'=>0);
  } else {
    $score = $score[0];
  }

  return array_merge($info, $score);
}

function GetObjectLabel($db, $pmf)
{
  $cmd = 'SELECT rating, comment, author, last_update FROM object_label WHERE pmf = '.$pmf;
  return QueryArray($db, $cmd, false);
}

// update the label info into the DB
function UpdateObjectLabels($db, $pmf, $rating, $comment, $author)
{
  if ((int)$rating == 0) $rating = 'NULL';
  $comment = trim($comment);

  $deleting = $rating == 'NULL' & $comment == '';

  $cmd = sprintf("SELECT count(pmf) FROM object_label where pmf=%s AND author='%s';", $pmf, $author);
  $result = QueryScalar($db, $cmd);

  $cmd = '';
  if ($result == 0) { // add new
    if (!$deleting) {
      $cmd = sprintf("INSERT INTO object_label
(pmf, rating, comment, author, last_update)
VALUES 
(%s, %s, '%s', '%s', '%s')
", $pmf, $rating, $comment, $author, date("y-m-d G:i:s"));
    }
  } else { // update
    if (!$deleting) {
      $cmd = sprintf("
UPDATE object_label
SET rating=%s, comment='%s', last_update='%s'
WHERE pmf=%s AND author='%s'
", $rating, $comment, date("y-m-d G:i:s"), $pmf, $author);
    } else {
      $cmd = sprintf("DELETE FROM object_label WHERE pmf=%s AND author='%s'",$pmf,$author);
    }
  }

  if ($cmd != '') {
    return Execute($db, $cmd, true);
  } else {
    return true;
  }
}

function GetSimilarObjects($pmf, $feat_code, $sim_code, $num)
{  
  $db = GetSimDB();
  $cmd = '
SELECT pmf2 as pmf FROM object_similarity
WHERE feature='.$feat_code.'
AND similarity_type='.$sim_code.'
AND pmf1='.$pmf.'
ORDER BY similarity DESC
LIMIT '.$num;
  $alikes = QueryArray($db, $cmd, false);
  $db->close();

  if (count($alikes) == 0)
    return $alikes;

  // check if in the main db
  // need optimization
  $db = GetMainDB();
  $results = array();
  $cmd = 'SELECT pmf FROM object_info WHERE pmf=';
  for ($i = 0; $i < count($alikes); $i ++) {
    $row = $alikes[$i];
    $cur = $db->query($cmd.$row['pmf']);
    if ($cur->fetchArray())
      array_push($results, $row);
  }
  $db->close();

  return $results;
}

?>
