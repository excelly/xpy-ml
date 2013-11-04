#include <Python.h>
#include <arrayobject.h>

#include <vector>
#include <algorithm>

using namespace std;

/* OS related crap */
# if defined(_MSC_VER)

typedef unsigned __int8 BYTE;
typedef __int16 INT16;
typedef unsigned __int16 UINT16;
typedef __int32 INT32;
typedef unsigned __int32 UINT32;
typedef  __int64 INT64;
typedef unsigned __int64 UINT64;

#include <hash_map>
#include <hash_set>

using namespace stdext;

# else

#include <stdint.h>
typedef uint8_t BYTE;
typedef int16_t INT16;
typedef uint16_t UINT16;
typedef int32_t INT32;
typedef uint32_t UINT32;
typedef int64_t INT64;
typedef uint64_t UINT64;

#include <tr1/unordered_set>
#include <tr1/unordered_map>

using namespace std::tr1;

#define hash_set unordered_set
#define hash_map unordered_map

# endif

//#define DBG

/*********** list functions */

extern "C" {
  static PyObject* exc_encode(PyObject *self, PyObject *args);
  static PyObject* exc_argunique(PyObject *self, PyObject *args);
  static PyObject* exc_accumvector(PyObject *self, PyObject *args);
  static PyObject* exc_group(PyObject *self, PyObject *args);
  static PyObject* exc_merge_join(PyObject *self, PyObject *args);
  static PyObject* exc_kth(PyObject *self, PyObject *args);
}

static PyMethodDef ExcMethods[] = {
  {"encode", exc_encode, METH_VARARGS,
   "encode(input, codebook, output)\n\
    Encode an int array. Unfound entries have code -1\n\
    The input arrays must be continuous."},
  {"argunique", exc_argunique, METH_VARARGS,
   "output=argunique(input)\n\
    get the index of unique elements of an array using hash set. -1\n\
    output is not sorted."},
  {"accumvector", exc_accumvector, METH_VARARGS,
   "accumvector(subs, val, base, type)\n\
    accumulate val to base, for a dense 1D vector\n\
    type: 0 - sum, 1 - prod, 2 - max, 3 - min."},
  {"group", exc_group, METH_VARARGS,
   "groups=group(pos, val, n)\n\
    groups val according to pos. a list of arrays is returned.\n\
    n: total number of positions"},
  {"merge_join", exc_merge_join, METH_VARARGS,
   "indeces=merge_join(key1, key2)\n\
    return the index pairs of joined relationships.\n\
    key1 and key2 must be both sorted."},
  {"kth", exc_kth, METH_VARARGS,
   "kmin=kth(X, k)\n\
    return the k-th smallest element for each row of X.\n\
    X must be float32 or float64."},
  {NULL, NULL, 0, NULL}
};

/************* utils */

#define max(a, b) ((a) >= (b) ? (a) : (b))
#define min(a, b) ((a) <= (b) ? (a) : (b))
#define Index2D(i, j, ncol) ((i)*(ncol) + (j))

//shortcut for reporting errors
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

// vector computation
template <class T>
T prod(T* p, size_t n)
{
  T r = 1;
  for(size_t i = 0 ; i < n ; ++ i) r *= p[i];
  return r;
}
template <class T>
T sum(T* p, size_t n)
{
  T r = 0;
  for(size_t i = 0 ; i < n ; ++ i) r += p[i];
  return r;
}

