<html>
<head>
<link rel="stylesheet" type="text/css" href="../style.css" />
<title>Auton SDSS</title>
</style>

</head>

<body>
<h1>SDSS Object Rating</h1>

<div>
<a href="http://cas.sdss.org/dr7/en/tools/search/sql.asp" target="_blank">DR7</a> &nbsp; 
<a href="http://www.sdss.org/dr7/dm/flatFiles/spSpec.html" target="_blank">FITS spec</a> &nbsp; 
<a href="http://simbad.u-strasbg.fr/guide/chF.htx" target="_blank">Object types</a> &nbsp; 
</div>
   
<?php 

error_reporting(E_ALL);
ini_set('display_errors', 'On');

require_once('../ui.php'); 
require_once('func.php'); 

$det_feature=GetEntry($_GET,             'det_feat', 'Spectrum');
$cla_feature=GetEntry($_GET,             'cla_feat', 'Spectrum');
$scorer=GetEntry($_GET,                  'scorer', 'pca_rec_err');
$classifier=GetEntry($_GET,              'classifier', 'mlr_uw');
$spec_class=GetEntry($_GET,              'class', 'star');
$sbd_type=trim(GetEntry($_GET,           'sbd_type', ''));
$pred_type=trim(GetEntry($_GET,          'pred_type', ''));
$label_filter=strtolower(GetEntry($_GET, 'labeled', 'all'));
$sort_order=strtolower(GetEntry($_GET,   'sort', 'desc'));
$page=GetEntry($_GET,                    'page', 1);
$page_size=20;

$det_run_id=GetDetRunID($det_feature, $scorer, $spec_class);
$cla_run_id=GetClaRunID($cla_feature, $classifier, $spec_class);

// handling DB
$db = GetMainDB(); // the db connection

if (GetObjectClass($det_run_id) != 1) {
  $results=GetObjectList_NC($db, $det_run_id, $label_filter, $sort_order, $page, $page_size);
} else {
  $results=GetObjectList($db, $det_run_id, $cla_run_id, $label_filter, $sbd_type, $pred_type, $sort_order, $page, $page_size);
}

$db->close();

?>

<form method="post" action="" name="main">

<?php echo GenPager($page, $sort_order); ?>
  
<?php
// show the list of objects
for($i = 0 ; $i < count($results) ; $i ++) {
  $dest = 'web_obj.php?spec_id='.$results[$i]['spec_id'].'&det_run_id='.$det_run_id.'&cla_run_id='.$cla_run_id;

  echo '
<iframe src ="'.$dest.'" width="100%" height="280" frameBorder="0" scrolling="no">
    <p>Please use a browser that supports iframes.</p>
</iframe>';
}

if (count($results) == 0) { // if nothing to list
  echo '<p>Nothing found. Please search again.</p>';
}

?>

<?php echo GenPageFooter(); ?>

</form>

</body>
</html>
