#include <stdio.h>
#include <stdlib.h>
#include <cassert>

#include "FeaFile.h"

CFeaFileBase::CFeaFileBase()
{
	m_fpFeaFile = NULL;
	m_pOffset = NULL;
	m_pCurFea  = NULL;
	m_nFileHeadLength = sizeof(FEA_FILE_HEADER);
	m_nCurRecordNo = 0;	
	m_nCurOffset = 0L;

	m_oFeaHead.nVersion = FEA_FILE_VERSION;
	m_oFeaHead.nRecords = 0;
	m_oFeaHead.nFeaDim = 0;
	m_oFeaHead.nElemType = ELEM_TYPE_FLOAT;	// default
	m_oFeaHead.nElemSize = g_ElemType2Size[ELEM_TYPE_FLOAT];
	m_oFeaHead.bIndexTab = 0;
	m_oFeaHead.bVarLen = 0;
	m_oFeaHead.szFeaName[0] = '\0';
	m_oFeaHead.szReserved[0] = '\0';
}

CFeaFileBase::~CFeaFileBase()
{
	closeFile();
	releaseMemory();
}

void CFeaFileBase::releaseMemory()
{
	if( m_pCurFea != NULL )
	{
		delete [] m_pCurFea;
		m_pCurFea = NULL;
	}
	if( m_pOffset != NULL )
	{
		delete [] m_pOffset;
		m_pOffset = NULL;
	}
}

// total feature length, not include FeaHeader, and index-tab
LONG64 CFeaFileBase::getTotalFeaLength()
{
	long nRec = m_oFeaHead.nRecords;
	LONG64 tFeaLen;
	if( m_oFeaHead.bIndexTab == 0 ) // no index table
		tFeaLen = (LONG64)(nRec * m_oFeaHead.nElemSize * m_oFeaHead.nFeaDim);
	else
	{
		tFeaLen = (LONG64)(m_pOffset[nRec-1].nOffset + m_pOffset[nRec-1].nFeaLength 
				  - m_pOffset[0].nOffset);
	}

	return tFeaLen;
}

// number of samples (not records) for Var-Len fea-file
long CFeaFileBase::getSampleNum4VarLen()
{
	if( m_oFeaHead.bVarLen )
		return (long)(getTotalFeaLength()/(m_oFeaHead.nElemSize * m_oFeaHead.nFeaDim));
	else
		return getRecordNum();
}

// offset from the file right-beginning
LONG64 CFeaFileBase::getOffsetAtIdx(int idx)
{
	if( idx < 0 || idx > m_oFeaHead.nRecords )
		return (LONG64)(-1);

	LONG64 offset;
	if( m_oFeaHead.bIndexTab == 0 ) // no index table
		offset = (LONG64)(sizeof(FEA_FILE_HEADER) + idx * m_oFeaHead.nElemSize * m_oFeaHead.nFeaDim);
	else
		offset = m_pOffset[idx].nOffset;

	return offset;
}

long CFeaFileBase::getFeaLenAtIdx(int idx)
{
	if( idx < 0 || idx > m_oFeaHead.nRecords )
		return -1;

	ULONG feaLength;
	if( m_oFeaHead.bIndexTab == 0 )
		feaLength = m_oFeaHead.nElemSize * m_oFeaHead.nFeaDim;
	else
		feaLength = m_pOffset[idx].nFeaLength;

	return feaLength;
}

long CFeaFileBase::getCurOuterIndex(int idx)
{
	if( m_pOffset == NULL )
		return -1;

	if( idx >= 0 && idx < m_oFeaHead.nRecords )
		return m_pOffset[idx].nOuterIndex;
	else
		return -1;
}

