<?php

error_reporting(E_ALL);
ini_set('display_errors', 'On');
session_start();

require_once('../ui.php');
require_once('user.php');

$db = GetUserDB();
$view_mode = array_key_exists('email', $_GET);

if ($view_mode) {
  $email = GetEntry($_GET, 'email', false);
} else {
  $email = GetEntry($_SESSION, 'email', false);
}

$user = fetch_user_profile($db, NULL, $email);
if (!$user) {
  $db->close();
  if ($view_mode) {
    exit('<p>User not found.</p>');
  } else {
    redirect('web_login.php');
  }
}

if (count($_POST) > 0 && !$view_mode) {
  if (array_key_exists('update', $_POST)) {
    $user['password'] = trim($_POST['password']);
    $user['nick_name'] = trim($_POST['nick_name']);
    $user['real_name'] = trim($_POST['real_name']);
    $user['institute'] = trim($_POST['inst']);
    if ($user['nick_name'] == '')
      $user['nick_name'] = EmailUsername($user['email']);

    if (!update_user_profile($db, $user)) {
      ReportError('Failed to update user profile');
    } else {
      ReportError('User profile updated', 0, 0);
    }
  }

  if (array_key_exists('retrieve_pw', $_POST)) {
    ReportError('Not implemented yet. Contact the admin.');
  }
}

$db->close();

?>

<html>
<head>
<title>SDSS@Auton User Profile</title>
<link rel="stylesheet" type="text/css" href="../style.css" />
<script src="../script.js" language="javascript"></script>
</head>

<body>
<form id="profile" action="" method="post">

<h1>User Profile</h1>

<table>
<tr><td>Email:</td><td>
<input type="text" name="email" id="email" size="40" maxlength="50" readonly="readonly"  value="<?php echo $user['email']; ?>"/>
</td></tr>
<tr id="tr_pw"><td>Password:</td><td>
<input type="password" name="password" id="password" size="40" maxlength="50" value=""/>
</td></tr>
<tr id="tr_nick"><td>Nick name:</td><td>
<input type="text" name="nick_name" id="nick_name" size="40" maxlength="50" value="<?php echo $user['nick_name']; ?>"/>
</td></tr>
<tr id="tr_realname"><td>Real name:</td><td>
<input type="text" name="real_name" id="real_name" size="40" maxlength="50" value="<?php echo $user['real_name']; ?>"/>
</td></tr>
<tr id="tr_inst"><td>Institute:</td><td>
<input type="text" name="inst" id="inst" size="40" maxlength="100" value="<?php echo $user['institute']; ?>"/>
</td></tr>
</table>

<input type="submit" name="update" id="btn_update" value="Update" />

<p><a href="../iii/web_list.php">SDSS III list</a></p>

<?php echo GenPageFooter(); ?>

</form>
<body>

<script type="text/javascript">

<?php
  if ($view_mode) {
    echo 'set_visible("tr_pw", false);';
    echo 'set_visible("btn_update", false);';
    echo 'document.getElementById("nick_name").readOnly = "readonly";';
    echo 'document.getElementById("real_name").readOnly = "readonly";';
    echo 'document.getElementById("inst").readOnly = "readonly";';
  }
?>

</script>

</html>
