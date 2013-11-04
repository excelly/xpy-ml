<?php

error_reporting(E_ALL);
ini_set('display_errors', 'On');
session_start();

require_once('../ui.php');
require_once('../membership/user.php');
require_once('func.php');

$user = GetUser();

$mobile = IsMobile();
$default_row_size = $mobile ? 1 : 3;
$page_size = $mobile ? 10 : 20;

$default_det = 'drmf_accum_err';
// show random detector
/* $default_det = array_keys($scorer_code); */
/* $default_det = $default_det[rand(0, count($default_det)-1)]; */
/* $default_det = str_replace('accum_dist', 'dist', $default_det); */
/* if (strpos($default_det, 'knn') !== false) */
/*   $default_det = 'pca_rec_err'; */

$det_feat = GetEntry($_GET,          'feature', 'Spectrum');
$scorer = GetEntry($_GET,            'scorer',  $default_det);
$cla = GetEntry($_GET,               'class',   'star');
$mjd = GetEntry($_GET,               'mjd',     'all');
$stamp = GetEntry($_GET,             'stamp',   'recent');
$labeled = strtolower(GetEntry($_GET,'labeled', 'all'));
$sort = strtolower(GetEntry($_GET,   'sort',    'desc'));
$page = GetEntry($_GET,              'page',    1);
$row_size = GetEntry($_GET,          'row_size',$default_row_size);
$pmf_list = GetEntry($_GET,          'pmf_list','');
$list_mode = $pmf_list == '' ? 'query' : 'pmfs';

$det_run_id = GetDetRunID($det_feat, $scorer, $cla);

if ($list_mode == 'query') {
  $db = GetMainDB();
  $obj_list = GetObjectList($db, $det_run_id, $mjd, $stamp, $labeled,
			    $sort, $page, $page_size);
  $stamps = GetUniqueStamps($db);
  $db->close();
} else {
  $pmf_list = explode('.', $pmf_list);
  $obj_list = array();
  for ($i = 0; $i < count($pmf_list); $i ++)
    array_push($obj_list, array('pmf' => $pmf_list[$i]));
  $stamps = array();
}

$page_size = count($obj_list);

?>

<html>

<head>
<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
<title>Auton SDSS III</title>
<link rel="stylesheet" type="text/css" href="../style.css" />
<script src="../script.js" language="javascript"></script>
</head>

<body>

<?php
echo GenPageHeader($user);
echo GenPager($page, $sort);
?>

<h1>SDSS III Object Labeling</h1>

<form method="get" action="" name="main">

<div id="div_query">
<table border="0">
<tr>
  <td>Object</td>
  <td>Observed on</td>
  <td>Processed on</td>
  <td>Feature</td>
  <td>Detector</td>
  <td>Status</td>
  <td>Sort</td>
  <td>Figure</td>
