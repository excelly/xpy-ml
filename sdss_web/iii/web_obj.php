<?php

error_reporting(E_ALL);
ini_set('display_errors', 'On');
session_start();

require_once('../ui.php');
require_once('../membership/user.php');
require_once('func.php'); 

$user = GetUser();
$pmf = GetEntry($_GET, 'pmf', '');
$det_run_id = GetEntry($_GET, 'det_run_id', 0);

?>

<html>

<head>
<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
<title>SDSS Object Information</title>
<link rel="stylesheet" type="text/css" href="../style.css" />
<script src="../script.js" language="javascript"></script>
</head>

<body>

<?php

if ($pmf == '') // if nothing to show
  exit('<p>No object specified.</p>');

$db = GetMainDB();

if (count($_POST) > 0) {// update the labels of objects
  $rating = GetEntry($_POST, 'rating', 0);
  $comment = GetEntry($_POST, 'comment', '');
  if ($user)
    UpdateObjectLabels($db, $pmf, $rating, $comment, $user['email']);
  else
    ReportError('Log in before comment please.');
}

$info = GetObjectData($db, $pmf, $det_run_id);
$labels = GetObjectLabel($db, $pmf);
$db->close();

if ($info == NULL)
  exit('<p>Cannot find specified PMF: '.$pmf.'</p>');

// handle labels
$label_own = array('rating'=>NULL,'comment'=>'');
if (count($labels) == 0) {
  $rating_min = 0;
} else {
  $rating_min = 100;
  for ($i = 0 ; $i < count($labels) ; $i ++) {
    $rating_min = min($rating_min, $labels[$i]['rating']);
    if ($labels[$i]['author'] == $user['email']) {
      $label_own = $labels[$i];
      break;
    }
  }
}
$others_comments = GenCommentList($labels);
if (!$user) $others_comments .= 'Log in to add your own comments.';
if ($rating_min < 0) $rating_min = 99;

// handle similar objects
$feat_code = $det_run_id == 0 ? $feature_code['spectrum'] : GetFeatureCode($det_run_id);
$sim_code = $similarity_code['l2'];

$alikes = GetSimilarObjects($pmf, $feat_code, $sim_code, 10);
if (count($alikes) == 0) {
  $alike_pmfs = '';
} else {
  $alike_pmfs = strval($alikes[0]['pmf']);;
  for ($i = 1; $i < count($alikes); $i ++)
    $alike_pmfs .= '.'.strval($alikes[$i]['pmf']);
}

?>

<form method="post" action="" name="main">

<div id="div_obj">

<div id="div_info" class="obj_info <?php echo 'rate'.$rating_min;?>">
  <?php echo GenObjectDescription($info); ?>
</div>

<div id="div_fig">
  <?php echo GenObjectImages($info['pmf'], $info['ra'], $info['dec'], 200); ?>
</div>

<div id="div_comments">
  <?php echo $others_comments; ?>
</div>

<div id="div_label">

<?php echo GenRatingGroup($label_own['rating']); ?>

<table border="0" width="100%">
<tr>
<td style="vertical-align:top; width:100px;">
  Comment:
  <br>
  <span style="font-size:12;">Use "#" to tag</span>
  <br>
  <input style="width:90px;" type="submit" value="Save" />
</td>
<td>
  <textarea style="width:100%;" rows="2" name="comment"><?php echo $label_own['comment']; ?></textarea>
</td>
</tr>
</table>

</div>

<div id="div_obj_misc">
<a href="web_list.php?pmf_list=<?php echo $alike_pmfs; ?>&det_run_id=<?php echo $det_run_id; ?>" target="_blank" id="alikes">Show similar spectra</a>
&nbsp;&nbsp;
<a href="" target="_blank" id="alone_link">
<img style="position:relative;top:8px;" src="../images/popout.gif" border="0" height="25px" />
</a>
</div>

</form>

<?php echo GenPageFooter(); ?>

<script type="text/javascript">

width = page_width();
if (self == top) {
  if (!is_mobile()) {
    document.body.style.marginLeft = width*0.15-10;
    document.body.style.marginRight = width*0.15-10;
    document.body.style.marginTop = 30;
    width = width*0.7;
  } else {
    width = width - 50;
  }
} else {
    document.body.style.marginLeft = 0;
    document.body.style.marginTop = 0;
    document.body.style.marginRight = 0;
    width = width - 5;
}

im_h = Math.round(width/2.34);
set_size("img_photo", im_h, -1, false);
set_size("img_spectrum", im_h, -1, false);

<?php 

if (!$user) {
  echo 'set_visible("div_label", false);';
}

echo 'alike_pmfs="'.$alike_pmfs.'";';

?>

if (alike_pmfs == "") {
  set_visible("alikes", false);
}

if (top == self) {
  set_visible("alone_link", false);
  document.getElementById('div_comments').style.height = 150;
} else {
  document.getElementById("alone_link").href = document.URL;
  set_visible("div_footer", false);
}

</script> 

</body>
</html>
