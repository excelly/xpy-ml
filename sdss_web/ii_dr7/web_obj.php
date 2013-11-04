<html>
<head>
<link rel="stylesheet" type="text/css" href="../style.css" />
<title>SDSS Object Information</title>
<script type="text/javascript">
function change_to_inframe()
{
  document.getElementById("alone_link").style.display = "inline";
  document.body.style.marginTop = 0;
  document.body.style.marginLeft = 0;
}
</script>
</head>
<body>

<?php

error_reporting(E_ALL);
ini_set('display_errors', 'On');

require_once('../ui.php'); 
require_once('func.php'); 

$spec_id = GetEntry($_GET, 'spec_id', '');
if ($spec_id == '') // if nothing to show
  exit('No object specified.');
$det_run_id = GetEntry($_GET, 'det_run_id', 0);
$cla_run_id = GetEntry($_GET, 'cla_run_id', 0);

$db = GetMainDB();

$updating = count($_POST) > 0;

if ($updating) {// update the labels of objects
  $rating = GetEntry('rating', $_POST, 0);
  $tag = GetEntry('tag', $_POST, '');
  $comment = GetEntry('comment', $_POST, '');
    
  UpdateObjectLabels($db, $spec_id, $rating, $tag, $comment);
}

$info = GetObjectData($db, $spec_id, $det_run_id, $cla_run_id);
$db->close();

?>

<form method="post" action="" name="main">

<?php
  echo '
<table style="text-align: left;" border="0">
  <tbody>
    <tr>
      <td style="vertical-align: top;background-color: #CCDCFF" colspan="1" rowspan="3">'.
        GenObjectDescription($info['ra'], $info['dec'], $info['z'], $info['score'], $info['rank'], $info['spec_id']).
      '</td>
      <td style="vertical-align: top;">Anomaly Rating:</td>
      <td style="vertical-align: top;">'.
  GenRatingGroup($info['rating']).
     '</td>
    </tr>
    <tr>
      <td style="vertical-align: top:">Classification:</td>
      <td style="vertical-align: top;"><input size="68" value="SIMBAD: '.
	 (is_null($info['sbd']) ? 'N/A' : $info['sbd']).
	 ' | Auton: '.(is_null($info['pred']) ? 'N/A' : $info['pred']).
	 '" readonly="true"><br>
      </td>
    </tr>
    <tr>
      <td style="vertical-align: top;">Tag:</td>
      <td style="vertical-align: top;"><input size="68" name="tag" value="'.$info['tag'].'"><br>
      </td>
    </tr>
    <tr>
      <td>'.
	 GenHtmlObject($info['ra'],$info['dec'],$info['spec_id'],200).
	 '</td>
      <td style="vertical-align: top;">Comments:</td>
      <td style="vertical-align: top;"><textarea cols="50" rows="5" name="comment">'.
	 $info['comment'].
	 '</textarea><br />
          <input style="width:100;" type="submit" value="Save" />
          <a href="" style="display:none;" target="_blank" id="alone_link">
          <img style="position:relative;top:8px;" src="../images/popout.gif" border=0 />
          </a>
      </td>
    </tr>
  </tbody>
</table>';

?>

<script type="text/javascript">
  if (top != self) {
    change_to_inframe();
  }
</script>  

</form>

</body>
</html>