// return the number of elements in arr
size_t numel(PyArrayObject* arr) 
{
  return prod(arr->dimensions, arr->nd);
}
// if the matrix if continuous in memory
bool IsCont(PyArrayObject* arr)
{
  return ((arr->flags & NPY_CARRAY) | (arr->flags & NPY_FARRAY)) != 0;
}
int Type(PyArrayObject* a)
{
  return a->descr->type_num;
}
// if two array has the same data type
bool SameType(PyArrayObject* a1, PyArrayObject* a2)
{
  return Type(a1) == Type(a2);
}
// if two array has the same size
bool SameSize(PyArrayObject* a1, PyArrayObject* a2)
{
  if(a1->nd != a2->nd) return false;
  for(int i = 0 ; i < a1->nd ; ++ i)
    if(a1->dimensions[i] != a2->dimensions[i]) return false;
  return true;
}
// convert a vector to a PyArrayObject
template <class T>
PyArrayObject* V2A(T* p, size_t n, int type_num) 
{
  npy_intp dims=n;
  PyArrayObject* output=(PyArrayObject*)PyArray_SimpleNew(1,&dims,type_num);

  if(sizeof(T) != output->descr->elsize)
    return (PyArrayObject*)WrongValue("type_num wrong in V2A");
  if(!IsCont(output))
    return (PyArrayObject*)Wrong("created array is not contiguous");

  memcpy(output->data, p, sizeof(T)*n);
  return output;
}
template <class T>
PyArrayObject* V2A(const vector<T>& v, int type_num) 
{
  return V2A(&v[0], v.size(), type_num);
}
// show an array of data
template <class T>
void ShowArray(const char* name, T* p, size_t n, 
	       const char* format="%d ")
{
  printf("exc: %s : (%d) [ ", name, (int)n);
  for(size_t i = 0 ; i < n ; ++ i) printf(format, p[i]);
  printf("]\n");
}
template <class T>
void ShowArray(const char* name, const vector<T>& v,
	       const char* format="%d ")
{
  ShowArray(name, &v[0], v.size(), format);
}
void ShowArray(const char* name, PyArrayObject* arr)
{
  size_t n = numel(arr);
  switch(Type(arr)) {
  case NPY_INT32:
    ShowArray(name, (INT32*)arr->data, n);break;
  case NPY_UINT32:
    ShowArray(name, (UINT32*)arr->data, n);break;
  case NPY_INT64:
    ShowArray(name, (INT64*)arr->data, n);break;
  case NPY_UINT64:
    ShowArray(name, (UINT64*)arr->data, n);break;
  case NPY_FLOAT32:
    ShowArray(name, (float*)arr->data, n, "%0.2f ");break;
  case NPY_FLOAT64:
    ShowArray(name, (double*)arr->data, n, "%0.2f ");break;
  default:
    printf("Unknown array type to show");    
  }
}

/************* implementations */

// encode using hash_map
template <class T>
void encode_in(T* input, size_t n, T* codebook, size_t nCode, 
	       INT32* output)
{
  hash_map<T, INT32> ht;
  typename hash_map<T, INT32>::const_iterator iter;

  for(size_t i = 0 ; i < nCode ; ++ i)
    ht.insert(pair<T, UINT32>(codebook[i], (INT32)i));

  for(size_t i = 0 ; i < n ; ++ i) {
    iter = ht.find(input[i]);
    output[i] = iter != ht.end() ? iter->second : -1;
  }
}

// unique using hash_set
template <class T>
void argunique_in(T* input, size_t n, vector<UINT64>& output)
{
  hash_set<T> ht;
  output.clear();

  for(size_t i = 0 ; i < n ; ++ i) {
    if(ht.find(input[i]) == ht.end()) {
      ht.insert(input[i]);
      output.push_back(i);
    }
  }
}

// accumulate to a vector 
template <class T_idx, class T_val>
void accumvector_in(T_idx* idx, T_val* val, size_t n, 
		    T_val* base, int type=0)
{
  if(type == 0) {
    for(size_t i = 0 ; i < n ; ++ i) {
      base[idx[i]] += val[i];
    }
  } else if(type == 1) {
    for(size_t i = 0 ; i < n ; ++ i) {
      base[idx[i]] *= val[i];
    }
  } else if(type == 2) {
    for(size_t i = 0 ; i < n ; ++ i) {
      base[idx[i]] = max(base[idx[i]], val[i]);
    }
  } else {
    for(size_t i = 0 ; i < n ; ++ i) {
      base[idx[i]] = min(base[idx[i]], val[i]);
    }
  }
}

// group values according to their positions
// n: number of tuples
template <class T_pos, class T_val>
void group_in(T_pos* pos, T_val* val, size_t n,
	      vector< vector<T_val> >& output)
{
  for(size_t i = 0 ; i < n ; ++ i)
    output[pos[i]].push_back(val[i]);
}

// merge join
template <class T>
void merge_join_in(T* key1, size_t n1, T* key2, size_t n2, 
		   vector<UINT32>& o1, vector<UINT32>& o2)
{
  size_t start1 = 0, start2 = 0, end1, end2, i, j;

  while(start1 < n1 && start2 < n2) {
    T val = key1[start1];

    // find end1
    for(end1 = start1 ; end1 < n1 && key1[end1] == val ; ++ end1);

    // find start2
    for(; start2 < n2 && key2[start2] < val ; ++ start2);

    // find end2
    for(end2 = start2 ; end2 < n2 && key2[end2] == val ; ++ end2);

    for(i = start1 ; i < end1 ; ++ i) {
      for(j = start2 ; j < end2 ; ++ j) {
	o1.push_back(i);
	o2.push_back(j);
      }
    }

    start1 = end1;
    start2 = end2;
  }
}

// kth smallest
template <class T>
void exc_kth_in(T* p, int m, int n, int k, T* output)
{
	vector<T> buffer(n);
	for (int i = 0 ; i < m ; ++i) {
		memcpy(&buffer[0], p + Index2D(i,0,n), sizeof(T)*n);
		nth_element(buffer.begin(), buffer.begin() + k, buffer.end());
		output[i] = buffer[k];
	}
}

