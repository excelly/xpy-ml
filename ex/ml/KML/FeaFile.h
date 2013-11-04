/*!
*	@file		FeaFile.h
*	@brief		Fea-File read/write I/O base class
*	@author		jianguo.li@intel.com
*	@version	1.0	--- Dec, 2006: original implementation, support varlen feature
*	@version	2.0 --- Jan, 2007: compatible with MPI parallel I/O model
*	@version	2.1 --- Feb, 2007: fix bug for file larger than 2GB
*	@version	2.2 --- Mar, 2007: support filling based write, and fix some bugs
*	@version	2.3 --- June, 2007: fix the fpos_t imcompatible problem in GCC(Linux platform)
*/

#ifndef _FEA_FILE_HPP
#define _FEA_FILE_HPP

#include <vector>
#include <stdio.h>

//#pragma warning(disable:1478)

#if !defined WINVER && !defined _MFC_VER && !defined _ATL_VER
	typedef unsigned char BYTE;
	typedef unsigned long ULONG;
	typedef long long int LONG64;
#endif

#define FEA_FILE_VERSION_V1  0x20061218
#define FEA_FILE_VERSION	 0x20070128

// FeaFile Header
typedef struct tag_FEATURE_FILE_HEADER
{
	long	nVersion;		//	version number, 0x20061218
	long	nRecords;		//	total number of samples
	long	nFeaDim;		//	dimensions of the feature
	long	nElemType;		//	element type(1=char; short; long; float; double; ) 
	long	nElemSize;		//  size of the element
	BYTE	bIndexTab;			//  1 with index table, 0 for without index table
	BYTE	bVarLen;		//  1 for variant length features, 0 for fixed length
	char	szFeaName[64];	//	feature name
	char	szReserved[42];	//	reserved, padding to 128 BYTE
}FEA_FILE_HEADER;

// offset index tab: optional for fixed length, must for var-length
typedef struct tag_INDEX_TAB{
	LONG64	nOffset;		//	offset of current sample from the beginning: compatible for file larger than 2GB
	ULONG	nFeaLength;		//	features length of current sample
	ULONG	nOuterIndex;	//	outside record index number
}FEA_INDEX_TAB;

// element type
enum gElemType{ELEM_TYPE_CHAR = 1, ELEM_TYPE_SHORT, ELEM_TYPE_LONG, 
				ELEM_TYPE_FLOAT, ELEM_TYPE_DOUBLE, ELEM_TYPE_STRUCT};

// from element type to element size
const int g_ElemType2Size[] = {0,	// no used 0
	sizeof(char),	// ELEM_TYPE_CHAR		1
	sizeof(short),	// ELEM_TYPE_SHORT		2
	sizeof(long),	// ELEM_TYPE_LONG		3
	sizeof(float),	// ELEM_TYPE_FLOAT		4
	sizeof(double),	// ELEM_TYPE_DOUBLE		5
	0				// user defined struct type
};

// reader buffer: read all into buffer, or read one record each time
// writer buffer: larger than 16MB, flush to disk
// Base class for FeaFile
class CFeaFileBase
{
public:
	CFeaFileBase();
	virtual~CFeaFileBase();

public:
	// interface
	virtual void openFile(const char* fname) = 0;

	virtual void closeFile()
	{
		if( m_fpFeaFile != NULL )
		{
			fclose(m_fpFeaFile);
			m_fpFeaFile = NULL;
		}
	}

	virtual void releaseMemory();

	void dumpHeader2File(FILE* fp = stdout, bool bIndexTab = false);

public:
	long getVersion()const
	{
		return m_oFeaHead.nVersion;
	}

	long getRecordNum()const
	{
		return m_oFeaHead.nRecords;
	}

	long getFeatureDim()const
	{
		return m_oFeaHead.nFeaDim;
	}

	long getElemType()const
	{
		return m_oFeaHead.nElemType;
	}

