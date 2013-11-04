<?php

require_once('base.php');

$tooltip_map = array(1 => 'Very interesting!',
		     2 => 'Interesting',
		     3 => 'Average',
		     4 => 'Boring',
		     5 => "It shouldn't be here!");

// generate the rating group for an object
function GenRatingGroup($rating = 0)
{
  global $colormap, $tooltip_map;

  $html = sprintf('<div class="div_rating">');
  
  for($i = 1; $i <= 5; $i ++) {
    $html .= sprintf('<input title="%s" name="rating" value="%d" type="radio" %s>%d', $tooltip_map[$i], $i, $rating == $i ? 'checked' : '', $i);
  }

  $html .= '&nbsp;&nbsp;&nbsp;&nbsp;';
  $html .= sprintf('<input title="Not specified" name="rating" value="0" type="radio" %s>N/A ', $rating === NULL ? 'checked' : '');
  $html .= sprintf('<input title="Bad observation" name="rating" value="-1" type="radio" %s>Noise', $rating < 0 ? 'checked' : '');

  return $html.'</div>';
}

// get the query string to a new page. 
// handling the page number and score filters
// $direction -1 means previous, 1 means next
function GetNewPageQuery($page, $direction)
{
  $query = $_SERVER['QUERY_STRING'];

  $pos = strpos($query, '&score_');
  if ($pos) 
    $query = substr($query, 0, $pos);

  $pos = strpos($query, 'page=');
  if ($pos == false) {
    return $query .= '&page='.($page + $direction);
  } else {
    return str_replace(sprintf('page=%d', $page), 
		       sprintf('page=%d', $page + $direction), 
		       $query);
  }
}

// generate the navigator html
// handling the page number and score filters
function GenPager($page, $sort_order)
{
  // prev
  $query = GetNewPageQuery($page, -1);
  $prev = $page == 1 ? 'Prev' : sprintf('<a href="web_list.php?%s">Prev</a>', $query);

  // next
  $query = GetNewPageQuery($page, 1);
  $next = sprintf('<a href="web_list.php?%s">Next</a>', $query);

  return sprintf('<div id="div_pager">&nbsp; %s &nbsp; Page %s &nbsp; %s</div>', $prev, $page, $next);
}

// generate the footer html
function GenPageHeader($user = false)
{
  global $root_url;

  if ($user) {
    return sprintf('<div id="div_header">Hello, <a href="%smembership/web_user_profile.php">%s</a>. <a href="%smembership/web_login.php?logout=1">Log out</a></div>', $root_url, $user['email'], $root_url);
  } else {
    return sprintf('<div id="div_header">Hello, Guest. <a href="%smembership/web_login.php">Log in</a></div>', $root_url);
  }
}

// generate the footer html
function GenPageFooter()
{
  return '<div id="div_footer">
Liang Xiong (<img style="position:relative;top:3px;" src="http://cs.cmu.edu/~lxiong/images/im.gif" width="130">), AutonLab, 2/28/2012
</div>';
}

?>