/***************** functions called */

extern "C" {

  static PyObject* exc_encode(PyObject *self, PyObject *args)
  {
    PyArrayObject *input, *codebook, *output;
    if (!PyArg_ParseTuple(args, "OOO", &input, &codebook, &output))
      return WrongType("input arguments cannot be parsed");

#if defined(DBG)
    ShowArray("encode.input", input);
    ShowArray("encode.codebook", codebook);
#endif

    if(!IsCont(input) || !IsCont(codebook) || !IsCont(output))
      return WrongValue("input array must be contiguous");
    if(!SameType(input, codebook))
      return WrongValue("input and codebook should have the same type");
    if(!SameSize(input, output) || Type(output) != NPY_INT32)
      return WrongValue("output should be int32 and the same size as input");

    switch(input->descr->elsize) {
    case 1:
      encode_in((BYTE*)input->data, numel(input), 
		(BYTE*)codebook->data, numel(codebook), 
		(INT32*)output->data); break;
    case 2:
      encode_in((UINT16*)input->data, numel(input), 
		(UINT16*)codebook->data, numel(codebook), 
		(INT32*)output->data); break;
    case 4:
      encode_in((UINT32*)input->data, numel(input), 
		(UINT32*)codebook->data, numel(codebook), 
		(INT32*)output->data); break;
    case 8:
      encode_in((UINT64*)input->data, numel(input), 
		(UINT64*)codebook->data, numel(codebook), 
		(INT32*)output->data); break;
    default:
      return WrongValue("input element size wrong");
    }

    Py_RETURN_NONE;
  }

  static PyObject* exc_argunique(PyObject *self, PyObject *args)
  {
    PyArrayObject *input;
    if (!PyArg_ParseTuple(args, "O", &input))
      return WrongType("input arguments cannot be parsed");

#if defined(DBG)
    ShowArray("argunique.input", input);
#endif

    if(!IsCont(input) || input->nd != 1)
      return WrongValue("input array must be contiguous vector");

    size_t n = numel(input);
    vector<UINT64> result;
    switch(input->descr->elsize) {
    case 1:
      argunique_in((BYTE*)input->data, n, result); break;
    case 2: 
      argunique_in((UINT16*)input->data, n, result); break;
    case 4:
      argunique_in((UINT32*)input->data, n, result); break;
    case 8:
      argunique_in((UINT64*)input->data, n, result); break;
    default:
      return WrongValue("input element size wrong");
    }

    return PyArray_Return(V2A(result, NPY_UINT64));
  }

  static PyObject* exc_accumvector(PyObject *self, PyObject *args)
  {

    PyArrayObject *subs, *val, *base;
    int type;
    if (!PyArg_ParseTuple(args, "OOOi", &subs, &val, &base, &type))
      return WrongType("input arguments cannot be parsed");

#if defined(DBG)
    ShowArray("accumvector.subs", subs);
    ShowArray("accumvector.base", base);
    ShowArray("accumvector.val", val);
#endif

    if(type < 0 || type > 3)
      return WrongValue("unknown operation type");
    if(!IsCont(subs) || !IsCont(val) || !IsCont(base))
      return WrongValue("input array must be contiguous vector");
    if(!SameType(val, base))
      return WrongValue("val and base should have the same type");
    if(numel(subs) != numel(val))
      return WrongValue("subs and val should have the same size");
 
    int itype=Type(subs);
    int vtype=Type(val);
    size_t n = numel(subs);
    if(itype == NPY_INT32 && vtype == NPY_FLOAT32) {
      accumvector_in((INT32*)subs->data, (float*)val->data,
		     n, (float*)base->data, type);
    } else if(itype == NPY_INT32 && vtype == NPY_FLOAT64) {
      accumvector_in((INT32*)subs->data, (double*)val->data,
		     n, (double*)base->data, type);
    } else if(itype == NPY_INT64 && vtype == NPY_FLOAT32) {
      accumvector_in((INT64*)subs->data, (float*)val->data,
		     n, (float*)base->data, type);
    } else if(itype == NPY_INT64 && vtype == NPY_FLOAT64) {
      accumvector_in((INT64*)subs->data, (double*)val->data,
		     n, (double*)base->data, type);
    } else {
      return WrongValue("wrong input type");
    }

    Py_RETURN_NONE;
  }

  static PyObject* exc_group(PyObject *self, PyObject *args)
  {
    PyArrayObject *pos, *val;
    int l;
    if (!PyArg_ParseTuple(args, "OOi", &pos, &val, &l))
      return WrongType("input arguments cannot be parsed");

    if(!IsCont(pos) || !IsCont(val))
      return WrongValue("input array must be contiguous vector");
    if(numel(pos) != numel(val))
      return WrongValue("subs and val should have the same size");

    PyObject* output = PyTuple_New(l);
    if(!output) return Wrong("return tuple cannot be constructed");

    int itype=Type(pos);
    int vtype=Type(val);
    size_t n = numel(pos);
    if(itype == NPY_INT32 && vtype == NPY_INT32) {
      vector< vector<INT32> > result; result.resize(l);
      group_in((INT32*)pos->data, (INT32*)val->data, n, result);
    
      for(int i = 0 ; i < l ; ++ i)
	if(PyTuple_SetItem(output,i,
			   PyArray_Return(V2A(result[i],NPY_INT32))))
	  return Wrong("failed to return the grouped list");
    } else if(itype == NPY_INT32 && vtype == NPY_INT64) {
      vector< vector<INT64> > result; result.resize(l);
      group_in((INT32*)pos->data, (INT64*)val->data, n, result);
    
      for(int i = 0 ; i < l ; ++ i)
	if(PyTuple_SetItem(output,i,
			   PyArray_Return(V2A(result[i],NPY_INT64))))
	  return Wrong("failed to return the grouped list");
    } else if(itype == NPY_INT64 && vtype == NPY_INT32) {
      vector< vector<INT32> > result; result.resize(l);
      group_in((INT64*)pos->data, (INT32*)val->data, n, result);

      for(int i = 0 ; i < l ; ++ i)
	if(PyTuple_SetItem(output,i,
			   PyArray_Return(V2A(result[i],NPY_INT32))))
	  return Wrong("failed to return the grouped list");
    } else if(itype == NPY_INT64 && vtype == NPY_INT64) {
      vector< vector<INT64> > result; result.resize(l);
      group_in((INT64*)pos->data, (INT64*)val->data, n, result);
    
      for(int i = 0 ; i < l ; ++ i)
	if(PyTuple_SetItem(output,i,
			   PyArray_Return(V2A(result[i],NPY_INT64))))
	  return Wrong("failed to return the grouped list");
    } else {
      return WrongValue("wrong input type");
    }

    return output;
  }

  static PyObject* exc_merge_join(PyObject *self, PyObject *args)
  {
    PyArrayObject *key1, *key2;
    if (!PyArg_ParseTuple(args, "OO", &key1, &key2))
      return WrongType("input arguments cannot be parsed");

    if(!IsCont(key1) || !IsCont(key2))
      return WrongValue("input array must be contiguous vector");
    if(!SameType(key1, key2))
      return WrongValue("input must have the same type");

    vector<UINT32> o1, o2;
    if(Type(key1) == NPY_INT32) {
      merge_join_in((INT32*)key1->data, numel(key1),
		    (INT32*)key2->data, numel(key2),
		    o1, o2);
    } else if(Type(key1) == NPY_INT64) {
      merge_join_in((INT64*)key1->data, numel(key1),
		    (INT64*)key2->data, numel(key2),
		    o1, o2);
    } else {
      return WrongValue("wrong input type");
    }

    o1.reserve(o1.size() + o2.size());
    o1.insert(o1.end(), o2.begin(), o2.end());
    o2.clear();

    return PyArray_Return(V2A(o1, NPY_UINT32));
  }

  static PyObject* exc_kth(PyObject *self, PyObject *args)
  {
	  PyArrayObject *X;
	  int m, n, k;
	  if (!PyArg_ParseTuple(args, "Oi", &X, &k))
		  return WrongType("input arguments cannot be parsed");

	  if(!(X->flags & NPY_CARRAY))
		  return WrongValue("input array must be C-contiguous");
	  if(X->nd == 1) {
		  m = 1;
		  n = X->dimensions[0];
	  } else if (X->nd == 2) {
		  m = X->dimensions[0];
		  n = X->dimensions[1];
	  } else {
		  return WrongValue("X must have less than 2D");
	  }
	  if(k < 0 || k > n) {
		  return WrongValue("k should be between 0 and n_col");
	  }

	  switch(Type(X)) {
	  case NPY_FLOAT32:
		  {
			  vector<float> result(m);
			  exc_kth_in((float*)X->data, m, n, k, &result[0]);
			  return PyArray_Return(V2A(result, NPY_FLOAT32));
		  }
	  case NPY_FLOAT64: 
		  {
			  vector<double> result(m);
			  exc_kth_in((double*)X->data, m, n, k, &result[0]);
			  return PyArray_Return(V2A(result, NPY_FLOAT64));
		  }
	  default:
		  return WrongValue("input type wrong. float only.");
	  }
  }
}

/********************** routines parts */

extern "C" {

  PyMODINIT_FUNC
  initexc() 
  {
    PyObject* m = Py_InitModule("exc", ExcMethods);
    if (m == NULL) {
      PyErr_SetString(PyExc_RuntimeError,"exc module failed to initialize");
      return;
    }
  
    import_array();
  }

}
