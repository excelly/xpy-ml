<?php

error_reporting(E_ALL);
ini_set('display_errors', 'On');
session_start();
require_once('../ui.php');
require_once('user.php');

// handle logout
$logout = GetEntry($_GET, 'logout', '0');
if ($logout == '1') {
  session_unset();
  setcookie('email', '', time() - 3600, '/');
  redirect($_SERVER['HTTP_REFERER']);
}

// handle login and registration
$email = '';
if (count($_POST) > 0) {
  $email = trim($_POST['email']);
  $password = trim($_POST['password']);

  if ($email == '' || $password == '') {
    ReportError('Email and password cannot be empty.');
  } else {
    $db = GetUserDB();
    if (array_key_exists('login', $_POST)) { // login
      $user = authenticate_user($db, $email, $password);
      if ($user === false) {
	ReportError('Authentication failed');
      } else {
	$_SESSION['email'] = $user['email'];
	setcookie('email', $user['email'], time()+60*60*24*30, '/');

	redirect('../iii/web_list.php');
      }
    } else { // register
      if (!register_user($db, $email, $password)) {
	ReportError('Registration failed.');
      } else {
	$user = fetch_user_profile($db, NULL, $email);
	$_SESSION['email'] = $user['email'];
	setcookie('email', $user['email'], time()+60*60*24*30, '/');

	redirect('web_user_profile.php');
      }
    }
  }
}

?>

<html>

<head>
<title>SDSS@Auton Login</title>
<link rel="stylesheet" type="text/css" href="../style.css" />
</head>

<body>
<form id="login" action="" method="post">

<h1>Login &amp; Registration</h1>

<h3>
<span style="color:red;">Warning:</span> 
<br>
Do not use your primary password here.
<br>
This website is not secure (yet)!
</h3>

<table>
<tr><td>Email:</td><td>
<input type="text" name="email" id="email" size="30" maxlength="50" value="<?php echo $email; ?>" />
</td></tr>
<tr><td>Password:</td><td>
<input type="password" name="password" id="password"  size="30" maxlength="50" />
</td></tr>
</table>

<input type="submit" name="login" value="Login" />
<input type="submit" name="register" value="Register" />

<?php echo GenPageFooter(); ?>

</form>
</body>
</html>