void CFeaFileBase::dumpHeader2File(FILE* fp /* =stdout */, bool bIndexTab /* =false */)
{
	fprintf(fp, "======================================\n");
	fprintf(fp, " version 0x%x \n", m_oFeaHead.nVersion);
	fprintf(fp, " # records = %d\n", m_oFeaHead.nRecords);
	fprintf(fp, " feature dim = %d (atomic feature dimension)\n", m_oFeaHead.nFeaDim);
	fprintf(fp, " element type = %d (1=char;2=short;3=long;4=float;5=double;6=struct)\n", m_oFeaHead.nElemType);
	fprintf(fp, " element size = %d \n", m_oFeaHead.nElemSize);
	fprintf(fp, " bIndexTab = %d (1=true, 0=false)\n", m_oFeaHead.bIndexTab);
	fprintf(fp, " bVarLen = %d (1=true, 0=false)\n", m_oFeaHead.bVarLen);
	fprintf(fp, " feature name = [%s]\n", m_oFeaHead.szFeaName);
	fprintf(fp, " reserved = [%s]\n", m_oFeaHead.szReserved);
	fprintf(fp, "======================================\n");

	// index table
	if( bIndexTab )
	{
		if( m_oFeaHead.bIndexTab == 1 && m_pOffset != NULL )
		{
			for (int i=0; i<m_oFeaHead.nRecords; i++)
			{
#ifdef _MSC_VER
				fprintf(fp, "index[%d],  offset = %I64d,  length = %ldL,  #outer_index = %d\n", 
					i, m_pOffset[i].nOffset, m_pOffset[i].nFeaLength, m_pOffset[i].nOuterIndex);
#else
				fprintf(fp, "index[%d],  offset = %lld,  length = %ldL,  #outer_index = %d\n", 
					i, (long long)m_pOffset[i].nOffset, m_pOffset[i].nFeaLength, m_pOffset[i].nOuterIndex);
#endif
			}
		}
	}
}

//////////////////////////////////////////////////////////////////////////
CFeaFileReader::CFeaFileReader():m_pAllFeature(NULL),m_pRangeBuffer(NULL),m_oldVarLen(0)
{
}

CFeaFileReader::~CFeaFileReader()
{
	releaseMemory();
}

void CFeaFileReader::releaseMemory()
{
	if(m_pAllFeature != NULL )
	{
		delete [] m_pAllFeature;
		m_pAllFeature = NULL;
	}
}

void CFeaFileReader::openFile(const char* fname)
{
	closeFile();
	releaseMemory();

	m_fpFeaFile = fopen(fname, "rb");
	if( m_fpFeaFile == NULL )
	{
		printf("File %s opened fail!\n", fname);
		exit(-1);
	}

	// read file header into the memory
	size_t readsz = fread(&m_oFeaHead, 1, sizeof(FEA_FILE_HEADER), m_fpFeaFile);
	if( m_oFeaHead.nElemSize <= 0 || readsz != sizeof(FEA_FILE_HEADER) || m_oFeaHead.nElemType <=0 )
	{
		printf("Reading error, Unsupported element format!\n");
		exit(-1);
	}

	// for those with index tab
	if( m_oFeaHead.bIndexTab == 1 && m_oFeaHead.nRecords > 0 )
	{
		m_pOffset = new FEA_INDEX_TAB[m_oFeaHead.nRecords];
		readsz = fread(m_pOffset, sizeof(FEA_INDEX_TAB), m_oFeaHead.nRecords, m_fpFeaFile);
		if( readsz != m_oFeaHead.nRecords )
		{
			printf("Reading error for fea-index-tab!\n");
			exit(-1);
		}

		m_nFileHeadLength = sizeof(FEA_FILE_HEADER) + sizeof(FEA_INDEX_TAB)*m_oFeaHead.nRecords;
	}

	if( m_oFeaHead.bVarLen == 0 ) // allocate for fixed length buffer
		m_pCurFea = new char[m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize];
}

void CFeaFileReader::readAllData()
{
	readAllData(m_pAllFeature);
}

