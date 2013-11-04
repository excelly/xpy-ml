//----------------------------------------------------------------------
//	File:		kmlsample.cpp
//	Programmer:	David Mount
//	Last modified:	05/14/04
//	Description:	Sample program for kmeans
//----------------------------------------------------------------------

#include <cstdlib>			// C standard includes
#include <iostream>			// C++ I/O
#include <string>			// C++ strings
#include "KMlocal.h"			// k-means algorithms

#include "cv.h"
#include "FeaFile.h"

using namespace std;			// make std:: available

//----------------------------------------------------------------------
// kmain
//
// This is a simple sample program for the kmeans local search on each
// of the four methods.  After compiling, it can be run as follows.
// 
//   kmain [-d dim] [-k nctrs] [-max mpts] [-df data] [-s stages]
//
// where
//	dim		Dimension of the space (default = 2)
//	nctrs		The number of centers (default = 4)
//	mpts		Maximum number of data points (default = 1000)
//	data		File containing data points
//			(If omitted mpts points are randomly generated.)
//	stages		Number of stages to run (default = 100)
//
// Results are sent to the standard output.
//----------------------------------------------------------------------

//----------------------------------------------------------------------
//  Global entry points
//----------------------------------------------------------------------
void getArgs(int argc, char **argv);	// get command-line arguments

void printSummary(			// print final summary
				  const KMlocal&	theAlg,		// the algorithm
				  const KMdata&	dataPts,	// the points
				  KMfilterCenters&	ctrs);		// the centers

bool readPt(				// read a point
			istream&		in,		// input stream
			KMpoint&		p);		// point (returned)

void printPt(				// print a point
			 ostream&		out,		// output stream
			 const KMpoint&	p);		// the point

//----------------------------------------------------------------------
//  Global parameters (some are set in getArgs())
//----------------------------------------------------------------------

int	k		= 4;		// number of centers
int	dim		= 2;		// dimension
int	maxPts		= 100;		// max number of data points
int	stages		= 100;		// number of stages
int binary	= 0;
istream* dataIn		= NULL;		// input data stream
std::string infname;

//----------------------------------------------------------------------
//  Termination conditions
//	These are explained in the file KMterm.h and KMlocal.h.  Unless
//	you are into fine tuning, don't worry about changing these.
//----------------------------------------------------------------------
KMterm	term(100, 0, 0, 0,		// run for 100 stages
			 0.10,			// min consec RDL
			 0.10,			// min accum RDL
			 3,				// max run stages
			 0.50,			// init. prob. of acceptance
			 10,			// temp. run length
			 0.95);			// temp. reduction factor

//----------------------------------------------------------------------
//  Main program
//----------------------------------------------------------------------
int main(int argc, char **argv)
{
	getArgs(argc, argv);			// read command-line arguments
	term.setAbsMaxTotStage(stages);		// set number of stages	

	KMdata dataPts(dim, maxPts);		// allocate data storage
	printf("Start Loading!\n");

	int nPts = 0;				// actual number of points
	// generate points
	if( !binary )
	{
		if (dataIn != NULL) 
		{			// read points from file
			while (nPts < maxPts && readPt(*dataIn, dataPts[nPts])) 
				nPts++;
		}
		else 
		{					// generate points randomly
			nPts = maxPts;
			kmClusGaussPts(dataPts.getPts(), nPts, dim, k);
		}
	}
	else
	{
		CFeaFileReader feaReader;
		feaReader.openFile(infname.c_str() );
		nPts = 0;
		char* pBuf = feaReader.getNextSample4VarLen(true);		
		for(; ;)
		{
			if( nPts >= maxPts )
				break;
			if( !pBuf )
				break;

			KMpoint pPtFea = (dataPts[nPts]);
			float *pF = (float *)pBuf;
			for (int d = 0; d < dim; d++) 
			{
				pPtFea[d] = pF[d];
			}
			nPts++;
			pBuf = feaReader.getNextSample4VarLen();
		}
	}
	printf("Load OK!\n");

	dataPts.setNPts(nPts);			// set actual number of pts
	dataPts.buildKcTree();			// build filtering structure

	KMfilterCenters ctrs(k, dataPts);		// allocate centers

	__int64 t1, t2;
	t1 = cvGetTickCount();
	cout << "\nExecuting Clustering Algorithm: Hybrid\n";
	KMlocalHybrid kmHybrid(ctrs, term);		// Hybrid heuristic
	ctrs = kmHybrid.execute();
	t2 = cvGetTickCount() - t1;

	printSummary(kmHybrid, dataPts, ctrs);

	printf( "Elapsed time = %10.2f (ms)\n", t2/(cvGetTickFrequency()*1000) );

	kmExit(0);
}

//----------------------------------------------------------------------
//  getArgs - get command line arguments
//----------------------------------------------------------------------

