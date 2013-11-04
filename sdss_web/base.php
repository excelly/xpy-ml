<?php

$feature_code = array('spectrum' => 1,
		      'continuum' => 2,
		      'spectrums1' => 3,
		      'continuums1' => 4,
		      'lines' => 5,
		      'spectrum-color' => 6,
		      'continuum-color' => 7,
		      'spectrums1-color' => 8,
		      'continuums1-color' => 9);

$scorer_code = array('pca_rec_err' => 1,
		     'pca_accum_err' => 2,
		     'pca_dist' => 3,
		     'pca_dist_out' => 4,
		     'pca_accum_dist_out' => 5,
		     'drmf_rec_err' => 6,
		     'drmf_accum_err' => 7,
		     'drmf_dist' => 8,
		     'drmf_dist_out' => 9,
		     'drmf_accum_dist_out' => 10,
		     'rpca_aprx' => 11,
		     'drmf_aprx' => 12,
		     'knn_mean_dist' => 13,
		     'knn_max_dist' => 14);

$similarity_code = array('l2' => 1);

$classifier_code = array('mlr_uw' => 1,
			 'mlr_w' => 2,
			 'svm_uw' => 3,
			 'svm_w' => 4);

$spec_cln_code = array('star' => 1,
		     'galaxy' => 2,
		     'quasar' => 3);

$root_url = 'http://www.autonlab.org/sdss/';

function redirect($url) {
  exit('<script>window.location="'.$url.'";</script>');
}

function IsMobile()
{
  $agent = $_SERVER['HTTP_USER_AGENT'];
  if (stripos($agent, 'phone') !== false ||
      stripos($agent, 'ipod') !== false ||
      stripos($agent, 'blackberry') !== false ||
      stripos($agent, 'android') !== false) {
    return true;
  } else {
    return false;
  }
}

// get an entry from $arr. if failed return $default
function GetEntry($arr, $key, $default = NULL)
{
  return array_key_exists($key, $arr) ? $arr[$key] : $default;
}

// get a field from an array of arrays
function GetField($arr, $field)
{
  $result = array();
  for ($i = 0; $i < count($arr); $i ++)
    array_push($result, $arr[$i][$field]);
  return $result;
}

function zfill($s, $l) 
{
  return str_pad(strval($s), $l, '0', STR_PAD_LEFT);
}

function ReportError($msg, $var_to_dump = 0, $level = 2)
{
  if ($level >= 2)
    $color = 'fdd';
  elseif ($level == 1)
    $color = 'ddd';
  else
    $color = 'dfd';

    echo '<div style="background-color:'.$color.';border-style:dotted;border-width:1px;">';
  
  if ($msg != '')
    echo '<p>'.$msg.'</p>';
  if ($var_to_dump != 0) 
    var_dump($var_to_dump);
  echo '</div>';
}

function Execute($db, $cmd, $debug = false)
{
  if (!$db->exec($cmd) || $db->changes() == 0) {
    if ($debug)
      ReportError('Excution failed::<br>'.$cmd.'<br>'.$db->lastErrorMsg());
    return false;
  } else {
    return $db->changes();
  }
}

function QueryArray($db, $cmd, $debug = false)
{
  $cur = $db->query($cmd);
  $debug = $cur === false ? true : $debug;

  if ($debug) ReportError($cmd.'<br><br>'.$db->lastErrorMsg());

  $results = array();
  while ($row = $cur->fetchArray(SQLITE3_BOTH))
    array_push($results, $row);
  $cur->finalize();

  if ($debug) ReportError('', $results);
  
  return $results;
}

function QueryScalar($db, $cmd, $debug = false)
{
  $cur = $db->query($cmd);
  $debug = $cur == false ? true : $debug;

  if ($debug) ReportError($cmd.'<br><br>'.$db->lastErrorMsg());

  $result = $cur->fetchArray(SQLITE3_BOTH);
  $result = $result ? $result[0] : false;
  $cur->finalize();

  if ($debug) ReportError('', $result);
  
  return $result;
}

// map the information of a run into a unique ID
function GetDetRunID($feature, $scorer, $spec_class)
{
  global $feature_code, $scorer_code, $spec_cln_code;

  $f = $feature_code[strtolower($feature)];
  $s = $scorer_code[strtolower($scorer)];
  $c = $spec_cln_code[strtolower($spec_class)];

  if ($f == 0 || $s == 0 || $c == 0) {
    echo '<p>Unknown detector config.</p>';
  }

  return $f*1e6 + $s*1e3 + $c;
}  
  
function GetClaRunID($feature, $classifier, $spec_class)
{
  global $feature_code, $classifier_code, $spec_cln_code;

  $f = $feature_code[strtolower($feature)];
  $s = $classifier_code[strtolower($classifier)];
  $c = $spec_cln_code[strtolower($spec_class)];

  if ($f == 0 || $s == 0 || $c == 0) {
    echo '<p>Unknown classifier config.</p>';
  }

  return $f*1e6 + $s*1e3 + $c;
}

// get the object class from the custom code
function GetObjectClass($run_id)
{
  return $run_id % 1e3;
}
function GetFeatureCode($run_id)
{
  return floor($run_id / 1e6);
}
function PMF_DashForm($pmf)
{
  return substr($pmf,0,4).'-'.substr($pmf,4,5).'-'.substr($pmf,9,4);
  // return zfill(floor($pmf/1000000000, 4)).'-'.zfill(fmod(floor($pmf/10000),100000), 5).'-'.zfill(fmod($pmf,10000), 4);
}

function YMDtoMJD ($yr, $month, $day)
{    
    $l = ceil(($month - 14) / 12);
             
    $p1 = $day - 32075 + floor(1461 * ($yr + 4800 + $l) / 4);
    $p2 = floor(367 * ($month - 2 - $l*12) / 12);
    $p3 = 3*floor(floor(($yr + 4900 + $l) / 100) / 4);
    
    return $p1 + $p2 - $p3 - 2400001;
}

function MJD2YMD ($mjd)
{
    $jdi = $mjd + 2400001;

    $l = $jdi + 68569;
    $n = floor (4 * $l / 146097);
   
    $l = floor ($l) - floor ((146097 * $n + 3) / 4);
    $year = floor (4000 * ($l + 1) / 1461001);
    
    $l = $l - (floor (1461 * $year / 4)) + 31;
    $month = floor (80 * $l / 2447);
    $day = $l - floor (2447 * $month / 80);
    
    $l = floor ($month / 11);
    $month = floor ($month + 2 - 12 * $l);
    $year = floor (100 * ($n - 49) + $year + $l);
    
    return sprintf('%d/%d/%d', $month, $day, $year % 100);
}

?>