// read all data into an outside buffer
void CFeaFileReader::readAllData(char*& buffer)
{
	// allocate buffer to read
	ULONG allBufSize = (ULONG) getTotalFeaLength();
	buffer = new char[allBufSize];

	// read all data into buffer
	size_t readsize = (size_t)fread(buffer, sizeof(char), allBufSize, m_fpFeaFile);
	if( readsize != allBufSize )
	{
		releaseMemory();
		closeFile();
		delete [] buffer;

		printf("Reading data into buffer error!\n");
		exit(-1);
	}
}

void CFeaFileReader::dumpAll2TxtFile(const char* fname)
{
	FILE* fp = fopen(fname, "wt");
	if( fp == NULL )
	{
		printf("File %s created fail!\n", fname);
		exit(-1);
	}

	// write header to the file
	dumpHeader2File(fp, true);

	if( m_oFeaHead.nElemType >= ELEM_TYPE_STRUCT )
	{
		fprintf(fp, "Unsupported structure data for dumping to text file!\n");
		fclose(fp);
		return;
	}

	fseek(m_fpFeaFile, sizeof(FEA_FILE_HEADER), SEEK_SET);
	if( m_oFeaHead.bIndexTab == 1 )
	{
		m_pOffset = new FEA_INDEX_TAB[m_oFeaHead.nRecords];
		fread(m_pOffset, m_oFeaHead.nRecords, sizeof(FEA_INDEX_TAB), m_fpFeaFile);
	}

	long feaLen, k, num;
	if( m_oFeaHead.nElemType == ELEM_TYPE_FLOAT )
	{
		for(int k = 0; k < m_oFeaHead.nRecords; k++)
		{
			feaLen = getFeaLenAtIdx(k);
			if( feaLen == 0 )
				continue;

			num = feaLen/m_oFeaHead.nElemType;
			if( m_oFeaHead.bVarLen && feaLen != m_oldVarLen )
			{
				if( m_pCurFea )
					delete [] m_pCurFea;
				m_pCurFea = new char [feaLen];
				m_oldVarLen = feaLen;
			}
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);

			float* pf = (float *)m_pCurFea;
			for(int i = 0; i < num; i++)
				fprintf(fp, "%f ", *pf++);
			fprintf(fp, "\n");
		}
	}
	else if( m_oFeaHead.nElemType == ELEM_TYPE_DOUBLE )
	{
		for(int k = 0; k < m_oFeaHead.nRecords; k++)
		{
			feaLen = getFeaLenAtIdx(k);
			if( feaLen == 0 )
				continue;

			num = feaLen/m_oFeaHead.nElemType;
			if( m_oFeaHead.bVarLen && feaLen != m_oldVarLen )
			{
				if( m_pCurFea )
					delete [] m_pCurFea;
				m_pCurFea = new char [feaLen];
				m_oldVarLen = feaLen;
			}
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);

			double* pf = (double *)m_pCurFea;
			for(int i = 0; i < num; i++)
				fprintf(fp, "%lf ", *pf++);
			fprintf(fp, "\n");
		}
	}
	else if( m_oFeaHead.nElemType == ELEM_TYPE_SHORT )
	{
		for(int k = 0; k < m_oFeaHead.nRecords; k++)
		{
			feaLen = getFeaLenAtIdx(k);
			if( feaLen == 0 )
				continue;

			num = feaLen/m_oFeaHead.nElemType;
			if( m_oFeaHead.bVarLen && feaLen != m_oldVarLen )
			{
				if( m_pCurFea )
					delete [] m_pCurFea;
				m_pCurFea = new char [feaLen];
				m_oldVarLen = feaLen;
			}
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);

			short* pf = (short *)m_pCurFea;
			for(int i = 0; i < num; i++)
				fprintf(fp, "%d ", *pf++);
			fprintf(fp, "\n");
		}
	}
	else if( m_oFeaHead.nElemType == ELEM_TYPE_LONG )
	{
		for(int k = 0; k < m_oFeaHead.nRecords; k++)
		{
			feaLen = getFeaLenAtIdx(k);
			if( feaLen == 0 )
				continue;

			num = feaLen/m_oFeaHead.nElemType;
			if( m_oFeaHead.bVarLen && feaLen != m_oldVarLen )
			{
				if( m_pCurFea )
					delete [] m_pCurFea;
				m_pCurFea = new char [feaLen];
				m_oldVarLen = feaLen;
			}
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);

			long* pf = (long *)m_pCurFea;
			for(int i = 0; i < num; i++)
				fprintf(fp, "%d ", *pf++);
			fprintf(fp, "\n");
		}
	}
	else if( m_oFeaHead.nElemType == ELEM_TYPE_CHAR )
	{
		for(k = 0; k < m_oFeaHead.nRecords; k++)
		{
			feaLen = getFeaLenAtIdx(k);
			if( feaLen == 0 )
				continue;

			num = feaLen/m_oFeaHead.nElemType;
			if( m_oFeaHead.bVarLen && feaLen != m_oldVarLen )
			{
				if( m_pCurFea )
					delete [] m_pCurFea;
				m_pCurFea = new char [feaLen];
				m_oldVarLen = feaLen;
			}
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);
			char* pf = (char *)m_pCurFea;
			for(int i = 0; i < num; i++)
				fprintf(fp, "%c ", pf++);
			fprintf(fp, "\n");
		}
	}
	fclose(fp);
}

