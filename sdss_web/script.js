function set_size(e, h, w, use_css)
{
    if (typeof e == "string")
	e = document.getElementById(e);

    if (use_css) {
	if (h > 0) e.style.height = h;
	if (w > 0) e.style.width = w;
    } else {
	if (h > 0) e.height = h;
	if (w > 0) e.width = w;
    }
}

function set_visible(e, visible)
{
    if (typeof e == "string")
	e = document.getElementById(e);

    e.style.display = visible ? "inline" : "none";
}

function set_value(e, val)
{
    if (typeof e == "string")
	e = document.getElementById(e);

    e.value = val;
}

function page_width()
{
    return document.body.clientWidth;
}

function is_mobile()
{
    ua = navigator.userAgent.toLowerCase();
    return ua.indexOf('sphone') >= 0 || ua.indexOf('android') >= 0 || ua.indexOf('ipod') >= 0 || ua.indexOf('blackberry') >= 0;
}