<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html><head>
<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type"><title>Auton SDSS II - DR7</title>
<style type="text/css">
    <!--
       body {
       margin-left: 200px;
       margin-top: 50px;
       margin-right: 200px;
       }
      -->
</style>
</head>
<body>
<h1>SDSS II DR7 Object Search</h1>

<form method="get" action="web_list.php" name="main"><input name="submit" value="Search" type="submit"><br><br><br>

<table style="text-align: left; width: 100%;" border="0" cellpadding="2" cellspacing="2">
<tbody>
<tr>
   <td>Object Type:</td>
   <td>
   <select style="width: 200px;" name="class">
   <option value="star">Star</option>
   <option value="galaxy">Galaxy</option>
   <option value="quasar">Quasar</option>
   </select>
   </td>
</tr>

<tr><td colspan="2"><hr></td></tr>

<tr>
   <td style="width: 200px;">Scoring Feature:</td>
   <td>
   <select style="width: 200px;" name="det_feat">
   <option selected="selected">Spectrum</option>
   <option>SpectrumS1</option>
   <option>Continuum</option>
   <option>ContinuumS1</option>
   </select>
</td>
</tr>
<tr>
<td>Scorer:</td>
<td>
<select style="width: 200px;" name="scorer">
<optgroup label="Global PCA">
	<option value="pca_accum_err" selected="selected">Accumulative Error</option>
	<option value="pca_rec_err">Reconstruction Error</option>
	<option value="pca_dist">M. Distance</option>
	<option value="pca_dist_out">M. Distance in Minor Subspace</option>
	<option value="pca_accum_dist_out">Accumulative M. Distance</option>
</optgroup>
<optgroup label="MMF">
	<option value="mmf_e_svd">MMF-Entry SVD</option>
	<option value="mmf_r_svd">MMF-Row SVD</option>
	<option value="mmf_e_nmf">MMF-Entry NMF</option>
	<option value="mmf_r_nmf">MMF-Row NMF</option>
</optgroup>
<optgroup label="Neighborhood">
	<option value="knn_mean_dist">Mean Distance</option>
	<option value="knn_max_dist">Max Distance</option>
</optgroup>
</select>
<br>
</td>
</tr>
<tr>
<td>Rating Status:</td>
<td>
<select style="width: 200px;" name="labeled">
   <option selected="selected" value="all">All</option>
   <option value="rated">Rated</option>
   <option value="unrated">Unrated</option>
   </select>
</td>
</tr>
<tr>
   <td>Sort:</td>
   <td>
   <select style="width: 200px;" name="sort">
   <option selected="selected" value="desc">DESC</option>
   <option value="asc">ASC</option>
   <option value="rand">RAND</option>
   </select>
</td>
</tr>

<tr><td colspan="2"><hr></td></tr>

<tr>
   <td style="width: 200px;">Classification Feature:</td>
   <td>
   <select style="width: 200px;" name="cla_feat">
   <option selected="selected">SpectrumS1-Color</option>
   </select>
   </td>
</tr>
<tr>
<td>Classifier:</td>
<td>
<select style="width: 200px;" name="classifier">
   <option value="mlr_uw" selected="selected">Multi-Logistic</option>
   <option value="mlr_w">Multi-Logistic Weighted</option>
   <option value="svm_uw">SVM</option>
   <option value="svm_w">SVM Weighted</option>
</select>
<br>
</td>
</tr>

<tr>
<td>SIMBAD Type:</td>
<td>
<input name="sbd_type" value="" style="width: 195px"></input>
</td>
</tr>
<tr>
<td>Predicted Type:</td>
<td>
<input name="pred_type" value="" style="width: 195px"></input>
</td>
</tr>
</tbody>
</table>
<input name="page" value="1" type="hidden">
</form>

<?php 
require_once('../ui.php');
echo GenPageFoot();
?>

<br>
</body></html>