// FrmIdx is 0-indexed
char* CFeaFileReader::readRecordAt(int iFrmIdx)
{
	if( iFrmIdx < 0 || iFrmIdx >= m_oFeaHead.nRecords )
		return NULL;

	char* pFeaX;
	long oldIndex = m_nCurRecordNo;

	m_nCurRecordNo = iFrmIdx;
	m_nCurOffset = getOffsetAtIdx(iFrmIdx);

	if( m_pAllFeature != NULL ) // all have been loaded into buffer
	{
		// for var-length feature, please call getFeaLenAtIdx() to get the feature length
		long feaLen = getFeaLenAtIdx(iFrmIdx);
		if( feaLen == 0 )
			return NULL;

		pFeaX = (char*)(m_pAllFeature + m_nCurOffset - m_nFileHeadLength);
	}
	else
	{
		// read directly from the FILE
		long feaLen = getFeaLenAtIdx(iFrmIdx);

		// for var-length feature: initial memory buffer
		if( m_oFeaHead.bVarLen )
		{
			if( feaLen == 0 ) // null features
				return NULL;

			if( m_pCurFea != NULL && feaLen != m_oldVarLen )
			{
				delete [] m_pCurFea;
				m_pCurFea = new char[feaLen];
			}
			if( m_pCurFea == NULL )
			{
				m_pCurFea = new char[feaLen];
			}
			m_oldVarLen = feaLen;
		}

		// when just at next position
		if( oldIndex != 0 && iFrmIdx == oldIndex + 1 )
		{
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);
		}
		else
		{
			// others, seek from the file beginning
			fpos_t curpos;
#if defined (__GNUC__) && !defined (__MINGW32__) && !defined (__CYGWIN__)
			curpos.__pos = m_nCurOffset;
#else
			curpos = m_nCurOffset;
#endif
			fsetpos(m_fpFeaFile, &curpos);
			fread(m_pCurFea, feaLen, 1, m_fpFeaFile);
		}
		pFeaX = (char*)m_pCurFea;
	}

	return pFeaX;
}

// get samples from var-length file
char* CFeaFileReader::getNextSample4VarLen(bool bReStart /* =false */)
{
	if( bReStart == true )
	{
		m_nCurRecordNo = 0;

		m_VarCurOffset = 0;
		m_VarCurRecLen = 0;
		m_pVarFea = NULL;
	}

	if(m_VarCurOffset >= m_VarCurRecLen)
	{
		do{
			m_pVarFea = readRecordAt(m_nCurRecordNo);
			m_VarCurRecLen = getFeaLenAtIdx(m_nCurRecordNo++);
			m_VarCurOffset = 0;
		}while( m_VarCurRecLen == 0 );
	}
	if(!m_pVarFea)
		return NULL;
	
	long curOffset = m_VarCurOffset;
	m_VarCurOffset += m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize;

	return	(char *)(m_pVarFea + curOffset);
}