	long getElemSize()const
	{
		return m_oFeaHead.nElemSize;
	}

	bool isVarLength()const
	{
		return (m_oFeaHead.bVarLen == 1);
	}

	bool isWithIndexTab()const
	{
		return (m_oFeaHead.bIndexTab == 1);
	}

	const char* getFeaName()const
	{
		return m_oFeaHead.szFeaName;
	}

	const char* getReservation()const
	{
		return m_oFeaHead.szReserved;
	}

	FEA_FILE_HEADER getFileHeader()
	{
		return m_oFeaHead;
	}

	ULONG getCurRecordIndex() const
	{
		return m_nCurRecordNo;
	}

	LONG64 getTotalFeaLength();

	// get number of samples in Var-len feaFile
	long getSampleNum4VarLen();

	LONG64 getOffsetAtIdx(int idx); // get offset at a given record index

	long getFeaLenAtIdx(int idx); // get feature length at a given record index

	long getCurOuterIndex(int idx); // get the outside index of current record

protected:
	FEA_FILE_HEADER m_oFeaHead;		// File Header
	FEA_INDEX_TAB  *m_pOffset;	// offset index tab: optional for fixed length, must for var-length

	FILE * m_fpFeaFile;			// Fea file that contains the data
	char * m_pCurFea;			// pointer to current feature

	ULONG  m_nFileHeadLength;	// length of fileHeader
	ULONG  m_nCurRecordNo;		// current record number inside the filw	
	LONG64  m_nCurOffset;		// current offset from the File beginning
};

class CFeaFileReader: public CFeaFileBase
{
public:
	CFeaFileReader();
	virtual ~CFeaFileReader();

	// open files
	virtual void openFile(const char* fname);

	virtual void releaseMemory();

public:
	// load all data into the inside buffer
	void readAllData();

	// load data into the outside buffer
	void readAllData(char*& buffer);

	// get one recorder at an index
	char* readRecordAt(int iFrmIdx);

	char* readRecordAtRange(int iStIdx, int iEndIdx, int* nCntStatus = NULL);

	char* getNextSample4VarLen(bool bReStart = false);

	void dumpAll2TxtFile(const char* fname);

private:
	char* m_pAllFeature;	// all data are read in memory
	char* m_pRangeBuffer;
	long m_oldVarLen;

	// for var-length file
	long m_VarCurOffset;
	long m_VarCurRecLen;
	char* m_pVarFea;
};

class CFeaFileWriter: public CFeaFileBase
{
public:
	CFeaFileWriter(int bufferSize = 16, bool bFilling = false);

	virtual ~CFeaFileWriter();

	// open file
	// bFilling = true, allocate the memory, and fill all into memory
	// bFilling = false, do not allocate the memory, and sequential write data
	virtual void openFile(const char* fname);

	virtual void closeFile();

	// must call after closeFile
	virtual void releaseMemory();

public:
	void setFileHeader(const FEA_FILE_HEADER& feaHeader);

	// write feature to buffer, feaLength = 0 mean fixed length feature
	// sequential writing
	void writeRecordAt(void* pFea, long nOuterIdx, long feaLength = 0);

	// filling mode file writer: only support fixed-length Fea-File
	// fill specific row
	void fillElemAt(void* pFea, int nRow);
	// fill specific element
	void fillElemAt(void* pFea, int nRow, int nDim);

	// force writing buffer to disk
	void flush2Disk();

private:
	bool	m_bFilling;		// when true, allocate the data for filling
	bool	m_bFileExist;
	// feature write buffer
	char*	m_pFeaBuffer;	// feature buffer
	ULONG	m_nBufSize;		// buffer size in MB, default 16MB
	ULONG   m_nCurBufOffset;	// current offset in the buffer
	long	m_nCurBufRecord;	// current record number in the buffer
	long	m_nMaxBufRecords;	// maximum number of records in the buffer
};

#endif
