<?php

require_once('../base.php');

function GetMainDB() 
{
  return $db = new SQLite3('/var/www/db/sdss_web.db3');
}

// get the image of the specified position
function PhotoURL($ra, $dec, $size = 200, $scale = 0.3, $theta = NULL,$opt = '')
{
  if($theta !== NULL)
    $scale = $theta*2.0*3600/$size;
  
//  return sprintf('http://sdss.lib.uchicago.edu/ImgCutoutDR7/getjpeg.aspx?ra=%f&dec=%f&scale=%f&width=%d&height=%d&opt=%s', $ra, $dec, $scale, $size, $size, $opt);
  return sprintf('http://casjobs.sdss.org/ImgCutoutDR7/getjpeg.aspx?ra=%f&dec=%f&scale=%f&width=%d&height=%d&opt=%s', $ra, $dec, $scale, $size, $size, $opt);
}

// get the html snippet for an object's images
function GenHtmlObject($ra, $dec, $spec_id, $height)
{
  $image_url = PhotoURL($ra, $dec, $height);
//  $detail_page = sprintf('http://sdss.lib.uchicago.edu/dr7/en/tools/explore/obj.asp?sid=%s', $spec_id);
//  $spectrum_url = sprintf('http://sdss.lib.uchicago.edu/dr7/en/get/specById.asp?id=%s', $spec_id);
  $detail_page = sprintf('http://cas.sdss.org/astro/en/tools/explore/obj.asp?sid=%s', $spec_id);
  $spectrum_url = sprintf('http://cas.sdss.org/astro/en/get/specById.asp?id=%s', $spec_id);

  return sprintf('
<a href="%s" target="_blank"><img src="%s" border="0" height="%d"></a>
<a href="%s" target="_blank"><img src="%s" border="0" height="%d"></a>', 
		 $detail_page, $image_url, $height, $spectrum_url, $spectrum_url, $height);
}

// generate the description html for an object
function GenObjectDescription($ra, $dec, $z, $score, $rank, $spec_id)
{
  return sprintf(' SpecID=%s, Score=%g (top %d), <br>
RA=%0.3f, DEC=%0.3f, Z=%0.3f', 
		 $spec_id, $score, $rank, $ra, $dec, $z);
}

// get the object list of current search. score_ub is the upper bound of scores in target page and score_lb is the lower bound
function GetObjectList($db, $det_run_id, $cla_run_id, $label_filter, $sbd_type, $pred_type, $sort_order, $page, $page_size)
{
  $label_filter = strtolower($label_filter) == 'all' ? '' : sprintf('AND labeled=%d', $label_filter == 'rated');
  $sbd_filter = $sbd_type == '' ? '' : sprintf(' AND simbad.obj_type="%s"', $sbd_type);
  $pred_filter = $pred_type == '' ? '' : sprintf(' AND class.predicted="%s"', $pred_type);

  $order_clause = 'ORDER BY scores.score '.$sort_order;
  if($sort_order == 'rand')
    $order_clause = 'AND scores.score >= (abs(random()) %% round((SELECT max(score) from object_score WHERE run_id == '.$det_run_id.')))';

  $cmd = sprintf('SELECT scores.specObjID as spec_id
FROM object_score as scores 
INNER JOIN object_info as info ON scores.specObjID=info.specObjID
INNER JOIN object_rating as r ON scores.specObjID=r.specObjID
LEFT OUTER JOIN simbad as simbad ON scores.specObjID=simbad.specObjID 
LEFT OUTER JOIN object_class as class ON class.specObjID=scores.specObjID
WHERE 
scores.run_id=%d AND class.runID=%d
%s 
%s
%s
%s
LIMIT %d, %d', 
		 $det_run_id, $cla_run_id, 
		 $label_filter, 
		 $sbd_filter, 
		 $pred_filter, 
		 $order_clause, 
		 ($page - 1)*$page_size, $page_size);

  return QueryArray($db, $cmd, false);
}
// get the list of objects without classification info
function GetObjectList_NC($db, $det_run_id, $label_filter, $sort_order, $page, $page_size)
{
  $label_filter = strtolower($label_filter) == 'all' ? '' : sprintf('AND labeled=%d', $label_filter == 'rated');
  $sbd_filter = $sbd_type == '' ? '' : sprintf(' AND simbad.obj_type="%s"', $sbd_type);
  $pred_filter = $pred_type == '' ? '' : sprintf(' AND class.predicted="%s"', $pred_type);

  $cmd = sprintf('SELECT scores.specObjID as spec_id
FROM object_score as scores 
INNER JOIN object_info as info ON scores.specObjID=info.specObjID
INNER JOIN object_rating as r ON scores.specObjID=r.specObjID
WHERE 
scores.run_id=%d
%s 
%s
LIMIT %d, %d', 
		 $det_run_id, 
		 $label_filter, 
		 $order_clause, 
		 ($page - 1)*$page_size, $page_size);

  return QueryArray($db, $cmd, false);
}

function GetObjectData($db, $spec_id, $det_run_id, $cla_run_id)
{
  // basic info
  $cmd = 'SELECT specObjID as spec_id, z, ra, dec
FROM object_info WHERE specObjID = '.$spec_id;
  $info = QueryArray($db, $cmd, false);
  if (count($info) == 0) {
    exit('Cannot find specified PMF.');
  } else {
    $info = $info[0];
  }

  // label
  $cmd = 'SELECT rating, tag, comment FROM object_rating WHERE specObjID = '.$spec_id;
  $label = QueryArray($db, $cmd, false);
  if (count($label) == 0) { // no label
    $label = array('rating'=>NULL,'tag'=>'','comment'=>'');
  } else {
    $label = $label[0];
  }

  // scores
  $cmd = 'SELECT score, rank FROM object_score WHERE specObjID = '.$spec_id.' AND run_id = '.$det_run_id;
  $score = QueryArray($db, $cmd, false);
  if (count($score) == 0) { // no label
    $score = array('score'=>0,'rank'=>0);
  } else {
    $score = $score[0];
  }

  // classification
  $cmd = 'SELECT predicted || " ; " || round(confidence*100) as pred FROM object_class where specObjID = '.$spec_id.' AND runID = '.$cla_run_id;
  $pred = QueryArray($db, $cmd, false);
  if (count($pred) == 0) { // no label
    $pred = array('pred'=>'');
  } else {
    $pred = $pred[0];
  }

  // simbad
  $cmd = 'SELECT obj_type || " ; " || spec_type || " ; " || dist as sbd FROM simbad WHERE specObjID = '.$spec_id;
  $simbad = QueryArray($db, $cmd, false);
  if (count($simbad) == 0) { // no simbad
    $simbad = array('sbd'=>'');
  } else {
    $simbad = $simbad[0];
  }

  return array_merge($info, $label, $score, $pred, $simbad);
}

// update the label info into the DB
function UpdateObjectLabels($db, $spec_id, $rating, $tag, $comment)
{
  if ((int)$rating == 0) $rating = 'NULL';
  $tag = trim($tag);
  $comment = trim($comment);

  $labeled = ($rating != 'NULL') | ($tag != '') | ($comment != '');

  $cmd = sprintf("UPDATE object_rating
SET rating=%s, tag='%s', comment='%s', labeled=%d, last_update='%s'
WHERE specObjID=%s
", $rating, $tag, $comment, $labeled, date("y-m-d G:i:s"), $spec_id);

  if (!$db->exec($cmd) || $db->changes() != 1) {
    ReportError('Failed to update label:<br>'.$cmd.'<br />'.$db->lastErrorMsg());
    return False;
  }
  else {
    return True;
  }
}

?>