char* CFeaFileReader::readRecordAtRange(int iStIdx, int iEndIdx, int* nCntStatus /* =NULL */ )
{
	if( (iStIdx < 0 || iStIdx >= m_oFeaHead.nRecords)
		|| (iEndIdx < 0 || iEndIdx >= m_oFeaHead.nRecords) )
		return NULL;

	if( iStIdx == iEndIdx )
		return readRecordAt(iStIdx);
	if( iStIdx > iEndIdx )
		std::swap(iStIdx, iEndIdx);

	char* pFeaX;
	long oldIndex = m_nCurRecordNo;

	m_nCurRecordNo = iStIdx;
	m_nCurOffset = getOffsetAtIdx(iStIdx);

	ULONG feaLen = 0;
	for(int i=iStIdx; i<=iEndIdx; i++)
		feaLen += getFeaLenAtIdx(i);
	if( feaLen == 0 )
		return NULL;

	if( nCntStatus != NULL )
		*nCntStatus = feaLen/(m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize);

	if( m_pAllFeature != NULL ) // all have been loaded into buffer
	{
		// for var-length feature, please call getFeaLenAtIdx() to get the feature length
		pFeaX = (char*)(m_pAllFeature + m_nCurOffset - m_nFileHeadLength);
	}
	else
	{
		// read directly from the FILE
		if( feaLen != m_oldVarLen )
		{
			if( m_pRangeBuffer )
				delete [] m_pRangeBuffer;
			m_pRangeBuffer = new char[feaLen];
			m_oldVarLen = feaLen;
		}

		// when just at next position
		if( oldIndex != 0 && iStIdx == oldIndex + 1 )
		{
			fread(m_pRangeBuffer, feaLen, 1, m_fpFeaFile);
		}
		else
		{
			// others, seek from the file beginning
			fpos_t curpos;
#if defined (__GNUC__) && !defined (__MINGW32__) && !defined (__CYGWIN__)
			curpos.__pos = m_nCurOffset;
#else
			curpos = m_nCurOffset;
#endif			
			fsetpos(m_fpFeaFile, &curpos);
			fread(m_pRangeBuffer, feaLen, 1, m_fpFeaFile);
		}
		pFeaX = (char*)m_pRangeBuffer;
	}

	return pFeaX;
}

//////////////////////////////////////////////////////////////////////////
CFeaFileWriter::CFeaFileWriter(int bufferSize /* =16 */, bool bFilling /* =false */)
{
	m_nBufSize = bufferSize; // initially in MB
	m_pFeaBuffer = NULL;
	m_nCurBufRecord = 0;
	m_nMaxBufRecords = 0;
	m_nCurBufOffset = 0;

	m_bFilling = bFilling;
}

CFeaFileWriter::~CFeaFileWriter()
{
	releaseMemory();
}

void CFeaFileWriter::releaseMemory()
{
	if( m_pFeaBuffer != NULL )
	{
		delete [] m_pFeaBuffer;
		m_pFeaBuffer = NULL;
	}
}

void CFeaFileWriter::closeFile()
{
	if( m_fpFeaFile != NULL )
	{
		if( m_nCurBufOffset != 0 )
			flush2Disk();

		// updated write index-table
		if( m_oFeaHead.bIndexTab && m_pOffset != NULL )
		{
			// fseek(m_fpFeaFile, sizeof(FEA_FILE_HEADER), SEEK_SET);
			LONG64 curpos = (LONG64)sizeof(FEA_FILE_HEADER);
			
			fpos_t thepos_t;
#if defined (__GNUC__) && !defined (__MINGW32__) && !defined (__CYGWIN__)			
			thepos_t.__pos = curpos;
#else
			thepos_t = curpos;
#endif			
			fsetpos(m_fpFeaFile, &thepos_t);
			fwrite(m_pOffset, sizeof(FEA_INDEX_TAB), m_oFeaHead.nRecords, m_fpFeaFile);
		}
		fclose(m_fpFeaFile);
		m_fpFeaFile = NULL;
	}
}