</tr>
<tr>
  <td>
  <select style="width: 70px;" name="class" title="Objet class" id="filt_class" onChange="this.form.submit();">
  <option value="star" selected="selected">Star</option>
  <option value="galaxy">Galaxy</option>
  <option value="qso">Quasar</option>
  </select>
  </td>
  <td>
  <select style="width: 120px;" name="mjd" title="Observation Date" id="filt_mjd" onChange="this.form.submit();">
  <option value="all" selected="selected">All</option>
  <option value="1">Today</option>
  <option value="7">Last Week</option>
  <option value="30">Last Month</option>
  <option value="90">Last 3 Months</option>
  <option value="180">Last 6 Months</option>
  <option value="365">Last Year</option>
  </select>
  </td>
  <td>
  <select style="width: 100px;" name="stamp" title="Processing Date" id="filt_stamp" onChange="this.form.submit();">
  <option value="all" selected="selected">All</option>
  <?php
  for ($i = 0; $i < min(10, count($stamps)); $i ++) {
    printf('<option value="%d" %s>%s</option>', 
	   $stamps[$i], $i == 0 ? 'selected="selected"' : '',
	   Stamp_ToDate($stamps[$i]));
  }
  ?>
  </select>
  </td>
  <td>
  <select style="width: 120px;" name="feature" title="Feature" id="filt_feat" onChange="this.form.submit();">
  <option value="Spectrum" selected="selected">Spectrum</option>
  <option value="SpectrumS1">SpectrumS1</option>
  </select>
  </td>
  <td>
  <select style="width: 150px;" name="scorer" title="Detector" id="filt_det" onChange="this.form.submit();">
  <optgroup label="PCA">
  <option value="pca_rec_err" selected="selected">Rec. Err</option>
  <option value="pca_accum_err">Accumu. Err</option>
  <option value="pca_dist">M. Distance</option>
  <option value="pca_dist_out">M. Distance 2</option>
  </optgroup>
  <optgroup label="Robust PCA">
  <option value="rpca_aprx">RPCA</option>
  <option value="drmf_aprx">DRMF</option>
  <option value="drmf_rec_err">R - Rec. Err</option>
  <option value="drmf_accum_err">R - Accumu. Err</option>
  <option value="drmf_dist">R - M. Distance</option>
  <option value="drmf_dist_out">R - M. Distance 2</option>
  </optgroup>
  <optgroup label="KNN">
  <option value="knn_mean_dist">Mean Distance</option>
  <option value="knn_max_dist">Max Distance</option>
  </optgroup>
  </select>
  </td>
  <td>
  <select style="width: 90px;" name="labeled" title="Labeling status" id="filt_lab" onChange="this.form.submit();">
  <option selected="selected" value="all">All</option>
  <option value="rated">Labeled</option>
  <option value="unrated">Unlabeled</option>
  </select>
  </td>
  <td>
  <select style="width: 80px;" name="sort" title="Sort order" id="filt_sort" onChange="this.form.submit();">
  <option selected="selected" value="desc">DESC</option>
  <option value="asc">ASC</option>
  <option value="rand">RAND</option>
  </select>
  </td>
  <td>
  <select style="width: 80px;" name="row_size" title="Figure Size" id="row_size" onChange="this.form.submit();">
  <option value="5">Tiny</option>
  <option value="4">Small</option>
  <option selected="selected" value="3">Medium</option>
  <option value="2">Large</option>
  <option value="1">Fit</option>
  </select>
  </td>
</tr>
</table>
</div>
<br>

<?php

for($i = 0; $i < $page_size; $i ++) {
  echo'
<iframe src ="" frameBorder="0" scrolling="no" id="fr'.$i.'">
<p>Please use a browser that supports iframes.</p>
</iframe>';
}

if ($page_size == 0)
  echo '<h2>Nothing found. Please search again.</h2>';

echo GenPageFooter(); 

?>

</form>
</body>

<script type="text/javascript">

<?php echo 'list_mode="'.$list_mode.'"'; ?>

if (is_mobile()) {
  document.body.style.marginLeft = 5;
  document.body.style.marginRight = 5;
}

// set the filter
if (list_mode == "pmfs") {
  document.getElementById("div_query").innerHTML='Look alike objects';
  set_visible("div_pager", false);
} else {
  set_value("filt_class", "<?php echo $cla; ?>");
  set_value("filt_mjd", "<?php echo $mjd; ?>");
  set_value("filt_stamp", "<?php echo $stamp; ?>");
  set_value("filt_feat", "<?php echo $det_feat; ?>");
  set_value("filt_det", "<?php echo $scorer; ?>");
  set_value("filt_lab", "<?php echo $labeled; ?>");
  set_value("filt_sort", "<?php echo $sort; ?>");
  set_value("row_size", <?php echo $row_size; ?>);
}

width = page_width();
row_size = <?php echo $row_size; ?>;

inner_im_w = Math.floor((width - 30 - (row_size + 1)*10)/row_size);
inner_im_h = inner_im_w/2.34;

frame_w = inner_im_w;
space_h = <?php echo $user ? 260 : 160; ?>;
frame_h = inner_im_h + space_h;

frames = document.getElementsByTagName('iframe');
for (i = 0; i < frames.length; i++) {
  set_size(frames[i], frame_h, frame_w);
}

<?php
for ($i = 0; $i < $page_size; $i ++) {
  printf('document.getElementById("fr%d").src = "web_obj.php?pmf=%s&det_run_id=%s";', $i, $obj_list[$i]['pmf'], $det_run_id);
}
?>

</script>

</html>
