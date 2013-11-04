import os
from distutils.sysconfig import get_python_lib
from distutils.core import setup, Extension

site_dir=get_python_lib()

include_dirs=[site_dir+"/numpy/core/include/numpy"];

module_exc=Extension(
        "exc", 
        sources=["exc.cpp"],
        include_dirs=include_dirs);

kml_srcs=['kml.cpp', 'KM_ANN.cpp', 'KMeans.cpp', 'KMterm.cpp', 'KMrand.cpp', 'KCutil.cpp', 'KCtree.cpp', 'KMdata.cpp', 'KMcenters.cpp', 'KMfilterCenters.cpp', 'KMlocal.cpp']
module_kml=Extension(
        "kml", 
        sources=["./ml/KML/"+src for src in kml_srcs],
        include_dirs=include_dirs);

setup(name="ex_c_libs",
      version="0.2",
      description="CXX module for fast functions",
      ext_modules=[module_exc, module_kml]);