void CFeaFileWriter::openFile(const char* fname)
{
	closeFile();
	releaseMemory();

	if( m_bFilling == false )
	{
		m_fpFeaFile = fopen(fname, "wb");
		if( m_fpFeaFile == NULL )
		{
			printf("File %s created fail!\n", fname);
			exit(-1);
		}
	}
	else
	{
		FILE* fp = fopen(fname, "rb");
		if( fp == NULL ) // file does not exist
		{
			m_fpFeaFile = fopen(fname, "wb");
			m_bFileExist = false;
		}
		else // file exist
		{
			fclose(fp);
			m_bFileExist = true;
			m_fpFeaFile = fopen(fname, "r+b");

			// read existed file header, and check the status
			fseek(m_fpFeaFile, 0L, SEEK_SET);
			fread(&m_oFeaHead, 1, sizeof(FEA_FILE_HEADER), m_fpFeaFile);
			if( m_oFeaHead.bVarLen || m_oFeaHead.bIndexTab )
			{
				printf("Error! Cannot handle var-length Fea-File in filling mode!\n");
				exit(0);
			}

			// allocate memory for all data
			m_nBufSize = m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize * m_oFeaHead.nRecords;
			m_nCurBufOffset = m_nBufSize;
			m_pFeaBuffer = new char[m_nBufSize];
			fseek(m_fpFeaFile, sizeof(FEA_FILE_HEADER), SEEK_SET);
			size_t readsize = (size_t)fread(m_pFeaBuffer, 1, m_nBufSize, m_fpFeaFile);
			if( readsize != m_nBufSize )
			{
				releaseMemory();
				closeFile();

				printf("Exist file was bad formated!\n");
				exit(-1);
			}
		}
	}
}

// Fill an row
void CFeaFileWriter::fillElemAt(void* pFea, int nRow)
{
	if( m_bFilling == false || m_pFeaBuffer == NULL )
	{
		printf("FillElemAt does not support current file open mode!\n");
		exit(-1);
	}

	long feaLength = m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize;
	long offSet = nRow * feaLength;
	memcpy(m_pFeaBuffer + offSet, pFea, feaLength);
}

void CFeaFileWriter::fillElemAt(void* pFea, int nRow, int nDim)
{
	if( m_bFilling == false || m_pFeaBuffer == NULL )
	{
		printf("FillElemAt does not support current file open mode!\n");
		exit(-1);
	}

	long offSet = (m_oFeaHead.nFeaDim*nRow + nDim) * m_oFeaHead.nElemSize;
	memcpy(m_pFeaBuffer + offSet, pFea, m_oFeaHead.nElemSize);
}

