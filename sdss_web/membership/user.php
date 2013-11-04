<?php

require_once('../base.php');

function GetUserDB()
{
  return new SQLite3('/home/lxiong/www/db/user.db3');
}

function ValidateEmail($email) 
{
  if (filter_var($email, FILTER_VALIDATE_EMAIL))
    return true;
  else {
    ReportError('Invalid Email', 0, 1);
    return false;
  }
}

function EmailUsername($email)
{
  $un = explode('@', $email); 
  return $un[0];
}

function GetEmail()
{
  $email = GetEntry($_SESSION, 'email', false);
  if ($email) return $email;
  
  $email = GetEntry($_COOKIE, 'email', false);
  if ($email) {
    $_SESSION['email'] = $email;
  }
  return $email;
}
 
function GetUser($db = false)
{
  $email = GetEmail();
  if ($email) {
    if ($db) {
      $user = fetch_user_profile($db, NULL, $email);
    } else {
      $db = GetUserDB();
      $user = fetch_user_profile($db, NULL, $email);
      $db->close();
    }

    return $user;
  } else {
    return false;
  }
}

function authenticate_user($db, $email, $password)
{
  $cmd = sprintf('SELECT * FROM users WHERE email = "%s" AND password = "%s";', $email, $password);

  $user = QueryArray($db, $cmd, false);
  if (count($user) == 0)
    return false;
  if (count($user) > 1)
    ReportError(sprintf('duplicate user found: %s', $email));

  return $user[0];
}

function fetch_user_profile($db, $user_id, $email = NULL)
{
  if (is_null($email)) {
    $cmd = sprintf('SELECT * FROM users WHERE user_id = %d', $user_id);
  } else {
    $cmd = sprintf('SELECT * FROM users WHERE email = "%s"', $email);
  }

  $user = QueryArray($db, $cmd, false);
  if (count($user) == 0)
    return false;
  if (count($user) > 1)
    ReportError(sprintf('duplicate user found: %s', $email));

  return $user[0];
}

function register_user($db, $email, $password)
{
  if (!ValidateEmail($email)) return false;

  $cmd = sprintf('SELECT count(*) from users WHERE email="%s"', $email);
  $existing_email = QueryScalar($db, $cmd, false);

  if ($existing_email > 0) {
    ReportError('Email already registered.', 0, 1);
    return false;
  } else {
    $cmd = sprintf('INSERT INTO users VALUES (NULL, "%s", "%s", "%s", "", "")', $email, $password, EmailUsername($email));
    return Execute($db, $cmd, false);
  }
}

function update_user_profile($db, $user)
{
  if (trim($user['password']) == '') { // not updating password
    $cmd = sprintf('UPDATE users SET nick_name="%s",real_name="%s",institute="%s" WHERE email="%s";', $user['nick_name'], $user['real_name'], $user['institute'], $user['email']);
  } else {
    $cmd = sprintf('UPDATE users SET password="%s",nick_name="%s",real_name="%s",institute="%s" WHERE email="%s";', $user['password'], $user['nick_name'], $user['real_name'], $user['institute'], $user['email']);
  }

  return Execute($db, $cmd);
}

?>
