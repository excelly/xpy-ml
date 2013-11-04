#include <Python.h>
#include <arrayobject.h>
#include <vector>

#include "KMterm.h"
#include "KMdata.h"
#include "KMfilterCenters.h"
#include "KMlocal.h"

using namespace std;

extern "C" {
  static PyObject* kml_main(PyObject *self, PyObject *args);
}

static PyMethodDef KMLMethods[] = {
  {"KML", kml_main, METH_VARARGS,
   "KML(X, output, type, maxIter, verbose)\n\
    kmeans-local (birch) clustering of X.\n\
    X: sample matrix. n x dim. A C-continguous float32 numpy array.\n\
    output: the output cluster centers. K x dim.\n\
    type: clustering type. 0-Lloyds, 1-Swap, 2-EZ_Hybrid, 3-Hybrid (recommended)."},
  {NULL, NULL, 0, NULL}
};

PyObject* WrongValue(const char* msg)
{
  PyErr_SetString(PyExc_ValueError, msg);  return NULL;
}
PyObject* WrongType(const char* msg)
{
  PyErr_SetString(PyExc_TypeError, msg);  return NULL;
}
PyObject* Wrong(const char* msg)
{
  PyErr_SetString(PyExc_RuntimeError, msg);  return NULL;
}
bool IsCont(PyArrayObject* arr)
{
  return (arr->flags & NPY_CARRAY) != 0;
}
int Type(PyArrayObject* a)
{
  return a->descr->type_num;
}

extern "C" {
  static PyObject* kml_main(PyObject *self, PyObject *args)
  {
    PyArrayObject *X, *output;
    int type, maxIter, verbose;
    if (!PyArg_ParseTuple(args, "OOiii", &X, &output, 
			  &type, &maxIter, &verbose))
      return WrongType("input arguments cannot be parsed");

    if (sizeof(float) != sizeof(KMcoord))
      return Wrong("KML is using data types other than float32");

    if (!IsCont(X) || Type(X) != NPY_FLOAT32 || X->nd != 2)
      return WrongValue("X must be a C-continguous float32 matrix");
    if (!IsCont(output) || Type(output) != NPY_FLOAT32 || output->nd != 2)
      return WrongValue("output must be a C-continguous float32 matrix");
    int n = X->dimensions[0];
    int dim = X->dimensions[1];
    int K = output->dimensions[0];
    if (output->dimensions[1] != dim)
      return WrongValue("output dim not the same with X");
    if (K < 2 || K > n)
      return WrongValue("K must be between 2 and # samples");
    if (type < 0 || type > 3)
      return WrongValue("Unknown clustering type");
    if (maxIter < 1)
      return WrongValue("maxIter must be greater than 0");

    KMterm term(maxIter, 0, 0, 0, 0.1, 0.1, 3, 0.5, 10, 0.95);
    KMdata dataPts(dim, n);
    memcpy(&dataPts[0][0], X->data, dim*n*sizeof(KMcoord));

    if (verbose) printf("Building KC tree...");
    dataPts.buildKcTree();
    
    KMfilterCenters ctrs(K, dataPts);
    KMlocal *alg;
    switch(type) {
    case 0:
      alg = new KMlocalLloyds(ctrs, term);
      if(verbose) printf("Clustering with Lloyds.\n");
      break;
    case 1:
      alg = new KMlocalSwap(ctrs, term);
      if(verbose) printf("Clustering with Swap.\n");
      break;
    case 2:
      alg = new KMlocalEZ_Hybrid(ctrs, term);
      if(verbose) printf("Clustering with EZ_Hybrid.\n");
      break;
    case 3:
      alg = new KMlocalHybrid(ctrs, term);
      if(verbose) printf("Clustering with Hybrid.\n");
      break;
    default:
      return WrongValue("Unknown clustering type");
    }

    alg->verbose = verbose;
    ctrs = alg->execute();

    double distortion = ctrs.getDist(false)/n;
    if (verbose)
      printf("KML completed. Stages=%d, Distortion=%0.4f.\n",
	     alg->getTotalStages(), distortion);
    delete alg;

    memcpy(output->data, &ctrs[0][0], dim*K*sizeof(KMcoord));

    return Py_BuildValue("d", distortion);
  }

  PyMODINIT_FUNC
  initkml() 
  {
    PyObject* m = Py_InitModule("kml", KMLMethods);
    if (m == NULL) {
      PyErr_SetString(PyExc_RuntimeError,"kml module failed to initialize");
      return;
    }
  
    import_array();
  }
}