void CFeaFileWriter::setFileHeader(const FEA_FILE_HEADER& feaHeader)
{
	m_oFeaHead = feaHeader;
	if( strlen(m_oFeaHead.szReserved) < 2 )
	{
		strcpy(m_oFeaHead.szReserved, "(C)CopyLeft 2006 by jianguo.li@intel.com");
	}

	if( m_bFilling && m_oFeaHead.bVarLen )
	{
		printf("Error! Cannot handle var-length Fea-File in filling mode!\n");
		exit(0);
	}
	
	if( !m_bFilling )
	{
		fseek(m_fpFeaFile, 0L, SEEK_SET);
		fwrite(&m_oFeaHead, sizeof(FEA_FILE_HEADER), 1, m_fpFeaFile);
		if( m_oFeaHead.bVarLen == 0 )
		{
			m_nMaxBufRecords = (m_nBufSize*1024*1024)/(m_oFeaHead.nFeaDim*m_oFeaHead.nElemSize);
			if( m_nMaxBufRecords > m_oFeaHead.nRecords )
				m_nMaxBufRecords = m_oFeaHead.nRecords;

			m_nBufSize = m_nMaxBufRecords * m_oFeaHead.nFeaDim*m_oFeaHead.nElemSize;
			m_pFeaBuffer = new char[m_nBufSize];
		}
		else
		{
			m_nBufSize = m_nBufSize * 1024*1024;
			m_pFeaBuffer = new char[m_nBufSize];
		}

		if( m_oFeaHead.bIndexTab )
		{			
			m_pOffset = new FEA_INDEX_TAB[m_oFeaHead.nRecords];
			m_nFileHeadLength = sizeof(FEA_FILE_HEADER) + sizeof(FEA_INDEX_TAB)*m_oFeaHead.nRecords;

			// write NULL to feature offset index table
			memset(m_pOffset, 0, sizeof(FEA_INDEX_TAB) * m_oFeaHead.nRecords);
			fwrite(m_pOffset, sizeof(FEA_INDEX_TAB), m_oFeaHead.nRecords, m_fpFeaFile);			
		}
	}
	else
	{
		m_oFeaHead.bIndexTab = 0;
		fseek(m_fpFeaFile, 0L, SEEK_SET);
		fwrite(&m_oFeaHead, sizeof(FEA_FILE_HEADER), 1, m_fpFeaFile);

		// allocate a buffer for first writing
		releaseMemory();
		m_nBufSize = m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize * m_oFeaHead.nRecords;
		m_nCurBufOffset = m_nBufSize;
		m_pFeaBuffer = new char[m_nBufSize];
		memset(m_pFeaBuffer, 0, m_nBufSize);
	}
	// writing start after file header
	m_nCurOffset = (LONG64)m_nFileHeadLength;
}

void CFeaFileWriter::writeRecordAt(void* pFea, long nOuterIdx, long feaLength /* =0 */)
{
	// for fixed length feature
	if( m_oFeaHead.bVarLen == 0 && feaLength == 0 )
		feaLength = m_oFeaHead.nFeaDim * m_oFeaHead.nElemSize;

	// when has index table
	if( m_oFeaHead.bIndexTab )
	{
		m_pOffset[ m_nCurRecordNo ].nOffset = m_nCurOffset; // current file offset
		if( m_oFeaHead.bVarLen ) // variant length
			m_pOffset[ m_nCurRecordNo ].nFeaLength = feaLength;
		else // fixed length
			m_pOffset[ m_nCurRecordNo ].nFeaLength = m_oFeaHead.nElemSize*m_oFeaHead.nFeaDim;
		m_pOffset[ m_nCurRecordNo ].nOuterIndex = nOuterIdx;
	}

	if( pFea == NULL && feaLength == 0 )
	{
		// update the global FILE record info
		m_nCurRecordNo ++;
		return ;
	}

	// when the buffer is full
	if( m_nCurBufOffset + feaLength > m_nBufSize )
		flush2Disk();

	// write current feature to the buffer
	memcpy(m_pFeaBuffer + m_nCurBufOffset, pFea, feaLength);

	// update the global FILE offset info
	m_nCurRecordNo ++;
	m_nCurOffset += (LONG64)feaLength;

	// update the local buffer info
	m_nCurBufRecord ++;
	m_nCurBufOffset += feaLength;
}

void CFeaFileWriter::flush2Disk()
{
	if( m_bFilling ) // for filling model
	{
		fseek(m_fpFeaFile, sizeof(FEA_FILE_HEADER), SEEK_SET);
		fwrite(m_pFeaBuffer, m_nCurBufOffset, 1, m_fpFeaFile);
	}
	else
		fwrite(m_pFeaBuffer, m_nCurBufOffset, 1, m_fpFeaFile);
		
	m_nCurBufOffset = 0;
	m_nCurBufRecord = 0;
}