void getArgs(int argc, char **argv)
{
	static ifstream dataStream;			// data file stream
	static ifstream queryStream;		// query file stream

	if (argc <= 1) {				// no arguments
		cerr << "Usage:\n\n"
			<< "   kmain [-d dim] [-k nctrs] [-max mpts] [-df data] [-s stages]\n"
			<< "OR \nkmain [-d dim] [-k nctrs] [-max mpts] [-df data] [-s stages] [-b]\n"
			<< "\n"
			<< " where\n"
			<< "    dim             Dimension of the space (default = 2)\n"
			<< "    nctrs           The number of centers (default = 4)\n"
			<< "    mpts            Maximum number of data points (default = 1000)\n"
			<< "    data            File containing data points\n"
			<< "                    (If omitted mpts points are randomly generated.)\n"
			<< "    stages          Number of stages to run (default = 100)\n"
			<< "    b          		binary fea-file\n"
			<< "\n"
			<< " Results are sent to kmean.log.\n"
			<< "\n";
		kmExit(0);
	}
	int i = 1;
	while (i < argc) 
	{				// read arguments
		if (!strcmp(argv[i], "-d")) {		// -d option
			dim = atoi(argv[++i]);
		}
		else if (!strcmp(argv[i], "-k")) {	// -k option
			k = atoi(argv[++i]);
		}
		else if (!strcmp(argv[i], "-max")) {	// -max option
			maxPts = atoi(argv[++i]);
		}
		else if (!strcmp(argv[i], "-df")) 
		{	
			// -df option
			infname = argv[i+1];
			dataStream.open(argv[++i], ios::in);
			if (!dataStream) {
				cerr << "Cannot open data file\n";
				kmExit(1);
			}
			dataIn = &dataStream;
		}
		else if (!strcmp(argv[i], "-s")) {	// -s option
			stages = atoi(argv[++i]);
		}
		else if (!strcmp(argv[i], "-b")) {	// -s option
			binary = 1;
		}
		//else 
		//{					// illegal syntax
		//	cerr << "Unrecognized option.\n";
		//	kmExit(1);
		//}
		i++;
	}
}

//----------------------------------------------------------------------
//  Reading/Printing utilities
//	readPt - read a point from input stream into data storage
//		at position i.  Returns false on error or EOF.
//	printPt - prints a points to output file
//----------------------------------------------------------------------
bool readPt(istream& in, KMpoint& p)
{
	for (int d = 0; d < dim; d++) {
		if(!(in >> p[d])) return false;
	}
	return true;
}

void printPt(ostream& out, const KMpoint& p)
{
	out << "(" << p[0];
	for (int i = 1; i < dim; i++) {
		out << ", " << p[i];
	}
	out << ")\n";
}

//------------------------------------------------------------------------
//  Print summary of execution
//------------------------------------------------------------------------
void printSummary(const KMlocal&		theAlg,		// the algorithm
				  const KMdata&		dataPts,	// the points
				  KMfilterCenters&		ctrs)		// the centers
{
	double dbval, xbval;
	dbval = ctrs.getDBIndex();
	xbval = ctrs.getXBIndex();

	FILE* logfp = fopen("kmean.log", "wt");
	fprintf(logfp, "Number of stages: %d\n", theAlg.getTotalStages());
	fprintf(logfp, "Average distortion: %g\n", ctrs.getDist(false)/double(ctrs.getNPts()));
	fprintf(logfp, "DB-index: %g\n", dbval);
	fprintf(logfp, "XB-index: %g\n", xbval);	

	cout << "Number of stages: " << theAlg.getTotalStages() << "\n";
	cout << "Average distortion: " <<
		ctrs.getDist(false)/double(ctrs.getNPts()) << "\n";
	cout << "DB-index = " << dbval << "\n";
	cout << "XB-index = " << xbval << "\n";

	KMctrIdxArray closeCtr = new KMctrIdx[dataPts.getNPts()];
	double* sqDist = new double[dataPts.getNPts()];
	ctrs.getAssignments(closeCtr, sqDist);

	int*  hist = new int[ctrs.getK()];
	memset(hist, 0, sizeof(int) * ctrs.getK() );
	for(int i=0; i < dataPts.getNPts(); i++ )
	{
		int k = closeCtr[i];
		hist[k] ++;
	}

	KMpoint kpt;
	for(int i=0; i< ctrs.getK(); i++ )
	{
		fprintf(logfp, "%3d-th, #%5d ", i, hist[i]);

		// print final center points
		kpt = ctrs[i];
		fprintf(logfp, " [");
		for (int j = 0; j < ctrs.getDim(); j++) 
		{
			fprintf(logfp, "%7g ", kpt[j]);
		}
		fprintf(logfp, " ]\n");
	}
	fclose(logfp);

	// write to fea-file
	CFeaFileWriter theFeaWriter;
	char saveName[256];
	sprintf(saveName, "kmain_%s", infname.c_str() );
	theFeaWriter.openFile(saveName);

	FEA_FILE_HEADER feaHeader;
	feaHeader.nVersion = FEA_FILE_VERSION;
	feaHeader.nRecords = ctrs.getK();
	feaHeader.nFeaDim = ctrs.getDim();
	feaHeader.nElemType = ELEM_TYPE_FLOAT;
	feaHeader.nElemSize = sizeof(float);
	feaHeader.bIndexTab = 0;
	feaHeader.bVarLen = 0;
	sprintf(feaHeader.szFeaName, "kmean codebook");
	theFeaWriter.setFileHeader(feaHeader);

	float* pFea = new float[ctrs.getDim()];
	for(int i=0; i< ctrs.getK(); i++ )
	{
		// save final center points
		kpt = ctrs[i];
		for (int j = 0; j < ctrs.getDim(); j++) 
			pFea[j] = kpt[j];

		theFeaWriter.writeRecordAt(pFea, i);
	}
	theFeaWriter.flush2Disk();
	theFeaWriter.closeFile();
	theFeaWriter.releaseMemory();
	delete [] pFea;

	delete [] closeCtr;
	delete [] sqDist;
	delete [] hist;
}
