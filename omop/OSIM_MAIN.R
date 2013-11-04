                                        # The source of each occurrence is tagged in the A_TYPE field.
                                        # 0: background
                                        # 1: indication
                                        # 2: outcome of drug
                                        # 3: outcome of indication

                                        #*************************************************************************
                                        #
                                        #	Observational Medical Outcomes Partnership
                                        #
                                        #	Procedure for constructing simulated observational datasets
                                        #
                                        #	 Original Pseudo Code Design: Patrick Ryan, GlaxoSmithKline
                                        #	 Written in R: Rich Murray, ProSanos Corporation
                                        #	Last modified: 12 August 2009
                                        #
                                        #
                                        #
                                        #	©2009 Foundation for the National Institutes of Health
                                        #
                                        #	(c) 2009 Foundation for the National Institutes of Health (FNIH).
                                        #
                                        #	Licensed under the Apache License, Version 2.0 (the "License"); you may not
                                        #	use this file except in compliance with the License. You may obtain a copy
                                        #	of the License at http://omop.fnih.org/publiclicense.
                                        #
                                        #	Unless required by applicable law or agreed to in writing, software
                                        #	distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
                                        #	WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. Any
                                        #	redistributions of this work or any derivative work or modification based on
                                        #	this work should be accompanied by the following source attribution: "This
                                        #	work is based on work by the Observational Medical Outcomes Partnership
                                        #	(OMOP) and used under license from the FNIH at
                                        #	http://omop.fnih.org/publiclicense.
                                        #
                                        #	Any scientific publication that is based on this work should include a
                                        #	reference to http://omop.fnih.org.
                                        #
                                        #
                                        #	DESCRIPTION:
                                        #	To accommodate the efficient and timely generation of a large number of simulated 
                                        #	records using a variety of high performance and lower-end platforms, the program 
                                        #	has been designed for both local and distributed execution modes.  In local 
                                        #	execution mode, the Simulation Attribute Tables that control the characteristics 
                                        #	of the Simulated Persons are generated in the same run as the Simulated Persons.  
                                        #	In a distributed mode run, the Simulation Attribute Tables are generated first, 
                                        #	in an initial execution.  These Simulation Attribute Tables are used as input to 
                                        #	multiple, distributed executions of OSIM to generated Simulated Persons.  Since 
                                        #	the distributed Simulated Person Files were generated using the same input Tables, 
                                        #	the files can be concatenated into one large Simulated Person file at the 
                                        #	conclusion of the distributed runs.  
                                        #
                                        #	To allow the simulated dataset to approximate characteristics of real 
                                        #	observational data, preliminary analyses were conducted on an administrative 
                                        #	claims database.  Descriptive statistics were calculated to estimate the 
                                        #	categories and probability distributions parameters for:
                                        #	•	Year of Birth
                                        #	•	Gender
                                        #	•	Race
                                        #	•	Observation period duration
                                        #	•	Prevalence rate of drug use
                                        #	•	Length of drug exposure
                                        #	•	Number of periods of exposure
                                        #	•	Prevalence rate of conditions
                                        #	•	Number of condition occurrences
                                        #
                                        #	Where data were not available, domain categories and probability distributions 
                                        #	were invented based on past experience.  These attributes include:
                                        #	•	Attributable risk of drug exposure from age
                                        #	•	Attributable risk of drug exposure from gender
                                        #	•	Attributable risk of drug exposure from race
                                        #	•	Attributable risk of drug exposure from ‘confounder’
                                        #	•	Sensitivity of data capture for drug exposure
                                        #	•	Specificity of data capture for drug exposure
                                        #	•	Proportion of exposure with prior indication
                                        #	•	Number of drugs per indication
                                        #	•	Attributable risk of condition from age
                                        #	•	Attributable risk of condition from gender
                                        #	•	Attributable risk of condition from race
                                        #	•	Attributable risk of condition from ‘confounder’
                                        #	•	Sensitivity of data capture for condition
                                        #	•	Specificity of data capture for condition
                                        #
                                        #	These probability distributions, which are described in detail in the Data 
                                        #	Dictionary for the Observational Medical Dataset Simulator, are input to OSIM 
                                        #	and are used to generate the simulated Attribute Tables and Persons.
                                        #
                                        #------------------------------------------------------------------------------
                                        #	MODIFICATION LOG
                                        #------------------------------------------------------------------------------
                                        #	22 Jul 2009 - r murray 	Original Version 1.0
                                        #	12 Aug 2009 - r murray 	Version 1.1 Outcome enhancements
                                        #	14 Aug 2009 - r murray 	Version 1.1.1 - added alphanumeric edit of 
                                        #							fileDistNumber execution parameter
                                        #

                                        #
                                        #------------------------------------------------------------------------------
                                        #	FILENAME CONSTANTS
                                        #------------------------------------------------------------------------------

                                        #
                                        #	Simulation Files
                                        #
OSIM.CONDITIONS.FILENAME <- "OSIM_CONDITIONS"
OSIM.DRUGS.FILENAME <- "OSIM_DRUGS"
OSIM.INDICATIONS.FILENAME <- "OSIM_INDICATIONS"
OSIM.DRUGOUTCOME.FILENAME <- "OSIM_DRUG_OUTCOMES"
OSIM.INDOUTCOME.FILENAME <- "OSIM_INDICATION_OUTCOMES"

OSIM.DISTRIBUTION.FILENAME <- "OSIM_DISTRIBUTIONS"
OSIM.INPUT.PARMS.FILENAME <- "OSIM_execParms"
OSIM.INPUT.DISTRIBUTION.FILENAME <- "OSIM_distParms"

OSIM.RUNLOG.FILENAME <- "OSIM_DOCUMENTATION"

                                        #
                                        #	CDM Format simulated output files
                                        #
OSIM.TABLE.PATH <- paste(getwd(),"/",sep="")
OSIM.PERSONS.FILENAME <- "OSIM_PERSON"
OSIM.OBSERVATIONS.FILENAME <- "OSIM_OBSERVATION_PERIOD"
OSIM.DRUGEXPOSURE.FILENAME <- "OSIM_DRUG_EXPOSURE"
OSIM.CONDITIONOCCURRENCE.FILENAME <- "OSIM_CONDITION_OCCURRENCE"
                                        #
                                        #	CDM Date Format
                                        #
OSIM.CDM.DATE.FORMAT <- "%Y-%m-%d"	# ISO 8601
                                        #
                                        #	CDM ID CODES
                                        #
OSIM.CDM.GENDER.CODES <- factor(c("Male" = 8507, "Female" = 8532))
OSIM.CDM.RACE.CODES <- factor(c("White" = 8527, "Non-white" = 9178))
OSIM.CDM.STATUS.CODES <- factor(c("active" = 9181, "deceased" = 9176))

                                        #------------------------------------------------------------------------------
                                        #	Vector of valid distribution names (DistName in the the input distribution file)
                                        #------------------------------------------------------------------------------
VALID.DISTRIBUTIONS <- 
  c("PersonAge",
    "PersonAgeRecorded",
    "PersonGender",
    "PersonGenderRecorded",
    "PersonRace",
    "PersonRaceRecorded",
    "PersonConfounder",
    "PersonAgeAtDeath",
    "ObservationPeriod",
    "CondBaselinePrevalence",
    "CondAttrRiskAge",
    "CondAttrRiskGender",
    "CondAttrRiskRace",
    "CondConfounderRisk",
    "CondSensitivity",
    "CondSpecificity",
    "CondOccurrence",
    "DrugBaselinePrevalence",
    "DrugAttrRiskAge",
    "DrugAttrRiskGender",
    "DrugAttrRiskRace",
    "DrugConfounderRisk",
    "DrugSensitivity",
    "DrugSpecificity",       
    "DrugExposureLength",
    "DrugNumExposures",
    "DrugPriorIndication",   
    "DrugsPerIndication",
    "IndOutcomeAttrRisk",
    "IndStartDate",
    "DrugOutcomeRiskType",
    "DrugOutcomeConstantRateOnset",
    "DrugOutcomeConstantRiskOnset",
    "DrugOutcomeConstantRateAttrRisk",
    "DrugOutcomeConstantRiskAttrRisk")

                                        #------------------------------------------------------------------------------
                                        #	CONTROL CONSTANTS
                                        #------------------------------------------------------------------------------
OSIM.DEBUG.MODE <- FALSE
MAX.DATAFRAME.SIZE <- 1000000
OSIM.VALIDATION.SEED <- 31

                                        #------------------------------------------------------------------------------
                                        #	GLOBAL VARIABLES
                                        #------------------------------------------------------------------------------
masterDistributionTable <- ""
execParmsTable <- ""
osim.runlog <- NA
osim.table.path <- ""
indicationCount <- 0

                                        #------------------------------------------------------------------------------
                                        #	EXECUTION PARAMETERS
                                        #------------------------------------------------------------------------------
fileModifier <- ""
fileDistNumber <- ""
simName <- ""
simDescription <- ""
personCount <- 0
personStartID <- 0
drugCount <- 0
conditionCount <- 0
minDatabaseDate <- 0
maxDatabaseDate <- 0
fileHeader <- TRUE
createSimTables <- FALSE
createSimPersons <- FALSE
validationMode <- FALSE

                                        #------------------------------------------------------------------------------
                                        #	FUNCTIONS
                                        #------------------------------------------------------------------------------
                                        #
                                        #------------------------------------------------------------------------------
                                        #	MultiIndex
                                        #
                                        #	Calls rmultinom to return an n x size(prob) matrix of 
                                        #	selected probabilities.
                                        #	Translates the matrix to an n size vector of indexes.
                                        #
                                        #	It is called by the multinomial Multi.
                                        #	It is used directly if the chosen multinomial is needed 
                                        #	by other following columns (generally for a secondary distribution) 
                                        #	in the dataframe.
                                        #
                                        #	n - size of index vector to return
                                        #	pi - vector of probabilities (generally sum to 1.0)
                                        #
MultiIndex <- function(n, pi) {
  x <- rmultinom(n, 1, prob=pi)
  x <- (which(x == 1) - 1) %% length(pi) + 1 
}
                                        #------------------------------------------------------------------------------
                                        #	Multi
                                        #
                                        #	Calls MultiIndec to return an n size vector of indexes
                                        #	Translates the n sized index vector into an n sized vector of values
                                        #
                                        #	n - size of value vector to return
                                        #	xi - vector of values associated with pi probabilities
                                        #	pi - vector of probabilities (generally sum to 1.0)
                                        #
Multi <- function(n, xi, pi) {
  x <- MultiIndex(n, pi)
  x <- xi[x]
}
                                        #------------------------------------------------------------------------------
                                        #	Norm
                                        #
                                        #	Truncated normal distribution
                                        #	Recursively calls Norm to generate a size n vector of 
                                        #	bounded normally distributed values.
                                        #
                                        #	Careful not to take the boundaries too far away on the same
                                        #	side of the mean.
                                        #
                                        #	n - size of value vector to return
                                        #	mu - mean
                                        #	s2 - Standard Deviation
                                        #	L - Lower limit
                                        #	U - Upper limit
                                        #
Norm <- function(n, mu, s2, L, U) {
  if (length(n) > 1) {n <- length(n) }
  x <- rep(NA,n)
  y <- which(! is.na(mu))
  x[y] <- rnorm(length(x[y]), mean = mu[y], sd = s2[y])
  y <- which(x<L|x>U)
  if (length(y) > 0) { x[y] <- Norm(length(y),mu[y],s2[y],L[y],U[y])	}
  return(x)
}

                                        #------------------------------------------------------------------------------
                                        #	secondaryDistribution
                                        #
                                        #	Applies secondary distribution for the selected primary distribution
                                        #
                                        #	Additional rules can be added to this function
                                        #
                                        #	x - index of distribution rule in data.frame, Dist
                                        #	Dist - Distribution data frame
                                        #
secondaryDistribution <- function(DF, Col=1, Dist, CatValue="", BPCol=1, 
                                  ContValue=NA, Duration=0, ResultType="continuous") {
  n <- nrow(DF)
                                        #	Use Name or column number
  if ( length(which(names(DF)==Col)) > 0 ) { Col <- which(names(DF)==Col) }
  if ( length(which(names(DF)==BPCol)) > 0 ) { BPCol <- which(names(DF)==BPCol) }

  res <- vector("numeric",n)
  x <- DF[,Col]
  if (! is.numeric(x[1])) {
    x <- match(x,Dist$Category,NA)
  }
  res <-
    ifelse( ( as.vector(Dist$Rule)[x] == "norm" ),
           ifelse( (rep(ResultType,n) == "discrete") ,
                  round(Norm(length(x), Dist$Mean[x], Dist$StDev[x], Dist$Lower[x], Dist$Upper[x])),
                  Norm(length(x), Dist$Mean[x], Dist$StDev[x], Dist$Lower[x], Dist$Upper[x])),
           ifelse( ( as.vector(Dist$Rule)[x] == "unif" ),
                  ifelse( (rep(ResultType,n) == "discrete") ,
                         round(suppressWarnings(runif(n ,Dist$Lower[x]-0.5, Dist$Upper[x]+0.499999999999))),
                         suppressWarnings(runif(n ,Dist$Lower[x], Dist$Upper[x]))),
                  ifelse( ( as.vector(Dist$Rule)[x] == "duration" ),
                         suppressWarnings(runif(n ,0, Duration)) *
                         ifelse( (is.na(Dist$Factor[x]) ), 1, Dist$Factor[x] ),
                         ifelse( ( as.vector(Dist$Rule)[x] == "const" ),
                                Dist$Const[x],
                                ifelse( ( as.vector(Dist$Rule)[x] == "cat" ),
                                       ifelse ( ( ( CatValue=="" ) | CatValue[1]==Dist$CatValue[x] ),
                                               suppressWarnings(runif(n ,Dist$Lower[x], Dist$Upper[x])) *
                                               ifelse( (Dist$xBP[x]!="y") , 1, DF[,BPCol] ),
                                               0 ),
                                       ifelse( ( as.vector(Dist$Rule)[x] == "cont" ),
                                              ifelse( (is.na(Dist$minCut[x]) & is.na(Dist$maxCut[x])), ContValue[1], 1) * 
                                              ifelse( (is.na(Dist$Factor[x]) ), 1, Dist$Factor[x] ) *
                                              ifelse( (is.na(Dist$minCut[x]) ), 1, ifelse(ContValue[1] >= Dist$minCut[x],1,0) ) *
                                              ifelse( (is.na(Dist$maxCut[x]) ), 1, ifelse(ContValue[1] <= Dist$maxCut[x],1,0) ) *
                                              ifelse( (Dist$xBP[x]!="y"), 1, DF[,BPCol] ),
                                              ifelse( ( as.vector(Dist$Rule)[x] == "omit" ),
                                                     NA,
                                                     NA
                                                     )))))))
  res
}

                                        #------------------------------------------------------------------------------
                                        #	getParameter
                                        #
                                        #	Returns value associated with parmName in the parmTable 
                                        #	data frame loaded from a name=value parameter file.
                                        #
                                        #	parmName - Name of parm to select from Name = Value pairs
                                        #	parmTable - dataframe loaded from Name = Value parameter file
                                        #
getParameter <- function(parmName,parmTable) {
  parmIndex <- as.numeric(which(parmTable$Name == parmName))
  parmValue <- as.character(parmTable$Value[parmIndex])
  x <- NA
  if (length(parmValue) > 0) {
    parmValue <- parmValue[length(parmValue)]
    logMessage(paste(parmName, "=", parmValue, sep=" "))
    if (grepl("^true$",parmValue,ignore.case=TRUE)) {
      x <- TRUE
    } else if (grepl("^false$",parmValue,ignore.case=TRUE)) {
      x <- FALSE
    } else if (grepl("^[0-9.,]+$",parmValue)) {
      x <- as.numeric(gsub(",","",parmValue))
    } else {
      x <- parmValue
    }
  }
  x
}

                                        #------------------------------------------------------------------------------
                                        #	checkParameter
                                        #
                                        #	Calls getParameter to select associated value than
                                        #	performs range edits.
                                        #	If no value is returned by getParameter, the defaultValue
                                        #	is used.
                                        #	If the value is out of allowable range, an error is raised
                                        #	and execution is halted.
                                        #
                                        #	parmName - Name of parm to select from Name = Value pairs
                                        #	parmTable - dataframe loaded from Name = Value parameter file
                                        #	L - Minimum allowed value
                                        #	U - Maximum allowed value
                                        #	defaultValue - value to return in parmValue is not in parmTable
                                        #
checkParameter <- function(parmName,parmTable,L,U,defaultValue) {
  parmValue <- getParameter(parmName, parmTable) [1]
  if (is.na(parmValue[1])) {
    logMessage(paste(parmName, "=", defaultValue, "(default)", sep=" "))
    parmValue <- defaultValue
  } else {
    if (parmValue < L || parmValue > U) {
      stop(paste("Execution parameter (", parmName,"=",parmValue, ") is out of range.", sep=""))
    }
  }
  parmValue
}

                                        #------------------------------------------------------------------------------
                                        #	whichDistribution
                                        #
                                        #	This function simply returns the matching rows from the larger
                                        #	masterDistributionTabledata frame in a smaller identiacally 
                                        #	structured data frame.
                                        #
                                        #	masterDistributionTable - master distribution data frame loaded 
                                        #		from the master distribution input file
                                        #	distName - Name of distribution to select
                                        #
whichDistribution <- function (masterDistributionTable, distName) {
  xDist <- which(masterDistributionTable[["DistName"]] == distName)
  if (length(xDist) > 0) {
                                        # logMessage(paste("Using ", distName, " distributions from input distribution file."))
  } else {
    stop(paste(distName, "distribution is not in the input distribution file.\n", sep=" "))
  }
  masterDistributionTable[xDist,]
}

                                        #------------------------------------------------------------------------------
                                        #	validateMasterDistributions
                                        #
                                        #	Attempt loading each valid distribution (specified in VALID.DISTRIBUTIONS)
                                        #	And check that the Prob column sums to 1.0
                                        #
validateMasterDistributions <- function(masterDistributionTable) {
  tmpMessages <- "Error(s)\n"
  for (tmpDistributionName in VALID.DISTRIBUTIONS) {
    tmpDistribution <- whichDistribution(masterDistributionTable, tmpDistributionName)
    if(! is.numeric(masterDistributionTable$Prob )) {
      stop("Problem in distributions file -- a non-numeric entry in Prob.\n")
    }
    tmpProbSum <- sum(tmpDistribution$Prob) 
    if ( fabs(1 -  tmpProbSum) > 0.01 ) {
      stop(paste("Prob column for", tmpDistributionName, "does not at up to 1.\n", sep=" "))
    }
    if(! is.numeric(masterDistributionTable$Lower )) {
      stop("Problem in distributions file -- a non-numeric entry in Lower.\n")
    }
    if(! is.numeric(masterDistributionTable$Upper )) {
      stop("Problem in distributions file -- a non-numeric entry in Upper.\n")
    }
    if(! is.numeric(masterDistributionTable$Mean )) {
      stop("Problem in distributions file -- a non-numeric entry in Mean.\n")
    }
    if(! is.numeric(masterDistributionTable$StDev )) {
      stop("Problem in distributions file -- a non-numeric entry in StDev.\n")
    }
    if(! is.numeric(masterDistributionTable$Const )) {
      stop("Problem in distributions file -- a non-numeric entry in Const.\n")
    }
    if(! is.numeric(masterDistributionTable$Factor )) {
      stop("Problem in distributions file -- a non-numeric entry in Factor.\n")
    }
    if(! is.numeric(masterDistributionTable$minCut )) {
      stop("Problem in distributions file -- a non-numeric entry in minCut.\n")
    }
    if(! is.numeric(masterDistributionTable$maxCut )) {
      stop("Problem in distributions file -- a non-numeric entry in maxCut.\n")
    }
    
    tmpErrors <-
      ifelse( (tmpDistribution$Rule=="unif"),
             ifelse( (is.na(tmpDistribution$Lower)),
                    paste("Uniform Distribution for", tmpDistribution$DistName,
                          tmpDistribution$Category, "does not contain a Lower value.\n", sep=" "),
                    ifelse( (is.na(tmpDistribution$Upper)),
                           paste("Uniform Distribution for", tmpDistribution$DistName,
                                 tmpDistribution$Category, "does not contain an Upper value.\n", sep=" "),
                           ifelse(	(tmpDistribution$Lower > tmpDistribution$Upper),
                                  paste("Uniform Distribution Lower Bound is greater than the Upper Bound for",
                                        tmpDistribution$DistName, tmpDistribution$Category, "\n", sep=" "),
                                  ""))), 
             ifelse( (tmpDistribution$Rule=="const"),
                    ifelse( is.na(tmpDistribution$Const),
                           paste("Constant Distribution for", tmpDistribution$DistName,
                                 tmpDistribution$Category,"does not contain a contant value.\n", sep=" "),
                           ""),
                    ifelse( (tmpDistribution$Rule=="norm"),
                           ifelse( (is.na(tmpDistribution$Lower)),
                                  paste("Normal Distribution for", tmpDistribution$DistName,
                                        tmpDistribution$Category, "does not contain a Lower value.\n", sep=" "),			
                                  ifelse( (is.na(tmpDistribution$Upper)),
                                         paste("Normal Distribution for", tmpDistribution$DistName,
                                               tmpDistribution$Category, "does not contain an Upper value.\n", sep=" "),
                                         ifelse( (is.na(tmpDistribution$Mean)),
                                                paste("Normal Distribution for", tmpDistribution$DistName,
                                                      tmpDistribution$Category, "does not contain a Mean value.\n", sep=" "),
                                                ifelse( (is.na(tmpDistribution$StDev)),
                                                       paste("Normal Distribution for", tmpDistribution$DistName,
                                                             tmpDistribution$Category, "does not contain a StDev value.\n", sep=" "),
                                                       "")))),
                           ifelse( (tmpDistribution$Rule=="cat"),
                                  ifelse( is.na(tmpDistribution$Lower),
                                         paste("Category Distribution for", tmpDistribution$DistName,
                                               tmpDistribution$Category, "does not contain a Lower value.\n", sep=" "),			
                                         ifelse( is.na(tmpDistribution$Upper),
                                                paste("Category Distribution for", tmpDistribution$DistName,
                                                      tmpDistribution$Category, "does not contain an Upper value.\n", sep=" "),
                                                ifelse( (tmpDistribution$xBP != "y" & tmpDistribution$xBP != "" ),
                                                       paste("Category Distribution for", tmpDistribution$DistName,
                                                             tmpDistribution$Category, "does not contain a valid xBP value.\n", sep=" "),
                                                       ""))),
                                  ifelse( (tmpDistribution$Rule=="cont"),
                                         ifelse( is.na(tmpDistribution$Factor),
                                                paste("Continuous Distribution for", tmpDistribution$DistName,
                                                      tmpDistribution$Category,"does not contain a Factor value.\n", sep=" "),			
                                                ifelse( (tmpDistribution$xBP != "y" & tmpDistribution$xBP != "" ),
                                                       paste("Continuous Distribution for", tmpDistribution$DistName,
                                                             tmpDistribution$Category,"does not contain a valid xBP value.\n", sep=" "),
                                                       "")),
                                         "")))))
    if ( length( which(tmpErrors > "") > 0 ) ) {
      tmpMessages <- c(tmpMessages, tmpErrors[which(tmpErrors > "")])
    }
  }
  if ( length(tmpMessages) > 1 )  {
    stop(tmpMessages)
  }
}

                                        #------------------------------------------------------------------------------
                                        #	yearFloat2CDMdate
                                        #
                                        #	function to convert decimal years used throughout the program
                                        #	to CDM date format for output
                                        #
                                        #	The date format to be used is contained in:
                                        #		OSIM.CDM.DATE.FORMAT
                                        #
yearFloat2CDMdate <- function(year) {
  format(as.Date((year - 1900) * 365.25 - 1, origin="1900-01-01"), format=OSIM.CDM.DATE.FORMAT )
}

                                        #------------------------------------------------------------------------------
                                        #	logMessage
                                        #
                                        #	Write passed message with a timestamp to osim.runlog
                                        #
logMessage <- function (messageText) {
  timeStamp <- format(Sys.time(), "%Y%m%d %H:%M:%S")
                                        #if (is.na(osim.runlog)) {
  cat(paste(timeStamp,messageText,"\n",sep=" "))
                                        #}
  
  if (!is.na(osim.runlog)) {
    write(paste(timeStamp,messageText,sep=" "),file=osim.runlog,append=TRUE)
  }
}
                                        #------------------------------------------------------------------------------
                                        #	readNameValueFile
                                        #
                                        #	Reads requested Name=Value File returning a dataframe
                                        #
readNameValueFile <- function(filename) {
  tmpTable <- read.table(filename, header = FALSE, sep= "=", fill = TRUE)
  names(tmpTable) <- c("Name", "Value")
  tmpTable
}

                                        #------------------------------------------------------------------------------
                                        #	getExecParms
                                        #
                                        #	Read and validate execution (Name=Value) parameters
                                        #
getExecParms <- function() {
  execParmFile <- paste(OSIM.TABLE.PATH,OSIM.INPUT.PARMS.FILENAME, ".txt", sep="")
  
  if (! file.exists(execParmFile) ) { 
    stop(paste(execParmFile, "file does not exist.  Execution halted.\n", sep=" "))
  }
  
  execParmsTable <<- readNameValueFile(execParmFile)

                                        #--------------------------------------------------------------------------
                                        #	Validate execution parameters
                                        #--------------------------------------------------------------------------
  fileModifier <<- getParameter("fileModifier", execParmsTable)[1]
  if ( is.na(fileModifier) ) { 
    fileModifier <<- format(Sys.time(), "%Y%m%d_%H%M%S")
    osim.table.path <<- paste(OSIM.TABLE.PATH,"/OSIM_",fileModifier,sep="")		
  } else {
    if (grepl("^[0-9a-zA-Z_]+$",fileModifier)) {
      fileModifier <<- gsub("^OSIM_","",fileModifier)
      osim.table.path <<- paste(OSIM.TABLE.PATH,"/OSIM_",fileModifier,sep="")
    } else {
      stop(paste("fileModifier (",fileModifier,
                 ") execution parameter must be alphanumeric.",sep=""))
    }
  }
  
                                        # If output directory does not exist, create it
  osim.table.path <<- gsub("//","/",osim.table.path)
  if (! file.exists(osim.table.path) ) {
    dir.create(osim.table.path)
  }
  
  osim.table.path <<- paste(osim.table.path,"/",sep="")
  
                                        # Set Global Runlog name
  osim.runlog <<- paste(osim.table.path, OSIM.RUNLOG.FILENAME, "_", 
                        fileModifier, ".txt", sep="")
  
  logMessage(paste("fileModifier", "=", fileModifier, sep=" "))
  
                                        #
                                        # Get and validate the remaining input execution parameters
                                        #
  simName <<- getParameter("simName", execParmsTable)[1]
  simDescription <<- getParameter("simDescription", execParmsTable)[1]
  
  createSimTables <<- getParameter("createSimTables", execParmsTable)[1]
  if (! is.na(createSimTables) & ! is.logical(createSimTables) ) {
    stop(paste("createSimTables (",createSimTables,
               ") execution parameter must be TRUE or FALSE.",sep=""))
  }
  if ( is.na(createSimTables) ) {createSimTables <<- TRUE}
  
  createSimPersons <<- getParameter("createSimPersons", execParmsTable)[1]
  if (! is.na(createSimPersons) & ! is.logical(createSimPersons) ) {
    stop(paste("createSimPersons (",createSimPersons,
               ") execution parameter must be TRUE or FALSE.",sep=""))
  }
  if ( is.na(createSimPersons) ) {createSimPersons <<- TRUE}
  
  validationMode <<- getParameter("validationMode", execParmsTable)[1]
  if (! is.na(validationMode) & ! is.logical(validationMode) ) {
    stop(paste("validationMode (",validationMode,
               ") execution parameter must be TRUE or FALSE.",sep=""))
  }
  if ( is.na(validationMode) ) {validationMode <<- FALSE}
  
  if ( createSimPersons ) {
    fileHeader <<- getParameter("fileHeader", execParmsTable)[1]
    if (! is.na(fileHeader) & ! is.logical(fileHeader) ) {
      stop(paste("fileHeader (",fileHeader,
                 ") execution parameter must be TRUE or FALSE.",sep=""))
    }
    if ( is.na(fileHeader) ) {fileHeader <<- TRUE }
    
    personCount <<- checkParameter("personCount", execParmsTable, 1, 500000000, 5000000)
    personStartID <<- checkParameter("personStartID", execParmsTable, 1, 500000000, 1)
    minDatabaseDate <<- checkParameter("minDatabaseDate", execParmsTable, 1900, 100000000, 2000)
    maxDatabaseDate <<- checkParameter("maxDatabaseDate", execParmsTable, 1900, 100000000, 2010)
    dateDiff <- maxDatabaseDate - minDatabaseDate
    if ( dateDiff > 100 ) {
      stop(paste("The Difference between min and maxDatabaseDate (", 
                 dateDiff,") can not exceed 100.",sep=""))
    }
    if ( dateDiff < 1 ) {
      stop(paste("The Difference between min and maxDatabaseDate (",
                 dateDiff,") can not be less than 1.",sep=""))
    }
    fileDistNumber <<- getParameter("fileDistNumber", execParmsTable)[1]
    if ( is.na(fileDistNumber)) {
      fileDistNumber <<- as.character(personStartID)
    } else {
      if (! grepl("^[0-9a-zA-Z_]+$",fileDistNumber)) {
        stop(paste("fileDistNumber (",fileDistNumber,
                   ") execution parameter must be alphanumeric.",sep=""))
      }
    }
  }
  
  if ( createSimTables ) {
    drugCount <<- checkParameter("drugCount", execParmsTable, 1, 75000, 5000)
    conditionCount <<- checkParameter("conditionCount", execParmsTable, 1, 25000, 4000)
  }

}

                                        #------------------------------------------------------------------------------
                                        #	getMasterDistributionTable
                                        #
                                        #	Reads Master Distribution Table into Global Data Frame
                                        #
getMasterDistributionTable <- function(filename) {
  logMessage("-----------------------------------------------------------------------")
  logMessage(paste("-- Reading Master Distribution Table ", filename))
  logMessage("-----------------------------------------------------------------------")
  masterDistributionTable <<- read.table(filename, header=TRUE, sep="\t", fill=TRUE, flush=TRUE)
  
  masterDistributionTable$xBP <<- tolower(masterDistributionTable$xBP)
  
  validateMasterDistributions(masterDistributionTable)
}

                                        #------------------------------------------------------------------------------
                                        #	Housekeeping
                                        #	
                                        #	Process Function 1.1:  Housekeeping
                                        #
                                        #	The Housekeeping function validates the input parameters and 
                                        #	probability distributions, creates the output directory, 
                                        #	copies the probability distribution data to the output 
                                        #	directory, and creates and saves a documentation file that 
                                        #	describes the simulation run.
                                        #
Housekeeping <- function(Module) {
  if (Module==1) {

    logMessage("-----------------------------------------------------------------------")
    logMessage(paste("NAME:",simName))
    logMessage(paste("DESCRIPTION:",simDescription))
    logMessage(paste("OUTPUT DIRECTORY:",osim.table.path))
    logMessage("-----------------------------------------------------------------------")

                                        # Copy the input distribution file to the output directory
    originalDistributionFile <- paste(OSIM.TABLE.PATH,OSIM.INPUT.DISTRIBUTION.FILENAME,
                                      ".txt", sep="")
    
    if ( file.exists(originalDistributionFile) ) {
      logMessage("   Copying Distributions to output directory.")
      file.copy(originalDistributionFile,
                paste(osim.table.path,OSIM.DISTRIBUTION.FILENAME, "_", 
                      fileModifier, ".txt", sep=""))
    } else {
      stop(paste(originalDistributionFile, 
                 "input distribution file does not exist.  Execution halted.\n", sep=" "))
    }
  }
  
  if (Module==2) {
                                        # Verify all input files exist for simulation
    if ( ! file.exists(sub("/$","",osim.table.path) ) ) {
      stop(paste("Input directory",osim.table.path,"does not exist.",sep=" "))
    }
    for (file in c(OSIM.DRUGS.FILENAME, 
                   OSIM.CONDITIONS.FILENAME,
                   OSIM.DRUGOUTCOME.FILENAME,
                   OSIM.INDOUTCOME.FILENAME)) {
      filename <- paste(osim.table.path, file, "_", fileModifier, ".txt", sep="")
      if ( ! file.exists(filename) ) {
        stop(paste("Input file",filename,"does not exist.",sep=" "))
      }
    }
  }
                                        #--------------------------------------------------------------------------
                                        #	Read master distribution table
                                        #--------------------------------------------------------------------------
  getMasterDistributionTable(paste(osim.table.path,OSIM.DISTRIBUTION.FILENAME, "_", 
                                   fileModifier, ".txt", sep=""))

}

                                        #------------------------------------------------------------------------------
                                        #	generateSimulatedConditions
                                        #
                                        #	Process Function 1.2:  Generate Simulated Conditions
                                        #
                                        #	The Generate Simulated Conditions function generates Simulated Conditions 
                                        #	and Condition Attributes for the number of conditions specified by the user 
                                        #	in the input parameters.  
                                        #
                                        #	‘Conditions’ refers to the number of distinct outcome concepts that are 
                                        #	eligible to be contained in the database.  All conditions in the simulated 
                                        #	dataset are fictitious entities, recorded with a unique identifier that does 
                                        #	not correspond to any real diagnosis code or concept.  Conditions can occur 
                                        #	in the background population.  Risk factors for the condition may include 
                                        #	age, gender, race, a generic “confounder”, and any drug or indication.  
                                        #
generateSimulatedConditions <- function() {
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- BEGIN generateSimulatedConditions")
  logMessage("-----------------------------------------------------------------------")
                                        #--------------------------------------------------------------------------
                                        #	Simulated Condistion Specific Distributions
                                        #--------------------------------------------------------------------------
  CondBaselinePrevalence <- whichDistribution(masterDistributionTable, "CondBaselinePrevalence")
  CondAttrRiskAge <- whichDistribution(masterDistributionTable, "CondAttrRiskAge")
  CondAttrRiskGender <- whichDistribution(masterDistributionTable, "CondAttrRiskGender")
  CondAttrRiskRace <- whichDistribution(masterDistributionTable, "CondAttrRiskRace")
  CondConfounderRisk <- whichDistribution(masterDistributionTable, "CondConfounderRisk")
  CondSensitivity <- whichDistribution(masterDistributionTable, "CondSensitivity")
  CondSpecificity <- whichDistribution(masterDistributionTable, "CondSpecificity")
  CondOccurrence <- whichDistribution(masterDistributionTable, "CondOccurrence")
  
                                        #--------------------------------------------------------------------------
                                        #	Simulate Conditions
                                        #--------------------------------------------------------------------------
  logMessage(paste("   Creating",conditionCount,"Simulated Conditions.",sep=" "))
                                        #	Prebuild Conditions data frame
  OSIM.Conditions <- data.frame(
                                CONDITION_ID=rep(0, conditionCount), 
                                CONDITION_PREVALENCE_CATEGORY=rep("", conditionCount),
                                CONDITION_PREVALENCE=rep(0, conditionCount),
                                CONDITION_AGE_ATTRIB_RISK_CATEGORY=rep("", conditionCount),
                                CONDITION_GENDER_ATTRIB_RISK_CATEGORY=rep("", conditionCount),
                                CONDITION_RACE_ATTRIB_RISK_CATEGORY=rep("", conditionCount),
                                CONDITION_CONFOUNDER_ATTRIB_RISK_CATEGORY=rep("", conditionCount),
                                CONDITION_SENSITIVITY_CATEGORY=rep("", conditionCount),
                                CONDITION_SENSITIVITY=rep(0, conditionCount),
                                CONDITION_SPECIFICITY_CATEGORY=rep("", conditionCount),
                                CONDITION_SPECIFICITY=rep(0, conditionCount),
                                CONDITION_OCCURRENCE_CATEGORY=rep("", conditionCount))

                                        #	Now fill it in a column at a time
  OSIM.Conditions$CONDITION_ID <- 1:conditionCount
  
  OSIM.Conditions$CONDITION_PREVALENCE <- 
    MultiIndex(conditionCount, CondBaselinePrevalence$Prob)
  
  OSIM.Conditions$CONDITION_PREVALENCE_CATEGORY <- 
    CondBaselinePrevalence$Category[OSIM.Conditions$CONDITION_PREVALENCE]
  
  OSIM.Conditions$CONDITION_PREVALENCE <- 
    secondaryDistribution(OSIM.Conditions, Col="CONDITION_PREVALENCE", 
                          Dist=CondBaselinePrevalence)
  
  OSIM.Conditions$CONDITION_AGE_ATTRIB_RISK_CATEGORY <- 
    Multi(conditionCount, CondAttrRiskAge$Category, CondAttrRiskAge$Prob)
  
  OSIM.Conditions$CONDITION_GENDER_ATTRIB_RISK_CATEGORY <- 
    Multi(conditionCount, CondAttrRiskGender$Category, CondAttrRiskGender$Prob)
  
  OSIM.Conditions$CONDITION_RACE_ATTRIB_RISK_CATEGORY <- 
    Multi(conditionCount, CondAttrRiskRace$Category, CondAttrRiskRace$Prob)
  
  OSIM.Conditions$CONDITION_CONFOUNDER_ATTRIB_RISK_CATEGORY <- 
    Multi(conditionCount, CondConfounderRisk$Category, CondConfounderRisk$Prob)
  
  OSIM.Conditions$CONDITION_SENSITIVITY <- 
    MultiIndex(conditionCount, CondSensitivity$Prob)
  
  OSIM.Conditions$CONDITION_SENSITIVITY_CATEGORY <- 
    CondSensitivity$Category[OSIM.Conditions$CONDITION_SENSITIVITY]
  
  OSIM.Conditions$CONDITION_SENSITIVITY <- 
    secondaryDistribution(OSIM.Conditions, Col="CONDITION_SENSITIVITY", 
                          Dist=CondSensitivity)
  
  OSIM.Conditions$CONDITION_SPECIFICITY <- 
    MultiIndex(conditionCount, CondSpecificity$Prob)
  
  OSIM.Conditions$CONDITION_SPECIFICITY_CATEGORY <- 
    CondSpecificity$Category[OSIM.Conditions$CONDITION_SPECIFICITY]
  
  OSIM.Conditions$CONDITION_SPECIFICITY <- 
    secondaryDistribution(OSIM.Conditions, Col="CONDITION_SPECIFICITY", 
                          Dist=CondSpecificity)
  
  OSIM.Conditions$CONDITION_OCCURRENCE_CATEGORY <- 
    Multi(conditionCount, CondOccurrence$Category, CondOccurrence$Prob)

  logMessage(paste("   ",conditionCount,"Simulated Conditions created.",sep=" "))
  
                                        #--------------------------------------------------------------------------
                                        #	Write the Simulated Conditions File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.CONDITIONS.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Writing",conditionCount,
                   "Simulated Conditions to",filename,sep=" "))
  write.table(OSIM.Conditions, file=filename, row.names=FALSE, 
              col.names=TRUE, sep="\t", na="", quote=FALSE, append=FALSE)
  logMessage(paste("   ",conditionCount,"Simulated Conditions written.",sep=" "))
  
  rm(OSIM.Conditions) # Cleanup
  
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- END generateSimulatedConditions")
  logMessage("-----------------------------------------------------------------------")
  
}	#	END generateSimulatedConditions

                                        #------------------------------------------------------------------------------
                                        #	generateSimulatedDrugsIndications
                                        #
                                        #	Process Function 1.3:  Generate Simulated Drugs & Indications
                                        #
                                        #	The Generate Simulated Drugs function generates Simulated Drugs and Drug 
                                        #	Attributes for the number of drugs specified by the user in the input parms.
                                        #
                                        #	‘Drugs’ is the number of distinct drug concepts that are eligible to be 
                                        #	contained in the database.  All drugs in the simulated dataset are 
                                        #	fictitious entities, recorded with a unique identifier that does not 
                                        #	correspond to any real drug code or concept.  
                                        #
                                        #	Each drug has multiple attributes, including prevalence of drug use, 
                                        #	length and number of periods of drug exposure, sensitivity and specificity 
                                        #	of data capture for drug exposure.  Because the characteristics of each 
                                        #	attribute will be sampled from probability distributions, it is important 
                                        #	to define the number of drugs as a sufficiently large number to produce a 
                                        #	representative sample of different drug scenarios for study.
                                        #
generateSimulatedDrugsIndications <- function() {
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- BEGIN generateSimulatedDrugsIndications")
  logMessage("-----------------------------------------------------------------------")
                                        #--------------------------------------------------------------------------
                                        #	Simulated Drug Specific Distributions
                                        #--------------------------------------------------------------------------
  DrugBaselinePrevalence <- whichDistribution(masterDistributionTable, "DrugBaselinePrevalence")
  DrugAttrRiskAge <- whichDistribution(masterDistributionTable, "DrugAttrRiskAge")
  DrugAttrRiskGender <- whichDistribution(masterDistributionTable, "DrugAttrRiskGender")
  DrugAttrRiskRace <- whichDistribution(masterDistributionTable, "DrugAttrRiskRace")
  DrugConfounderRisk <- whichDistribution(masterDistributionTable, "DrugConfounderRisk")
  DrugSensitivity <- whichDistribution(masterDistributionTable, "DrugSensitivity")
  DrugSpecificity <- whichDistribution(masterDistributionTable, "DrugSpecificity")	
  DrugNumExposures <- whichDistribution(masterDistributionTable, "DrugNumExposures")	
  DrugExposureLength <- whichDistribution(masterDistributionTable, "DrugExposureLength")	
  DrugsPerIndication <- whichDistribution(masterDistributionTable, "DrugsPerIndication")	
  DrugPriorIndication <- whichDistribution(masterDistributionTable, "DrugPriorIndication")
  DrugOutcomeRiskType <- whichDistribution(masterDistributionTable, "DrugOutcomeRiskType")
  DrugOutcomeConstantRateOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRateOnset")
  DrugOutcomeConstantRiskOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRiskOnset")
  DrugOutcomeConstantRateAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRateAttrRisk")
  DrugOutcomeConstantRiskAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRiskAttrRisk")
  IndOutcomeAttrRisk <- whichDistribution(masterDistributionTable, "IndOutcomeAttrRisk")	
  
                                        #--------------------------------------------------------------------------
                                        #	Simulate Drugs
                                        #--------------------------------------------------------------------------
  logMessage(paste("   Creating",drugCount,"Simulated Drugs.",sep=" "))
                                        #	Prebuild Drugs data frame
  OSIM.Drugs <- data.frame(
                           DRUG_ID=rep(0, drugCount), 
                           DRUG_PREVALENCE_CATEGORY=rep("", drugCount),
                           DRUG_PREVALENCE=rep(0, drugCount),
                           DRUG_AGE_ATTRIB_RISK_CATEGORY=rep("", drugCount),
                           DRUG_GENDER_ATTRIB_RISK_CATEGORY=rep("", drugCount),
                           DRUG_RACE_ATTRIB_RISK_CATEGORY=rep("", drugCount),
                           DRUG_CONFOUNDER_ATTRIB_RISK_CATEGORY=rep("", drugCount),
                           DRUG_SENSITIVITY_CATEGORY=rep("", drugCount),
                           DRUG_SENSITIVITY=rep(0, drugCount),
                           DRUG_SPECIFICITY_CATEGORY=rep("", drugCount),
                           DRUG_SPECIFICITY=rep(0, drugCount),
                           DRUG_EXPOSURE_LENGTH_CATEGORY=rep("", drugCount),
                           DRUG_NUM_EXPOSURES_CATEGORY=rep("", drugCount),
                           DRUG_INDICATION_PROPORTION_CATEGORY=rep("", drugCount),
                           DRUG_INDICATION_PROPORTION=rep(0, drugCount),
                           INDICATION_ID=rep(0, drugCount))
  
                                        #	Now fill it in a column at a time
                                        #   DRUG_ID is just a sequence
  OSIM.Drugs$DRUG_ID <- 1:drugCount
  
                                        #   DRUG_RPREVALENCE and DRUG_PREVALENCE_CATEGORY
  OSIM.Drugs$DRUG_PREVALENCE <- MultiIndex(drugCount, DrugBaselinePrevalence$Prob)
  
  OSIM.Drugs$DRUG_PREVALENCE_CATEGORY <- 
    DrugBaselinePrevalence$Category[OSIM.Drugs$DRUG_PREVALENCE]
  
  OSIM.Drugs$DRUG_PREVALENCE <- 
    secondaryDistribution(OSIM.Drugs, Col="DRUG_PREVALENCE", 
                          Dist=DrugBaselinePrevalence)
  
                                        #   Set Drug Attributable Risks
  OSIM.Drugs$DRUG_AGE_ATTRIB_RISK_CATEGORY <- 
    Multi(drugCount, DrugAttrRiskAge$Category, DrugAttrRiskAge$Prob)
  
  OSIM.Drugs$DRUG_GENDER_ATTRIB_RISK_CATEGORY <- 
    Multi(drugCount, DrugAttrRiskGender$Category, DrugAttrRiskGender$Prob)
  
  OSIM.Drugs$DRUG_RACE_ATTRIB_RISK_CATEGORY <- 
    Multi(drugCount, DrugAttrRiskRace$Category, DrugAttrRiskRace$Prob)
  
  OSIM.Drugs$DRUG_CONFOUNDER_ATTRIB_RISK_CATEGORY <- 
    Multi(drugCount, DrugConfounderRisk$Category, DrugConfounderRisk$Prob)
  
                                        #   Set DRUG_SENSITIVITY and DRUG_SENSITIVITY_CATEGORY
  OSIM.Drugs$DRUG_SENSITIVITY <- 
    MultiIndex(drugCount, DrugSensitivity$Prob)
  
  OSIM.Drugs$DRUG_SENSITIVITY_CATEGORY <- 
    DrugSensitivity$Category[OSIM.Drugs$DRUG_SENSITIVITY]
  
  OSIM.Drugs$DRUG_SENSITIVITY <- 
    secondaryDistribution(OSIM.Drugs, Col="DRUG_SENSITIVITY", 
                          Dist=DrugSensitivity)
  
                                        #   Set DRUG_SPECIFICITY and DRUG_SPECIFICITY_CATEGORY
  OSIM.Drugs$DRUG_SPECIFICITY <- 
    MultiIndex(drugCount, DrugSpecificity$Prob)
  
  OSIM.Drugs$DRUG_SPECIFICITY_CATEGORY <- 
    DrugSpecificity$Category[OSIM.Drugs$DRUG_SPECIFICITY]
  
  OSIM.Drugs$DRUG_SPECIFICITY <- 
    secondaryDistribution(OSIM.Drugs, Col="DRUG_SPECIFICITY", 
                          Dist=DrugSpecificity)
  
                                        #   Set Drug Exposure Values
  OSIM.Drugs$DRUG_EXPOSURE_LENGTH_CATEGORY <- 
    Multi(drugCount, DrugExposureLength$Category, DrugExposureLength$Prob)
  
  OSIM.Drugs$DRUG_NUM_EXPOSURES_CATEGORY <- 
    Multi(drugCount, DrugNumExposures$Category, DrugNumExposures$Prob)
  
                                        #   Set DRUG_INDICATION_PROPORTION and DRUG_INDICATION_PROPORTION_CATEGORY
  OSIM.Drugs$DRUG_INDICATION_PROPORTION <- 
    MultiIndex(drugCount, DrugPriorIndication$Prob)
  
  OSIM.Drugs$DRUG_INDICATION_PROPORTION_CATEGORY <- 
    DrugPriorIndication$Category[OSIM.Drugs$DRUG_INDICATION_PROPORTION]
  
  OSIM.Drugs$DRUG_INDICATION_PROPORTION <- 
    secondaryDistribution(OSIM.Drugs, Col="DRUG_INDICATION_PROPORTION", 
                          Dist=DrugPriorIndication)

                                        #--------------------------------------------------------------------------
                                        #	Simulate Indications
                                        #--------------------------------------------------------------------------
                                        #	Prebuild Condition data frame
                                        #    Build the Indications as big as it can ever be -- the number of Drugs
                                        #    We will truncate it later after assigning INDICATION_IDs to Drugs
  
  logMessage(paste("   Creating","Simulated Indications.",sep=" "))
  OSIM.Indications <- data.frame(
                                 INDICATION_ID=conditionCount+1:drugCount, 
                                 DRUGS_PER_INDICATION_CATEGORY=rep("", drugCount),
                                 DRUGS_PER_INDICATION=rep(0, drugCount))

                                        #	Now fill it in a column at a time
                                        #	Indications are independent from Conditions, so we use different IDs	
                                        #	Set IndicationId = Conditions + 1  	
  
  OSIM.Indications$DRUGS_PER_INDICATION <- 
    MultiIndex(drugCount, DrugsPerIndication$Prob)
  
  OSIM.Indications$DRUGS_PER_INDICATION_CATEGORY <- 
    DrugsPerIndication$Category[OSIM.Indications$DRUGS_PER_INDICATION]
  
  OSIM.Indications$DRUGS_PER_INDICATION <- 
    secondaryDistribution(OSIM.Indications, Col="DRUGS_PER_INDICATION", 
                          Dist=DrugsPerIndication, ResultType="discrete")

                                        #	build a vector of INDICATION_IDs each repeated DRUGS_PER_INDICATION times
  OSIM.Drugs$INDICATION_ID <- 
    rep(OSIM.Indications$INDICATION_ID,OSIM.Indications$DRUGS_PER_INDICATION)[1:drugCount]
  
                                        #--------------------------------------------------------------------------
                                        #	Truncate Indications data frame to just the used Indications
                                        #--------------------------------------------------------------------------
  indicationCount <<- max(OSIM.Drugs$INDICATION_ID) - conditionCount
  OSIM.Indications <- OSIM.Indications[1:indicationCount,]
  
  logMessage(paste("   ",indicationCount,"Simulated Indications created.",sep=" "))
  
                                        #--------------------------------------------------------------------------
                                        #	Write the Simulated Drugs File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.DRUGS.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Writing",drugCount,"Simulated Drugs to",filename,sep=" "))
  write.table(OSIM.Drugs, file=filename, row.names=FALSE, col.names=TRUE, 
              sep="\t", na="", quote=FALSE, append=FALSE)
  logMessage(paste("   ",drugCount,"Simulated Drugs written.",sep=" "))
  
                                        #--------------------------------------------------------------------------
                                        #	Write the Simulated Indications File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.INDICATIONS.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Writing",indicationCount,
                   "Simulated Indications to",filename,sep=" "))
  write.table(OSIM.Indications, file=filename, row.names=FALSE, 
              col.names=TRUE, sep="\t", na="", quote=FALSE, append=FALSE)
  logMessage(paste("   ",indicationCount,"Simulated Indications written.",sep=" "))
  
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- END generateSimulatedDrugsIndications")
  logMessage("-----------------------------------------------------------------------")
  
}	#	END generateSimulatedDrugsIndications

                                        #------------------------------------------------------------------------------
                                        #	generateSimulatedDrugOutcomes
                                        #	
                                        #	Process Function 1.4:  Generate Simulated Drugs Outcomes
                                        #
                                        #	The Generate Simulated Drugs Outcomes function generates Simulated 
                                        #	Drugs Outcome Relationship Attributes (adverse events).  Perhaps 
                                        #	the most important relationship under consideration is the temporal 
                                        #	relationship between the drugs and the outcomes.  Increased risk in 
                                        #	harmful outcomes following drug exposure could be indicative of 
                                        #	potential drug adverse reactions that warrant further consideration.
                                        #
                                        #	The Simulated Drug Outcomes file contains the attributable risk 
                                        #	assigned to each drug / condition pair.  The vast majority of drug 
                                        #	condition pairs are assigned no attributable risk, reflecting no 
                                        #	increased risk of that outcome following drug exposure.  Because 
                                        #	the number of unique drug / condition pairs can be very 
                                        #	large (20,000,000 using default drug and condition counts), by 
                                        #	default drug / condition pairs that have no attributable risk are 
                                        #	not stored in this file.  
                                        #
generateSimulatedDrugOutcomes <- function() {
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- BEGIN generateSimulatedDrugOutcomes")
  logMessage("-----------------------------------------------------------------------")
                                        #--------------------------------------------------------------------------
                                        #	Simulate Drug Outcome Relationships
                                        #--------------------------------------------------------------------------
  DrugOutcomeRiskType <- whichDistribution(masterDistributionTable, "DrugOutcomeRiskType")
  DrugOutcomeConstantRateOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRateOnset")
  DrugOutcomeConstantRiskOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRiskOnset")
  DrugOutcomeConstantRateAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRateAttrRisk")
  DrugOutcomeConstantRiskAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRiskAttrRisk")
                                        #--------------------------------------------------------------------------
                                        #	Process Drug x Outcome size data frame
                                        #	in MAX.DATAFRAME.SIZE chunks
                                        #--------------------------------------------------------------------------
  logMessage(paste("   Creating and Writing","Simulated Drug Outcomes",sep=" "))
  drugConditionXREFCount <- drugCount * conditionCount
  drugConditionXREF <- 1
  drugConditionsWritten <- 0
  while (drugConditionXREF <= drugConditionXREFCount) {
    thisPassCount <- drugConditionXREFCount - (drugConditionXREF - 1)
    if ( thisPassCount > MAX.DATAFRAME.SIZE ) {
      thisPassCount <- MAX.DATAFRAME.SIZE
    }
                                        #	Prebuild Drug / Condition data frame
    OSIM.DrugOutcomes <- data.frame(
                                    CONDITION_ID=drugConditionXREF:(drugConditionXREF+thisPassCount-1), 
                                    DRUG_ID=rep(0, thisPassCount),
                                    DRUG_OUTCOME_ATTRIB_RISK_TYPE=Multi(thisPassCount, 
                                      DrugOutcomeRiskType$Category, DrugOutcomeRiskType$Prob),
                                    DRUG_OUTCOME_TIME_TO_ONSET_CATEGORY=rep("", thisPassCount),
                                    DRUG_OUTCOME_ATTRIB_RISK_CATEGORY=rep("", thisPassCount))

    OSIM.DrugOutcomes$DRUG_OUTCOME_TIME_TO_ONSET_CATEGORY <-
      ifelse(OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
             as.vector(Multi(thisPassCount, 
                             DrugOutcomeConstantRiskOnset$Category, DrugOutcomeConstantRiskOnset$Prob)),
             ifelse(OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant rate",
                    as.vector(Multi(thisPassCount, 
                                    DrugOutcomeConstantRateOnset$Category, DrugOutcomeConstantRateOnset$Prob)),
                    ""
                    )
             )
    
    OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_CATEGORY=
      ifelse(OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
             as.vector(Multi(thisPassCount, 
                             DrugOutcomeConstantRiskAttrRisk$Category, DrugOutcomeConstantRiskAttrRisk$Prob)),
             ifelse(OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant rate",
                    as.vector(Multi(thisPassCount, 
                                    DrugOutcomeConstantRateAttrRisk$Category, DrugOutcomeConstantRateAttrRisk$Prob)),
                    ""
                    )
             )

                                        #	Omit DRUG_OUTCOME_ATTRIB_RISK_TYPE == "omit"
    OmitCategory <- DrugOutcomeRiskType$Category[which(DrugOutcomeRiskType$Rule=="omit")]
    OSIM.DrugOutcomes <- OSIM.DrugOutcomes[-which(
                                                  OSIM.DrugOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE==OmitCategory),]
    
                                        #	Map generated Index to Drug x Condition Indexes
    OSIM.DrugOutcomes$DRUG_ID <- (OSIM.DrugOutcomes$CONDITION_ID-1) %% drugCount + 1
    OSIM.DrugOutcomes$CONDITION_ID <- (OSIM.DrugOutcomes$CONDITION_ID-1) %/% drugCount + 1
    
                                        #----------------------------------------------------------------------
                                        #	Write the Simulated Drug Outcomes File
                                        #----------------------------------------------------------------------
    condFileAppend <- (drugConditionXREF > 1) 
    filename <- paste(osim.table.path, OSIM.DRUGOUTCOME.FILENAME, "_", 
                      fileModifier, ".txt", sep="")
    write.table(OSIM.DrugOutcomes, file=filename, row.names=FALSE, 
                col.names=(! condFileAppend), sep="\t", na="", quote=FALSE, 
                append=condFileAppend)
    
    drugConditionsWritten <- drugConditionsWritten + nrow(OSIM.DrugOutcomes)
    rm(OSIM.DrugOutcomes)
    
    drugConditionXREF <- drugConditionXREF + thisPassCount
  }
  logMessage(paste("   ",drugConditionsWritten,"Simulated Drug Outcomes created and written.",sep=" "))
  logMessage(paste("    (",(drugConditionXREFCount-drugConditionsWritten),
                   "omitted from output.)",sep=" "))
  
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- END generateSimulatedDrugOutcomes")
  logMessage("-----------------------------------------------------------------------")
  
}	#	END generateSimulatedDrugOutcomes

                                        #------------------------------------------------------------------------------
                                        #	generateSimulatedIndicationOutcomes
                                        #	
                                        #	Process Function 1.5:  Generate Simulated Indication Outcomes
                                        #
                                        #	The Generate Simulated Indication Outcomes function generates 
                                        #	Simulated Indication Outcome Relationships.  
                                        #
                                        #	Often times, co-morbidities can be risk factors for subsequent 
                                        #	disease outcomes.  For example, patients with diabetes have 
                                        #	increased risk of subsequent cardiovascular events.  Confounding 
                                        #	by indication can be introduced because drugs intended to treat 
                                        #	a particular indication are associated with potential high-risk 
                                        #	populations.  
                                        #
                                        #	The simulation procedure incorporates the effect of the 
                                        #	indication on each outcome, independent from drug exposure.
                                        #
generateSimulatedIndicationOutcomes <- function() {
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- BEGIN generateSimulatedIndicationOutcomes")
  logMessage("-----------------------------------------------------------------------")
                                        #--------------------------------------------------------------------------
                                        #	Simulate Indication Outcome Relationships
                                        #--------------------------------------------------------------------------
  IndOutcomeAttrRisk <- whichDistribution(masterDistributionTable, "IndOutcomeAttrRisk")	

                                        #--------------------------------------------------------------------------
                                        #	Process Indication x Outcome size data frame
                                        #	in MAX.DATAFRAME.SIZE chunks
                                        #--------------------------------------------------------------------------
  logMessage(paste("   Creating and Writing","Simulated Indication Outcomes.",sep=" "))
  indicationConditionXREFCount <- indicationCount * conditionCount
  indicationConditionXREF <- 1
  indicationConditionsWritten <- 0

  while (indicationConditionXREF <= indicationConditionXREFCount) {
    thisPassCount <- indicationConditionXREFCount - (indicationConditionXREF - 1)
    if ( thisPassCount > MAX.DATAFRAME.SIZE ) {
      thisPassCount <- MAX.DATAFRAME.SIZE
    }
    
                                        #	Prebuild Drugs data frame
    OSIM.IndicationOutcomes <- data.frame(
                                          CONDITION_ID=indicationConditionXREF:(indicationConditionXREF+thisPassCount-1), 
                                          INDICATION_ID=rep(0, thisPassCount), 
                                          IND_OUTCOME_ATTRIB_RISK_CATEGORY=
                                          Multi(thisPassCount, IndOutcomeAttrRisk$Category, IndOutcomeAttrRisk$Prob))
    
                                        #	Truncate the Data Frame to just associated Indications / Outcomes
    OmitCategory <- IndOutcomeAttrRisk$Category[which(IndOutcomeAttrRisk$Rule=="omit")]
    OSIM.IndicationOutcomes <- 
      OSIM.IndicationOutcomes[-which(
                                     OSIM.IndicationOutcomes$IND_OUTCOME_ATTRIB_RISK_CATEGORY==OmitCategory),]

                                        #	Map generated Index to Drug x Condition Indexes
    OSIM.IndicationOutcomes$INDICATION_ID <- 
      (OSIM.IndicationOutcomes$CONDITION_ID-1) %% indicationCount + 1 + conditionCount
    OSIM.IndicationOutcomes$CONDITION_ID <- 
      (OSIM.IndicationOutcomes$CONDITION_ID-1) %/% indicationCount + 1
    
                                        #----------------------------------------------------------------------
                                        #	Write the Simulated Indications File
                                        #----------------------------------------------------------------------
    condFileAppend <- (indicationConditionXREF > 1) 
    filename <- paste(osim.table.path, OSIM.INDOUTCOME.FILENAME, "_", 
                      fileModifier, ".txt", sep="")
    write.table(OSIM.IndicationOutcomes, file=filename, row.names=FALSE, 
                col.names=(! condFileAppend), sep="\t", na="", quote=FALSE, 
                append=condFileAppend)
    indicationConditionsWritten <- indicationConditionsWritten + nrow(OSIM.IndicationOutcomes)
    rm(OSIM.IndicationOutcomes)
    
    indicationConditionXREF <- indicationConditionXREF + thisPassCount
  }
  logMessage(paste("   ",indicationConditionsWritten,
                   "Simulated Indication Outcomes created and written.",sep=" "))
  logMessage(paste("    (",(indicationConditionXREFCount-indicationConditionsWritten),
                   "omitted from output.)",sep=" "))

  logMessage("-----------------------------------------------------------------------")
  logMessage("-- END generateSimulatedIndicationOutcomes")
  logMessage("-----------------------------------------------------------------------")	

}	#	END generateSimulatedIndicationOutcomes

                                        #------------------------------------------------------------------------------
                                        #	generateSimulatedPersons
                                        #
                                        #	Process Function 2.2:  Generate Simulated Persons 
                                        #	The Generate Simulated Persons function generates Simulated 
                                        #	Persons, and records them in the format of the OMOP Common Data Model.
                                        #
                                        #	‘Persons’ is the total sample size in the database, as specified by 
                                        #	the user input parameter personCount.  The simulated dataset 
                                        #	procedure can be used to create validation datasets to aid in 
                                        #	evaluating the performance characteristics of the analysis methods.  
                                        #	The total number of persons will have a major bearing on the power 
                                        #	for methods, since the sample size for any specific drug or outcome 
                                        #	will likely be a function of the overall population (recognizing 
                                        #	that most methods are based on number of exposed or number of 
                                        #	outcomes).  
                                        #
                                        #	When the input parameter validationMode is set to True, this process 
                                        #	generates additional validation files that can be used to validate 
                                        #	the content and characteristics of the simulated data.
                                        #
generateSimulatedPersons <- function() {
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- BEGIN generateSimulatedPersons")
  logMessage("-----------------------------------------------------------------------")	
                                        #--------------------------------------------------------------------------
                                        #	Read the Simulated Drugs File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.DRUGS.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Reading","Simulated Drugs from",filename,sep=" "))
  OSIM.Drugs <- read.table(filename, header=TRUE, sep="\t", fill=TRUE)
  drugCount <- nrow(OSIM.Drugs)
  logMessage(paste("   ",drugCount,"Simulated Drugs loaded.",sep=" "))

                                        #--------------------------------------------------------------------------
                                        # Reread the Simulated Conditions File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.CONDITIONS.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Reading","Simulated Conditions from",filename,sep=" "))
  OSIM.Conditions <- read.table(filename, header=TRUE, sep="\t", fill=TRUE)
  conditionCount <- nrow(OSIM.Conditions)
  logMessage(paste("   ",conditionCount,"Simulated Conditions loaded.",sep=" "))
  
  
                                        #--------------------------------------------------------------------------
                                        #	Read the truncated Simulated Drug Outcomes File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.DRUGOUTCOME.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Reading","Simulated Drug Outcomes from",filename,sep=" "))
  OSIM.DrugOutcomes <- read.table(filename, header=TRUE, sep="\t", fill=TRUE)
  drugOutcomesCount <- nrow(OSIM.DrugOutcomes)
  logMessage(paste("   ",drugOutcomesCount,"Simulated Drug Outcomes loaded.",sep=" "))
  
                                        #--------------------------------------------------------------------------
                                        #	Read the truncated Simulated Indication Outcomes File
                                        #--------------------------------------------------------------------------
  filename <- paste(osim.table.path, OSIM.INDOUTCOME.FILENAME, "_", 
                    fileModifier, ".txt", sep="")
  logMessage(paste("   Reading","Simulated Indication Outcomes from",filename,sep=" "))
  OSIM.IndicationOutcomes <- read.table(filename, header=TRUE, sep="\t", fill=TRUE)
  indicationOutcomesCount <- nrow(OSIM.IndicationOutcomes)
  logMessage(paste("   ",indicationOutcomesCount,"Simulated Indication Outcomes loaded.",sep=" "))

                                        #--------------------------------------------------------------------------
                                        #	Simulated Outcomes Specific Distributions
                                        #--------------------------------------------------------------------------
  PersonAgeRecorded <- whichDistribution(masterDistributionTable, "PersonAgeRecorded")
  PersonGenderRecorded <- whichDistribution(masterDistributionTable, "PersonGenderRecorded")
  PersonRaceRecorded <- whichDistribution(masterDistributionTable, "PersonRaceRecorded")
  PersonAge <- whichDistribution(masterDistributionTable, "PersonAge")
  PersonGender <- whichDistribution(masterDistributionTable, "PersonGender")
  PersonRace <- whichDistribution(masterDistributionTable, "PersonRace")
  PersonConfounder <- whichDistribution(masterDistributionTable, "PersonConfounder")	
  PersonAgeAtDeath <- whichDistribution(masterDistributionTable, "PersonAgeAtDeath")	
  ObservationPeriod <- whichDistribution(masterDistributionTable, "ObservationPeriod")	
  DrugAttrRiskAge <- whichDistribution(masterDistributionTable, "DrugAttrRiskAge")
  DrugAttrRiskGender <- whichDistribution(masterDistributionTable, "DrugAttrRiskGender")
  DrugAttrRiskRace <- whichDistribution(masterDistributionTable, "DrugAttrRiskRace")
  DrugConfounderRisk <- whichDistribution(masterDistributionTable, "DrugConfounderRisk")
  DrugSensitivity <- whichDistribution(masterDistributionTable, "DrugSensitivity")
  DrugSpecificity <- whichDistribution(masterDistributionTable, "DrugSpecificity")	
  DrugNumExposures <- whichDistribution(masterDistributionTable, "DrugNumExposures")	
  DrugExposureLength <- whichDistribution(masterDistributionTable, "DrugExposureLength")	
  DrugsPerIndication <- whichDistribution(masterDistributionTable, "DrugsPerIndication")	
  DrugPriorIndication <- whichDistribution(masterDistributionTable, "DrugPriorIndication")
  DrugOutcomeRiskType <- whichDistribution(masterDistributionTable, "DrugOutcomeRiskType")
  DrugOutcomeConstantRateOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRateOnset")
  DrugOutcomeConstantRiskOnset <- whichDistribution(masterDistributionTable, 
                                                    "DrugOutcomeConstantRiskOnset")
  DrugOutcomeConstantRateAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRateAttrRisk")
  DrugOutcomeConstantRiskAttrRisk <- whichDistribution(masterDistributionTable, 
                                                       "DrugOutcomeConstantRiskAttrRisk")
  IndOutcomeAttrRisk <- whichDistribution(masterDistributionTable, "IndOutcomeAttrRisk")
  IndStartDate <- whichDistribution(masterDistributionTable, "IndStartDate")
  CondAttrRiskAge <- whichDistribution(masterDistributionTable, "CondAttrRiskAge")
  CondAttrRiskGender <- whichDistribution(masterDistributionTable, "CondAttrRiskGender")
  CondAttrRiskRace <- whichDistribution(masterDistributionTable, "CondAttrRiskRace")
  CondConfounderRisk <- whichDistribution(masterDistributionTable, "CondConfounderRisk")
  CondSensitivity <- whichDistribution(masterDistributionTable, "CondSensitivity")
  CondSpecificity <- whichDistribution(masterDistributionTable, "CondSpecificity")
  CondOccurrence <- whichDistribution(masterDistributionTable, "CondOccurrence")

                                        # set mean drug exposure forn non-normal distributions
  DrugExposureLength$Mean <- 
    ifelse(is.na(DrugExposureLength$Mean),
           (DrugExposureLength$Upper+DrugExposureLength$Lower)/2,
           DrugExposureLength$Mean
           )
  
                                        #--------------------------------------------------------------------------
                                        #	Simulate Persons
                                        #--------------------------------------------------------------------------
  tmpSeed <- as.integer(runif(1,personStartID,(personStartID+personCount-1)))
  logMessage(paste("   Setting Person Seed to",tmpSeed,sep=" "))
  set.seed(tmpSeed)
  
                                        #--------------------------------------------------------------------------
                                        #	Process Persons data frame
                                        #	in MAX.DATAFRAME.SIZE chunks
                                        #--------------------------------------------------------------------------
  indicationConditionXREFCount <- personCount
  indicationConditionXREF <- 1
  personIDOffset <- personStartID - 1
  currentPerson <- 1
  personCountLimit <- personCount

                                        #   Create all simulated Persons
  while (currentPerson <= personCount) {
    thisPassPersonCount <- personCount - (currentPerson - 1)
    logMessage(paste("   Creating a set of",thisPassPersonCount,"Persons.",sep=" "))
    
    if ( thisPassPersonCount > MAX.DATAFRAME.SIZE ) {
      thisPassPersonCount <- MAX.DATAFRAME.SIZE
    }

    personsAliveDuringObservationPeriod <- 0
    currentPersonID <- currentPerson + personIDOffset
    
                                        #	Prebuild Perons Validation and Calculation data frames
    OSIM.PersonsCalc <- data.frame(
                                   SIMULATED_AGE=rep(0, thisPassPersonCount),
                                   SIMULATED_BIRTH_YEAR=rep(0, thisPassPersonCount),
                                   SIMULATED_DEATH_AGE=rep(0, thisPassPersonCount),
                                   SIMULATED_DEATH_YEAR=rep(0, thisPassPersonCount))

    OSIM.PersonsValidation <- data.frame(
                                         PERSON_ID=currentPersonID:(currentPersonID+thisPassPersonCount-1),
                                         PERSON_AGE_RECORDED=rep(0, thisPassPersonCount),
                                         SIMULATED_AGE=rep(0, thisPassPersonCount),
                                         PERSON_GENDER_RECORDED=rep(0, thisPassPersonCount),
                                         SIMULATED_GENDER=rep("", thisPassPersonCount),
                                         PERSON_RACE_RECORDED=rep(0, thisPassPersonCount),
                                         SIMULATED_RACE=rep("", thisPassPersonCount),
                                         SIMULATED_CONFOUNDER=rep(0, thisPassPersonCount),
                                         SIMULATED_AGE_OF_DEATH=rep(0, thisPassPersonCount),
                                         SIMULATED_YEAR_OF_DEATH=rep(0, thisPassPersonCount))

                                        #----------------------------------------------------------------------
                                        #	Build the required number of simulated persons that do not 
                                        #	have a simulated death date prior to the database 
                                        #	observation period
                                        #----------------------------------------------------------------------
                                        #	Loop until the required number of "living" persons have been created
    while (personsAliveDuringObservationPeriod < thisPassPersonCount) {
      
                                        #	Prebuild Peron Age data frame
      OSIM.PersonsAge <- data.frame(
                                    SIMULATED_AGE=rep(0, thisPassPersonCount),
                                    SIMULATED_BIRTH_YEAR=rep(0, thisPassPersonCount),
                                    SIMULATED_DEATH_AGE=rep(0, thisPassPersonCount),
                                    SIMULATED_DEATH_YEAR=rep(0, thisPassPersonCount))
      
      OSIM.PersonsAge$SIMULATED_AGE_CATEGORY <- as.vector(Multi(
                                                                thisPassPersonCount, PersonAge$Category, PersonAge$Prob))
      
      OSIM.PersonsAge$SIMULATED_AGE <- secondaryDistribution(OSIM.PersonsAge, 
                                                             Col="SIMULATED_AGE_CATEGORY", Dist=PersonAge)
      
      OSIM.PersonsAge$SIMULATED_BIRTH_YEAR <- 
        maxDatabaseDate - OSIM.PersonsAge$SIMULATED_AGE
      
      OSIM.PersonsAge$SIMULATED_DEATH_AGE <- 
        MultiIndex(thisPassPersonCount, PersonAgeAtDeath$Prob)
      
      OSIM.PersonsAge$SIMULATED_DEATH_AGE <- secondaryDistribution(OSIM.PersonsAge, 
                                                                   Col="SIMULATED_DEATH_AGE", Dist=PersonAgeAtDeath)
      
      OSIM.PersonsAge$SIMULATED_DEATH_YEAR <- OSIM.PersonsAge$SIMULATED_BIRTH_YEAR + 
        OSIM.PersonsAge$SIMULATED_DEATH_AGE
      
                                        # Bring out your dead!
      if (length(which(OSIM.PersonsAge$SIMULATED_DEATH_YEAR < minDatabaseDate)) > 0) {
        OSIM.PersonsAge <- 
          OSIM.PersonsAge[-which(OSIM.PersonsAge$SIMULATED_DEATH_YEAR < minDatabaseDate),]
      }

      personsToAdd <- length(OSIM.PersonsAge$SIMULATED_AGE)
      if ((personsToAdd + personsAliveDuringObservationPeriod) > thisPassPersonCount) {
        personsToAdd <- thisPassPersonCount - personsAliveDuringObservationPeriod
      }
      
                                        #	Copy the valid persons to the main person validation data frame
      OSIM.PersonsCalc[(personsAliveDuringObservationPeriod+1):(
                                                                personsAliveDuringObservationPeriod+personsToAdd),1] = 
                                                                  OSIM.PersonsAge[1:personsToAdd,1]
      OSIM.PersonsCalc[(personsAliveDuringObservationPeriod+1):(
                                                                personsAliveDuringObservationPeriod+personsToAdd),2] = 
                                                                  OSIM.PersonsAge[1:personsToAdd,2]
      OSIM.PersonsCalc[(personsAliveDuringObservationPeriod+1):(
                                                                personsAliveDuringObservationPeriod+personsToAdd),3] = 
                                                                  OSIM.PersonsAge[1:personsToAdd,3]
      OSIM.PersonsCalc[(personsAliveDuringObservationPeriod+1):(
                                                                personsAliveDuringObservationPeriod+personsToAdd),4] = 
                                                                  OSIM.PersonsAge[1:personsToAdd,4]
      
      OSIM.PersonsValidation[(personsAliveDuringObservationPeriod+1):(
                                                                      personsAliveDuringObservationPeriod+personsToAdd),3] = 
                                                                        OSIM.PersonsAge[1:personsToAdd,1]
      OSIM.PersonsValidation[(personsAliveDuringObservationPeriod+1):(
                                                                      personsAliveDuringObservationPeriod+personsToAdd),9] = 
                                                                        OSIM.PersonsAge[1:personsToAdd,3]
      OSIM.PersonsValidation[(personsAliveDuringObservationPeriod+1):(
                                                                      personsAliveDuringObservationPeriod+personsToAdd),10] = 
                                                                        OSIM.PersonsAge[1:personsToAdd,4]
      personsAliveDuringObservationPeriod <- 
        personsAliveDuringObservationPeriod + personsToAdd
    }
    
                                        #   Sample for other attributes of the living
    OSIM.PersonsValidation$PERSON_AGE_RECORDED <- 
      MultiIndex(thisPassPersonCount, PersonAgeRecorded$Prob)
    
    OSIM.PersonsValidation$PERSON_AGE_RECORDED <- 
      secondaryDistribution(OSIM.PersonsValidation, Col="PERSON_AGE_RECORDED", 
                            Dist=PersonAgeRecorded)
    
    OSIM.PersonsValidation$PERSON_GENDER_RECORDED <- 
      MultiIndex(thisPassPersonCount, PersonGenderRecorded$Prob)
    
    OSIM.PersonsValidation$PERSON_GENDER_RECORDED <- 
      secondaryDistribution(OSIM.PersonsValidation, Col="PERSON_GENDER_RECORDED", 
                            Dist=PersonGenderRecorded)
    
    OSIM.PersonsValidation$SIMULATED_GENDER <- 
      Multi(thisPassPersonCount, PersonGender$Category, PersonGender$Prob)
    
    OSIM.PersonsValidation$PERSON_RACE_RECORDED <- 
      MultiIndex(thisPassPersonCount, PersonRaceRecorded$Prob)
    
    OSIM.PersonsValidation$PERSON_RACE_RECORDED <- 
      secondaryDistribution(OSIM.PersonsValidation, Col="PERSON_RACE_RECORDED", 
                            Dist=PersonRaceRecorded)
    
    OSIM.PersonsValidation$SIMULATED_RACE <- 
      Multi(thisPassPersonCount, PersonRace$Category, PersonRace$Prob)
    
    OSIM.PersonsValidation$SIMULATED_CONFOUNDER <- 
      Multi(thisPassPersonCount, PersonConfounder$Category, PersonConfounder$Prob)
    
                                        #	Build Persons data frame
    OSIM.Persons <- data.frame(
                               PERSON_ID=OSIM.PersonsValidation$PERSON_ID, 
                               YEAR_OF_BIRTH=
                               ifelse(OSIM.PersonsValidation$PERSON_AGE_RECORDED==1,
                                      as.integer(maxDatabaseDate - OSIM.PersonsValidation$SIMULATED_AGE),
                                      ""),
                               GENDER_CONCEPT_ID=
                               ifelse(OSIM.PersonsValidation$PERSON_GENDER_RECORDED==1,
                                      as.vector(OSIM.CDM.GENDER.CODES[
                                                                      as.vector(OSIM.PersonsValidation$SIMULATED_GENDER)]),
                                      ""),
                               RACE_CONCEPT_ID=
                               ifelse(OSIM.PersonsValidation$PERSON_RACE_RECORDED==1,
                                      as.vector(OSIM.CDM.RACE.CODES[
                                                                    as.vector(OSIM.PersonsValidation$SIMULATED_RACE)]),
                                      ""),
                               LOCATION_CONCEPT_ID=rep("", thisPassPersonCount),
                               SOURCE_PERSON_KEY=rep("", thisPassPersonCount),
                               SOURCE_GENDER_CODE=
                               ifelse(OSIM.PersonsValidation$PERSON_GENDER_RECORDED==1,
                                      as.vector(OSIM.PersonsValidation$SIMULATED_GENDER),
                                      ""),
                               SOURCE_LOCATION_CODE=rep("", thisPassPersonCount),
                               SOURCE_RACE_CODE=
                               ifelse(OSIM.PersonsValidation$PERSON_RACE_RECORDED==1,
                                      as.vector(OSIM.PersonsValidation$SIMULATED_RACE),
                                      ""))
    
    logMessage(paste("   Set of",thisPassPersonCount,"Persons created.",sep=" "))
                                        #----------------------------------------------------------------------
                                        #	Write the Current Set of Simulated Persons
                                        #----------------------------------------------------------------------
    condFileAppend <- (currentPerson > 1) 
    condFileHeaders <- (fileHeader && ! condFileAppend)
    filename <- paste(osim.table.path, OSIM.PERSONS.FILENAME, "_", 
                      fileModifier, "_", fileDistNumber, ".txt", sep="")
    write.table(OSIM.Persons, file=filename, row.names=FALSE, 
                col.names=condFileHeaders, sep="\t", na="", 
                quote=FALSE, append=condFileAppend)
    logMessage(paste("   Set of",thisPassPersonCount,"Persons written.",sep=" "))
    
    rm(OSIM.Persons) #	Don't need the real thing anymore, only the validation table
    
    if (validationMode) {
                                        #------------------------------------------------------------------
                                        #	Write the Current Set of Simulated Persons Validation
                                        #------------------------------------------------------------------
      filename <- paste(osim.table.path, OSIM.PERSONS.FILENAME, 
                        "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
      write.table(OSIM.PersonsValidation, file=filename, row.names=FALSE, 
                  col.names=condFileHeaders, sep="\t", na="", 
                  quote=FALSE, append=condFileAppend)
    }
    
                                        #	Process Function 2.2.1:  Generate Simulated Observation Period 
                                        #	The Generate Simulated Observation Period function generates an 
                                        #	Observation Period for each Simulated Person, and records it in 
                                        #	the OSIM_OBSERVATION_PERIOD	 file.
                                        #	
                                        #	An OBSERVATION_PERIOD is a defined period of time when data will 
                                        #	be recorded for a patient.  In administrative claims data, the 
                                        #	period of observation may be defined by a person’s enrollment in 
                                        #	the insurance plan (otherwise defined as the eligibility period).  
                                        #	In electronic health records, the observation period may be 
                                        #	defined by the span of time from the first observation to the 
                                        #	last observation.  In the simulated dataset, the observation 
                                        #	period is used to censor the data.  While patients may have drug 
                                        #	utilization and condition occurrence throughout an extended period 
                                        #	of time, only events that occur during the observation period may 
                                        #	be recorded into the database.
                                        #	
                                        #	Observational period duration will be constructed from first 
                                        #	sampling the ObservationPeriod input distribution to get a month 
                                        #	range category, then applying the Sampling Rule for that category 
                                        #	to obtain a specific number of months.  By default, the Sampling 
                                        #	Rule to select a value from any of the ObservationPeriod categories 
                                        #	is a uniform distribution within the category bounds.  
                                        #
                                        #   Generate a single observation period per simulate person
    OSIM.ObservationPeriodCalcs <- data.frame(
                                              MIN_DATE=pmax(OSIM.PersonsCalc$SIMULATED_BIRTH_YEAR,minDatabaseDate),
                                              MAX_DATE=pmin(OSIM.PersonsCalc$SIMULATED_DEATH_YEAR,maxDatabaseDate),
                                              MIN_OBS_DATE=rep(0,thisPassPersonCount),
                                              MAX_OBS_DATE=rep(0,thisPassPersonCount))
    
    OSIM.ObservationPeriodValidation <- data.frame(
                                                   SIMULATED_OBSERVATION_PERIOD_ID=OSIM.PersonsValidation$PERSON_ID * 10 + 1,
                                                   SIMULATED_PERSON_ID=OSIM.PersonsValidation$PERSON_ID, 
                                                   SIMULATED_OBSERVATION_CATEGORY=rep("",thisPassPersonCount),
                                                   SIMULATED_OBSERVATION_START_DATE=rep(0,thisPassPersonCount),
                                                   SIMULATED_OBSERVATION_PERIOD=MultiIndex(thisPassPersonCount, ObservationPeriod$Prob),
                                                   SIMULATED_OBSERVATION_END_DATE=rep(0,thisPassPersonCount))
    
    OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_CATEGORY <- 
      ObservationPeriod$Category[OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD]
    
    OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD <- 
      secondaryDistribution(OSIM.ObservationPeriodValidation, 
                            Col="SIMULATED_OBSERVATION_PERIOD", Dist=ObservationPeriod)
    
    OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD <- 
      OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD / 12
    
    OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_START_DATE <- 
      runif(thisPassPersonCount,OSIM.ObservationPeriodCalcs$MIN_DATE,
            OSIM.ObservationPeriodCalcs$MAX_DATE)
    
    OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_END_DATE <- 
      OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_START_DATE + 
        OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD
    
    OSIM.ObservationPeriodCalcs$MIN_OBS_DATE <- pmax(OSIM.ObservationPeriodCalcs$MIN_DATE,
                                                     OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_START_DATE)
    
    OSIM.ObservationPeriodCalcs$MAX_OBS_DATE <-	pmin(OSIM.ObservationPeriodCalcs$MAX_DATE,
                                                     OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_END_DATE)	
    
    OSIM.ObservationPeriod <- data.frame(
                                         OBSERVATION_PERIOD_ID=
                                         OSIM.ObservationPeriodValidation$SIMULATED_OBSERVATION_PERIOD_ID,
                                         OBSERVATION_START_DATE=
                                         yearFloat2CDMdate(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE),
                                         OBSERVATION_END_DATE=
                                         yearFloat2CDMdate(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE),
                                         PERSON_ID=OSIM.ObservationPeriodValidation$SIMULATED_PERSON_ID, 
                                         PERSON_STATUS_CONCEPT_ID=as.vector(OSIM.CDM.STATUS.CODES[
                                           as.vector(
                                                     ifelse(OSIM.PersonsCalc$SIMULATED_DEATH_YEAR>=maxDatabaseDate,
                                                            "active",
                                                            "deceased"))]),
                                         RX_DATA_AVAILABILITY=rep("Y",thisPassPersonCount))
    
                                        #----------------------------------------------------------------------
                                        #	Write the Current Set of Simulated Person Observation Periods
                                        #----------------------------------------------------------------------
    condFileAppend <- (currentPerson > 1)
    condFileHeaders <- (fileHeader && ! condFileAppend)
    filename <- paste(osim.table.path, OSIM.OBSERVATIONS.FILENAME, "_", 
                      fileModifier, "_", fileDistNumber, ".txt", sep="")
    write.table(OSIM.ObservationPeriod, file=filename, row.names=FALSE, 
                col.names=condFileHeaders, sep="\t", na="", quote=FALSE, 
                append=condFileAppend)
    rm(OSIM.ObservationPeriod) # Don't need the real thing anymore, only the validation tables
    
    if (validationMode) {
                                        #------------------------------------------------------------------
                                        #	Write the Curr Set of Simulated Persons Obs Periods Validation
                                        #------------------------------------------------------------------
      filename <- paste(osim.table.path, OSIM.OBSERVATIONS.FILENAME, 
                        "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
      write.table(OSIM.ObservationPeriodValidation, file=filename, 
                  col.names=condFileHeaders, sep="\t", na="", row.names=FALSE, 
                  quote=FALSE, append=condFileAppend)
    }

                                        #----------------------------------------------------------------------
                                        #   All simulated Persons and Observation Periods are built
                                        #----------------------------------------------------------------------
    
    logMessage("-----------------------------------------------------------------------")
    logMessage(paste("--   Begin generating Other Simulated Files for this set of",
                     thisPassPersonCount,"Persons",sep=" "))	
    logMessage("-----------------------------------------------------------------------")	
    
                                        #----------------------------------------------------------------------
                                        #   For each simulated Person
                                        # 		Generate Drug Exposures
                                        #		Conditions consisting of
                                        #			Indications
                                        #			Outcomes
                                        #			Conditions
                                        #----------------------------------------------------------------------
    for (thisPerson in currentPerson:thisPassPersonCount) {
      thisPersonID <- thisPerson + personIDOffset
      
      THIS.PERSON.DRUGEXPOSURE.SEED <- 1
      THIS.PERSON.CONDITION.SEED <- 1
      THIS.PERSON.DRUG.SEED <- 1
      THIS.PERSON.OUTCOME.SEED <- 1

                                        #	
                                        #	Process Function 2.2.2:  Generate Simulated Drug Exposures
                                        #	
                                        #	The Generate Simulated Drug Exposure function generates Drug 
                                        #	Exposures for each Simulated Person and records them in the 
                                        #	OSIM_DRUG_EXPOSURES file.
                                        #	
                                        #	To determine which Drugs get added to a Person, this process 
                                        #	examines every Drug for each patient and assigns a probability 
                                        #	of recording that Drug based on the attributes found in the 
                                        #	attribute table for that Drug including:  baseline prevalence, 
                                        #	age attributable risk, gender attributable risk, race 
                                        #	attributable risk, and confounder attributable risk.   If the 
                                        #	patient has the Drug based on the calculated probability, the 
                                        #	Drug sensitivity determines whether or not the value is 
                                        #	actually recorded in the database.  If so, then the number of 
                                        #	Exposures to record for the Drug are determined based on the 
                                        #	Number of Drug Exposures attribute.  A date for each Exposure 
                                        #	is randomly selected between the minimum and maximum database 
                                        #	dates, and if this date falls within the observation period for 
                                        #	that patient, it is recorded in the Drug Exposure file.  The 
                                        #	Drug Exposure end date is calculated by the Drug Exposure Length 
                                        #	attribute.  False positive Drug Exposures are recorded using the 
                                        #	condition specificity value.  
                                        #	
                                        #	Indications are also generated, and written to the 
                                        #	CONDITION_OCCURRENCE_FILE
                                        #	
                                        #	Unique Drug Exposure and Condition Occurrence IDs are calculated, 
                                        #	which include the PATIENT_ID to ensure that the ID’s will be 
                                        #	unique even for distributed runs.
                                        #	If the program is run in validation mode, a validation file is 
                                        #	also produced that records all Simulated Drugs, whether or not 
                                        #	they got recorded to the OSIM_DRUG_EXPOSURE_ FILE.  A specific 
                                        #	code to each validation record describing its ultimate disposition.
                                        #	 
                                        #	Valid codes are:
                                        #	1.	Drug Recorded
                                        #	2.	Drug not Recorded: False Negative 
                                        #	3.	Drug not Recorded:  not within Observation Period 
                                        #	4.	Drug Recorded:  False Positive 
                                        #	5.	Drug Not Recorded:  False Positive not within Observation Period
                                        #	
                                        #	If the program is run with Validation Mode set to true Simulated 
                                        #	Indications are also recorded in the Condition Occurrence Validation 
                                        #	file with the following codes:
                                        #	6.	Indication Recorded
                                        #	7.	Indication not Recorded:  not within Observation period 
                                        #	
      OSIM.DrugExposureValidation <- data.frame(
                                                SIMULATED_DRUG_EXPOSURE_ID=rep(0,drugCount),
                                                SIMULATED_PERSON_ID=rep(thisPersonID,drugCount),
                                                SIMULATED_DRUG_EXPOSURE_LENGTH=rep(0,drugCount),
                                                SIMULATED_DRUG_EXPOSURE_START_DATE=rep(0,drugCount),
                                                SIMULATED_DRUG_EXPOSURE_END_DATE=rep(0,drugCount),
                                                SIMULATED_DRUG_CONCEPT_CODE=1:drugCount,
                                                DRUG_RECORDING_TYPE=rep(0,drugCount),
                                                SIMULATED_DRUG_AGE_ATTRIB_RISK=rep(0,drugCount),
                                                SIMULATED_DRUG_GENDER_ATTRIB_RISK=rep(0,drugCount),
                                                SIMULATED_DRUG_RACE_ATTRIB_RISK=rep(0,drugCount),
                                                SIMULATED_DRUG_CONFOUNDER_RISK=rep(0,drugCount),
                                                SIMULATED_DRUG_COMBINED_RISK=rep(0,drugCount),
                                                SIMULATED_DRUG_INITIAL_PROBABILITY=rep(0,drugCount),
                                                SIMULATED_DRUG_NUM_EXPOSURES=rep(0,drugCount),
                                                SIMULATED_HAS_DRUG=rep(FALSE,drugCount),
                                                SIMULATED_HAS_RECORD=rep(FALSE,drugCount),
                                                SIMULATED_DRUG_DURING_OBSERVATION=rep(FALSE,drugCount),
                                                SIMULATED_HAS_INDICATION=rep(FALSE,drugCount))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_ID <- 
        thisPersonID * 100000 + OSIM.Drugs$DRUG_ID
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_AGE_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Drugs, Col="DRUG_AGE_ATTRIB_RISK_CATEGORY", 
                              BPCol="DRUG_PREVALENCE", Dist=DrugAttrRiskAge, 
                              ContValue=as.vector(OSIM.PersonsValidation$SIMULATED_AGE[thisPerson]))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_GENDER_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Drugs, Col="DRUG_GENDER_ATTRIB_RISK_CATEGORY", 
                              BPCol="DRUG_PREVALENCE", Dist=DrugAttrRiskGender, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_GENDER[thisPerson]))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_RACE_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Drugs, Col="DRUG_RACE_ATTRIB_RISK_CATEGORY", 
                              BPCol="DRUG_PREVALENCE", Dist=DrugAttrRiskRace, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_RACE[thisPerson]))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_CONFOUNDER_RISK <- 
        secondaryDistribution(OSIM.Drugs, Col="DRUG_CONFOUNDER_ATTRIB_RISK_CATEGORY", 
                              BPCol="DRUG_PREVALENCE", Dist=DrugConfounderRisk, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_CONFOUNDER[thisPerson]))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_COMBINED_RISK <- 
                                        # OSIM.Drugs$DRUG_PREVALENCE[OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE] + 
        OSIM.Drugs$DRUG_PREVALENCE + 
          OSIM.DrugExposureValidation$SIMULATED_DRUG_AGE_ATTRIB_RISK + 
            OSIM.DrugExposureValidation$SIMULATED_DRUG_GENDER_ATTRIB_RISK + 
              OSIM.DrugExposureValidation$SIMULATED_DRUG_RACE_ATTRIB_RISK + 
                OSIM.DrugExposureValidation$SIMULATED_DRUG_CONFOUNDER_RISK

                                        #		convert rate to probability
                                        #		set probDrug = 1 - exp(-rateDrug * (maxPersonDate - minPersonDate))				
      OSIM.DrugExposureValidation$SIMULATED_DRUG_INITIAL_PROBABILITY <- 
        1 - exp(-OSIM.DrugExposureValidation$SIMULATED_DRUG_COMBINED_RISK *
                (OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson] - 
                 OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson]))
      
                                        #	If initial probability is < 0, set to 0
      OSIM.DrugExposureValidation$SIMULATED_DRUG_INITIAL_PROBABILITY  <- 
        ifelse(OSIM.DrugExposureValidation$SIMULATED_DRUG_INITIAL_PROBABILITY < 0,
               0,
               OSIM.DrugExposureValidation$SIMULATED_DRUG_INITIAL_PROBABILITY )
      
                                        #	Sample for probability of drug exposure
      OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG <- 
        runif(drugCount,0,1) < 
          OSIM.DrugExposureValidation$SIMULATED_DRUG_INITIAL_PROBABILITY
      
                                        #	If the Person has drug exposure
                                        #		then HAS_RECORD = sample for sensitivy
                                        #		else HAS_RECORD = sample for specificity
      OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD <- 
        ifelse(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG, 
               runif(drugCount,0,1) < OSIM.Drugs$DRUG_SENSITIVITY,
               runif(drugCount,0,1) < (( 1 - OSIM.Drugs$DRUG_SPECIFICITY ) *
                                       OSIM.Drugs$DRUG_PREVALENCE))
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES <-
        ifelse(OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD,
               secondaryDistribution(OSIM.Drugs, Col="DRUG_NUM_EXPOSURES_CATEGORY", 
                                     Dist=DrugNumExposures, ResultType="discrete" ), 
               0)

                                        # If small set and validation mode... output entire drug exposure occurrence numbers
      if (validationMode & ((conditionCount * drugCount) <= 100000)) {	
        condFileAppend <- (thisPerson > 1) 
        condFileHeaders <- (fileHeader && ! condFileAppend)
        filename <- paste(osim.table.path, OSIM.DRUGEXPOSURE.FILENAME, 
                          "_VALID_ALL_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        write.table(OSIM.DrugExposureValidation, file=filename, 
                    row.names=FALSE, col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      
                                        #	Truncate to Drugs Recorded or actually taken
      OSIM.DrugExposureValidation <- 
        OSIM.DrugExposureValidation[which(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG | 
                                          OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD),]

                                        #	Hold on to the actually taken Drugs for Outcome Sampling
                                        #	Hold on to the Initial Probability for Preventative Condition calculations
      tmpDrugsTaken <- which(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG)
      OSIM.DrugsTaken <- data.frame(
                                    DRUG_ID=OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE[tmpDrugsTaken],
                                    EARLIEST_EXPOSURE=rep(0,length(tmpDrugsTaken)))
      
                                        #	Did person have indication
      n <- nrow(OSIM.DrugExposureValidation)
      OSIM.DrugExposureValidation$SIMULATED_HAS_INDICATION <- 
        ifelse(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG,
               runif(n,0,1) < 
               OSIM.Drugs$DRUG_INDICATION_PROPORTION[OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE],
               FALSE)

      OSIM.IndicationValidation <- data.frame(
                                              SIMULATED_CONDITION_OCCURRENCE_ID=rep(0,n),
                                              SIMULATED_PERSON_ID=rep(thisPersonID,n),
                                              SIMULATED_CONDITION_CONCEPT_CODE=
                                              OSIM.Drugs$INDICATION_ID[OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE],
                                              SIMULATED_DRUG_CONCEPT_CODE=
                                              OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE,
                                              CONDITION_RECORDING_TYPE=rep(0,n),
                                              SIMULATED_CONDITION_START_CATEGORY=rep("",n),
                                              SIMULATED_CONDITION_START_DATE=rep(0,n),
                                              SIMULATED_COND_AGE_ATTRIB_RISK=rep(NA,n),
                                              SIMULATED_COND_GENDER_ATTRIB_RISK=rep(NA,n),
                                              SIMULATED_COND_RACE_ATTRIB_RISK=rep(NA,n),
                                              SIMULATED_COND_CONFOUND_RISK=rep(NA,n),
                                              SIMULATED_DRUG_ATTRIB_RISK=rep(NA,n),
                                              SIMULATED_IND_ATTRIB_RISK=rep(NA,n),
                                              SIMULATED_IND_ID=rep(NA,n),
                                              SIMULATED_CONDITION_COMBINED_RISK=rep(NA,n),
                                              SIMULATED_CONDITION_INITIAL_PROBABILITY=rep(NA,n),
                                              SIMULATED_HAS_CONDITION=rep(TRUE,n),
                                              SIMULATED_HAS_RECORD=rep(TRUE,n),
                                              SIMULATED_DRUG_EXPOSURE_START_DATE=rep(NA,n),
                                              SIMULATED_CONDITION_NUM_OCCURRENCES=rep(NA,n))
      
      OSIM.IndicationValidation <- 
        OSIM.IndicationValidation[which(OSIM.DrugExposureValidation$SIMULATED_HAS_INDICATION),]
      
      n <- nrow(OSIM.IndicationValidation)
      
      if  (n > 0) {
        OSIM.IndicationValidation$SIMULATED_CONDITION_OCCURRENCE_ID <-
          (thisPersonID * 100000 + THIS.PERSON.CONDITION.SEED):
            (thisPersonID * 100000 + THIS.PERSON.CONDITION.SEED + 
             nrow(OSIM.IndicationValidation) - 1)
        
        THIS.PERSON.CONDITION.SEED <- 
          THIS.PERSON.CONDITION.SEED + nrow(OSIM.IndicationValidation)
      }
      
      n <- sum(OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES) +
        length(OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES[
                                                                        which(OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES==0)])
      
                                        #	Generate a row per drug exposure in the validation data frame
      tmpDF <- data.frame(
                          SIMULATED_DRUG_EXPOSURE_ID=rep("",n))

      
                                        #	Create a temp Drug Exposure Row for each Exposure
      tmpDF$SIMULATED_DRUG_EXPOSURE_ID <- 
        rep(OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_ID,
            ifelse((OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES==0),
                   1,
                   OSIM.DrugExposureValidation$SIMULATED_DRUG_NUM_EXPOSURES))
      
                                        #	Merge (INNER JOIN) with original Exposure Data Frame by original Exposure ID
      OSIM.DrugExposureValidation <- 
        merge(tmpDF,OSIM.DrugExposureValidation, by=c("SIMULATED_DRUG_EXPOSURE_ID"))
      
      n <- nrow(OSIM.DrugExposureValidation)
      
                                        #	Now create new unique IDs
      if (n > 0) {
        OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_ID <- 
          (thisPersonID * 100000 + THIS.PERSON.DRUGEXPOSURE.SEED):
            (thisPersonID * 100000 + THIS.PERSON.DRUGEXPOSURE.SEED + n - 1)

        THIS.PERSON.DRUGEXPOSURE.SEED <- 
          THIS.PERSON.DRUGEXPOSURE.SEED + nrow(OSIM.DrugExposureValidation)
      }

                                        #	Sample for other drug exposure values
      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_LENGTH <- 
        match(OSIM.Drugs$DRUG_EXPOSURE_LENGTH_CATEGORY[
                                                       c(OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE)],
              DrugExposureLength$Category)
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_LENGTH <- 
        secondaryDistribution(OSIM.DrugExposureValidation, 
                              Col="SIMULATED_DRUG_EXPOSURE_LENGTH", Dist=DrugExposureLength) / 365.25

      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_START_DATE <- 
        ifelse((OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG | 
                OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD),
               runif(nrow(OSIM.DrugExposureValidation),
                     OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson], 
                     OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson]),
               NA)

      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_END_DATE <- 
        ifelse((OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG | 
                OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD),
               OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_START_DATE + 
               OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_LENGTH ,
               NA)
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_END_DATE <- 
        ifelse((OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG | 
                OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD),
               pmin(OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_END_DATE,
                    rep(OSIM.PersonsValidation$SIMULATED_YEAR_OF_DEATH[thisPerson],n)),
               NA)
      
      OSIM.DrugExposureValidation$SIMULATED_DRUG_DURING_OBSERVATION <- 
        ifelse(OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD,
               (OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_END_DATE >=
                rep(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE[thisPerson],n)) &
               (OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_START_DATE <=
                rep(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE[thisPerson],n)),
               NA)

      OSIM.DrugExposureValidation$DRUG_RECORDING_TYPE <- 
        ifelse( ! OSIM.DrugExposureValidation$SIMULATED_HAS_RECORD,
               2,
               ifelse(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG,
                      ifelse(OSIM.DrugExposureValidation$SIMULATED_DRUG_DURING_OBSERVATION, 1, 3),
                      ifelse(OSIM.DrugExposureValidation$SIMULATED_DRUG_DURING_OBSERVATION, 4, 5)))
      
      OSIM.ActualDrugExposures <- 
        OSIM.DrugExposureValidation[which(OSIM.DrugExposureValidation$SIMULATED_HAS_DRUG),]
      
      OSIM.DrugExposure <- data.frame(
                                      DRUG_EXPOSURE_ID=rep(0,n),
                                      DRUG_EXPOSURE_START_DATE=rep(0,n),
                                      DRUG_EXPOSURE_END_DATE=rep(0,n),
                                      PERSON_ID=rep(thisPersonID,n),
                                      DRUG_CONCEPT_ID=rep(0,n),
                                      DRUG_EXPOSURE_TYPE=rep("",n),
                                      STOP_REASON=rep("",n),
                                      REFILLS=rep("",n),
                                      DRUG_QUANTITY=rep("",n),
                                      DAYS_SUPPLY=rep("",n),
                                      SOURCE_DRUG_CODE=rep("",n))
      
      OSIM.DrugExposure$DRUG_EXPOSURE_ID <- 
        OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_ID
      
      OSIM.DrugExposure$PERSON_ID <- OSIM.DrugExposureValidation$SIMULATED_PERSON_ID
      
      OSIM.DrugExposure$DRUG_EXPOSURE_START_DATE <- 
        yearFloat2CDMdate(OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_START_DATE)
      
      OSIM.DrugExposure$DRUG_EXPOSURE_END_DATE <- 
        yearFloat2CDMdate(OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_END_DATE)
      
      OSIM.DrugExposure$DRUG_CONCEPT_ID <- 
        OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE
      
      OSIM.DrugExposure <- 
        OSIM.DrugExposure[
                          which(OSIM.DrugExposureValidation$DRUG_RECORDING_TYPE == 1 | 
                                OSIM.DrugExposureValidation$DRUG_RECORDING_TYPE == 4 ),]
      
                                        #	Initialize Indication Start Date to earliest drug exposure
      minStartDates <- 
        tapply(OSIM.DrugExposureValidation$SIMULATED_DRUG_EXPOSURE_START_DATE, 
               OSIM.DrugExposureValidation$SIMULATED_DRUG_CONCEPT_CODE, min)
      
      OSIM.DrugsTaken$EARLIEST_EXPOSURE <- 
        as.vector(minStartDates)[match(as.character(OSIM.DrugsTaken$DRUG_ID),
                                       row.names(minStartDates))]
      
      OSIM.IndicationValidation$EARLIEST_EXPOSURE <- 
        as.vector(minStartDates)[
                                 match(as.character(OSIM.IndicationValidation$SIMULATED_DRUG_CONCEPT_CODE),
                                       row.names(minStartDates))]
      
                                        #	Now set Indication Start Date to uniform distribution between left censor date and earliest drug exposure			#	Now set Indication Start Category and Date 
      n <- nrow(OSIM.IndicationValidation)
      OSIM.IndicationValidation$SIMULATED_CONDITION_START_CATEGORY <-
        Multi(n, IndStartDate$Category, IndStartDate$Prob)
      
      OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE <-
        (secondaryDistribution(OSIM.IndicationValidation, Col="SIMULATED_CONDITION_START_CATEGORY", 
                               Dist=IndStartDate, Duration=(OSIM.IndicationValidation$EARLIEST_EXPOSURE -
                                 OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson]) * 365.25) / 365.25) +
                                   OSIM.IndicationValidation$EARLIEST_EXPOSURE

      
      OSIM.IndicationValidation$CONDITION_RECORDING_TYPE <-
        ifelse((OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE < 
                rep(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE[thisPerson],
                    nrow(OSIM.IndicationValidation))) |
               (OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE >
                rep(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE[thisPerson],
                    nrow(OSIM.IndicationValidation))),
               7,
               6)
      
                                        # Eliminate Indications before birth or after death
      OSIM.IndicationValidation <- OSIM.IndicationValidation[
                                                             which((OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE >=
                                                                    OSIM.PersonsCalc$SIMULATED_BIRTH_YEAR[thisPerson]) |
                                                                   (OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE <=
                                                                    OSIM.PersonsCalc$SIMULATED_DEATH_YEAR[thisPerson])),]
      
      tmpIndications <- which(OSIM.IndicationValidation$CONDITION_RECORDING_TYPE == 6)
      
      n <- length(tmpIndications)
      OSIM.Indication <- data.frame(
                                    CONDITION_OCCURRENCE_ID=rep(0,n),
                                    CONDITION_START_DATE=rep(0,n),
                                    PERSON_ID=rep(thisPersonID,n),
                                    CONDITION_END_DATE=rep(NA,n),
                                    CONDITION_OCCUR_TYPE=rep(NA,n),
                                    CONDITION_CONCEPT_ID=rep(0,n),
                                    STOP_REASON=rep(NA,n),
                                    DX_QUALIFIER=rep(NA,n),
                                    SOURCE_CONDITION_CODE=rep(NA,n))
      
      if (n > 0) {
        OSIM.Indication$CONDITION_OCCURRENCE_ID <- 
          OSIM.IndicationValidation$SIMULATED_CONDITION_OCCURRENCE_ID[tmpIndications]
        OSIM.Indication$CONDITION_CONCEPT_ID <-
          OSIM.IndicationValidation$SIMULATED_CONDITION_CONCEPT_CODE[tmpIndications]
        OSIM.Indication$CONDITION_START_DATE <-
          yearFloat2CDMdate(OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE[tmpIndications])
      }
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Drug Exposure File
                                        #------------------------------------------------------------------
      condFileAppend <- (thisPerson > 1) 
      condFileHeaders <- (fileHeader && ! condFileAppend)
      filename <- paste(osim.table.path, OSIM.DRUGEXPOSURE.FILENAME, "_", 
                        fileModifier, "_", fileDistNumber, ".txt", sep="")
      write.table(OSIM.DrugExposure, file=filename, row.names=FALSE, 
                  col.names=condFileHeaders, sep="\t", na="", 
                  quote=FALSE, append=condFileAppend)
      if (! OSIM.DEBUG.MODE) { rm(OSIM.DrugExposure) }
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Drug Exposure Validation File
                                        #------------------------------------------------------------------
      if (validationMode) {
        filename <- paste(osim.table.path, OSIM.DRUGEXPOSURE.FILENAME, 
                          "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        write.table(OSIM.DrugExposureValidation, file=filename, 
                    row.names=FALSE, col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      if (! OSIM.DEBUG.MODE) { rm(OSIM.DrugExposureValidation) }
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Indications
                                        #------------------------------------------------------------------
      filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                        "_", fileModifier, "_", fileDistNumber, ".txt", sep="")
      
      OSIM.Indication=cbind(A_TYPE=rep(1, nrow(OSIM.Indication)), OSIM.Indication)
      write.table(OSIM.Indication, file=filename, row.names=FALSE, 
                  col.names=condFileHeaders, 
                  sep="\t", na="", quote=FALSE,  append=condFileAppend)
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated IndicationsValidation File
                                        #------------------------------------------------------------------
      if (validationMode) {
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.IndicationValidation=cbind(A_TYPE=rep(1, nrow(OSIM.IndicationValidation)), OSIM.IndicationValidation)
        write.table(OSIM.IndicationValidation, file=filename, row.names=FALSE, 
                    col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      
                                        #	
                                        #	Process Function 2.2.2.1:  Generate Outcomes
                                        #	
                                        #	Often times, co-morbidities can be risk factors for subsequent 
                                        #	disease outcomes.  For example, patients with diabetes have 
                                        #	increased risk of subsequent cardiovascular events.  Confounding 
                                        #	by indication can be introduced because drugs intended to treat 
                                        #	a particular indication are associated with potential high-risk 
                                        #	populations.  The simulation procedure incorporates the effect 
                                        #	of the indication on each outcome, independent from drug exposure.
                                        #	
                                        #	Increased risk in harmful outcomes following drug exposure could 
                                        #	be indicative of potential drug adverse reactions that warrant 
                                        #	further consideration.  The simulation procedure will incorporate 
                                        #	the relationship between drugs and outcomes by introducing 
                                        #	additional cases of the condition into the sample based to the 
                                        #	attributable risk of the condition due to the drug.  
                                        #	
                                        #	Sensitivity can be estimated as the number of ‘true positives’ 
                                        #	divided by the total number of ‘true associations’.  Specificity 
                                        #	can be estimated as the number of ‘true negatives’ divided by the 
                                        #	total number of ‘false associations’.  Similarly, positive 
                                        #	predictive value and negative predictive value can also be 
                                        #	calculated.  
                                        #	
                                        #	The Generate Additional Outcomes generates additional 
                                        #	OSIM_CONDITION_OCCURRENCE records, representing Outcomes, based 
                                        #	on Indication and on Drug Exposure.
                                        #	
                                        #	If the program is run with Validation Mode set to true, Simulated 
                                        #	Outcomes are also recorded in the Condition Occurrence Validation 
                                        #	file with the following codes:
                                        #	8.	Outcome Recorded
                                        #	9.	Outcome not Recorded:  False Negative (not recorded due to sensitivity)
                                        #	10.	Outcome not Recorded:  not within Observation period 
                                        #	
                                        #------------------------------------------------------------------
                                        #	DRUG OUTCOMES
                                        #------------------------------------------------------------------
                                        #
      OSIM.SimulatedOutcomes <- 
        merge(OSIM.ActualDrugExposures, OSIM.DrugOutcomes,
              by.x="SIMULATED_DRUG_CONCEPT_CODE", by.y="DRUG_ID") # INNER JOIN
      
      OSIM.SimulatedDrugOutcomesBP <- data.frame(
                                                 CONDITION_PREVALENCE=
                                                 OSIM.Conditions$CONDITION_PREVALENCE[
                                                                                      OSIM.SimulatedOutcomes$CONDITION_ID],
                                                 CONDITION_SENSITIVITY=
                                                 OSIM.Conditions$CONDITION_SENSITIVITY[
                                                                                       OSIM.SimulatedOutcomes$CONDITION_ID])
      
      OSIM.SimulatedOutcomes <- 
        cbind(OSIM.SimulatedOutcomes, OSIM.SimulatedDrugOutcomesBP)
      
      OSIM.SimulatedOutcomes$INDICATION_ID <-
        ifelse(OSIM.SimulatedOutcomes$SIMULATED_HAS_INDICATION,
               OSIM.Drugs$INDICATION_ID[OSIM.SimulatedOutcomes$SIMULATED_DRUG_CONCEPT_CODE],
               NA
               )
      
      OSIM.SimulatedOutcomes <-
        merge(OSIM.SimulatedOutcomes,OSIM.IndicationOutcomes, all.x=TRUE,
              by=c("INDICATION_ID","CONDITION_ID")) # LEFT JOIN
      
      n <- nrow(OSIM.SimulatedOutcomes)

                                        #	Get Drug Attributable Risk
      OSIM.SimulatedOutcomes$tmpDrugRisk <-
        ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
               as.vector(secondaryDistribution(OSIM.SimulatedOutcomes,
                                               Col="DRUG_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                               BPCol="CONDITION_PREVALENCE", Dist=DrugOutcomeConstantRiskAttrRisk)),
               ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant rate",
                      as.vector(secondaryDistribution(OSIM.SimulatedOutcomes,
                                                      Col="DRUG_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                                      BPCol="CONDITION_PREVALENCE", Dist=DrugOutcomeConstantRateAttrRisk)),
                      ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Drug preventative effect",
                             as.vector(secondaryDistribution(OSIM.SimulatedOutcomes,
                                                             Col="DRUG_OUTCOME_ATTRIB_RISK_TYPE", 
                                                             BPCol="CONDITION_PREVALENCE", Dist=DrugOutcomeRiskType)),
                             0
                             )
                      )
               )
      
                                        #	Get Indication Attributable Risk
      OSIM.SimulatedOutcomes$tmpIndicationRisk <-
        ifelse(OSIM.SimulatedOutcomes$SIMULATED_HAS_INDICATION,
               secondaryDistribution(OSIM.SimulatedOutcomes,
                                     Col="IND_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                     BPCol="CONDITION_PREVALENCE", Dist=IndOutcomeAttrRisk),
               NA
               )
      
      OSIM.SimulatedOutcomes$Rate <-
        OSIM.SimulatedOutcomes$tmpDrugRisk +
          ifelse(is.na(OSIM.SimulatedOutcomes$tmpIndicationRisk),
                 0,
                 OSIM.SimulatedOutcomes$tmpIndicationRisk)
      
                                        #	Calculate Probability from Rate
                                        #	For Constant rate
                                        #	- assign risk for the drug exposure duration
                                        #	For constant risk
                                        #	- assign risk for the censored person observation period
      OSIM.SimulatedOutcomes$Probability <-
        ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant rate",
               as.vector(1 - exp(-OSIM.SimulatedOutcomes$Rate *
                                 ((OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_END_DATE - 
                                   OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_START_DATE)/
                                  (DrugExposureLength$Mean[match(
                                                                 as.vector(OSIM.Drugs$DRUG_EXPOSURE_LENGTH_CATEGORY[OSIM.SimulatedOutcomes$SIMULATED_DRUG_CONCEPT_CODE]),
                                                                 DrugExposureLength$Category)
                                                           ] / 365.25)) *
                                 (OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson] - 
                                  OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson]))),
               as.vector(1 - exp(-OSIM.SimulatedOutcomes$Rate *
                                 (OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson] - 
                                  OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson])))
               )
      
      OSIM.SimulatedOutcomes$Probability <- 
        ifelse(OSIM.SimulatedOutcomes$Probability < 0,
               0,
               OSIM.SimulatedOutcomes$Probability)
      
                                        #	Truncate to Actual Outcomes
      OSIM.SimulatedOutcomes <-
        OSIM.SimulatedOutcomes[which(runif(n,0,1) < 
                                     OSIM.SimulatedOutcomes$Probability),]
      
      n <- nrow(OSIM.SimulatedOutcomes)	
      
      OSIM.SimulatedOutcomes$HasRecord <- 
        runif(n,0,1) < OSIM.SimulatedOutcomes$CONDITION_SENSITIVITY
      
                                        #	Calculate regardless -- no if check and no NAs for start date calc
                                        #	A (very) few Preventative Drugs may creep in here...
                                        #	-	Set tha start date for preventative drug outcomes to unif(censored observation period)
      OSIM.SimulatedOutcomes$TimeToOnset <-
        ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
               as.vector(secondaryDistribution(OSIM.SimulatedOutcomes,
                                               Col="DRUG_OUTCOME_TIME_TO_ONSET_CATEGORY", Dist=DrugOutcomeConstantRiskOnset,
                                               Duration=OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_LENGTH*365.25) / 365.25),
               ifelse(OSIM.SimulatedOutcomes$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant rate",
                      as.vector(secondaryDistribution(OSIM.SimulatedOutcomes,
                                                      Col="DRUG_OUTCOME_TIME_TO_ONSET_CATEGORY", Dist=DrugOutcomeConstantRateOnset,
                                                      Duration=OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_LENGTH*365.25) / 365.25),
                      runif(n,OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson],
                            OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson]) -
                      OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_START_DATE
                                        # Make offset relative to Drug Exposure
                      )
               )

      OSIM.OutcomeValidation <- data.frame(
                                           SIMULATED_CONDITION_OCCURRENCE_ID=rep(0,n),
                                           SIMULATED_PERSON_ID=rep(thisPersonID,n),
                                           SIMULATED_CONDITION_CONCEPT_CODE=OSIM.SimulatedOutcomes$CONDITION_ID,
                                           SIMULATED_DRUG_CONCEPT_CODE=OSIM.SimulatedOutcomes$SIMULATED_DRUG_CONCEPT_CODE,
                                           CONDITION_RECORDING_TYPE=rep(0,n),
                                           SIMULATED_CONDITION_START_CATEGORY=rep("",n),
                                           SIMULATED_CONDITION_START_DATE=
                                           OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_START_DATE +
                                           OSIM.SimulatedOutcomes$TimeToOnset,
                                           SIMULATED_COND_AGE_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_GENDER_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_RACE_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_CONFOUND_RISK=rep(NA,n),
                                           SIMULATED_DRUG_ATTRIB_RISK=rep(0,n),
                                           SIMULATED_IND_ATTRIB_RISK=rep(0,n),
                                           SIMULATED_IND_ID=OSIM.SimulatedOutcomes$INDICATION_ID,
                                           SIMULATED_CONDITION_COMBINED_RISK=rep(0,n),
                                           SIMULATED_CONDITION_INITIAL_PROBABILITY=rep(0,n),
                                           SIMULATED_HAS_CONDITION=rep(TRUE,n),
                                           SIMULATED_HAS_RECORD=rep(FALSE,n),
                                           SIMULATED_DRUG_EXPOSURE_START_DATE=OSIM.SimulatedOutcomes$SIMULATED_DRUG_EXPOSURE_START_DATE,
                                           SIMULATED_CONDITION_NUM_OCCURRENCES=rep(NA,n))
      if (n > 0) {
        OSIM.OutcomeValidation$SIMULATED_CONDITION_OCCURRENCE_ID <-
          thisPersonID * 100000 + (THIS.PERSON.CONDITION.SEED:(THIS.PERSON.CONDITION.SEED+n-1))
        THIS.PERSON.CONDITION.SEED <- THIS.PERSON.CONDITION.SEED + n
        
        OSIM.OutcomeValidation$SIMULATED_CONDITION_COMBINED_RISK <- 
          OSIM.SimulatedOutcomes$Rate
        OSIM.OutcomeValidation$SIMULATED_DRUG_ATTRIB_RISK <- 
          OSIM.SimulatedOutcomes$tmpDrugRisk
        OSIM.OutcomeValidation$SIMULATED_IND_ATTRIB_RISK <- 
          OSIM.SimulatedOutcomes$tmpIndicationRisk
        OSIM.OutcomeValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY <- 
          OSIM.SimulatedOutcomes$Probability
        OSIM.OutcomeValidation$SIMULATED_HAS_RECORD <- 
          OSIM.SimulatedOutcomes$HasRecord
      }
      
                                        #	8	- Recorded
                                        #	9	- Not Recorded due to Sensitivity
                                        #	10	- Not in Observation Period
      OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE <-
        ifelse( (OSIM.SimulatedOutcomes$HasRecord),
               ifelse( (OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE <
                        rep(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE[
                                                                     thisPerson], n)) |
                      (OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE >
                       rep(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE[
                                                                    thisPerson], n)),
                      10,	
                      8),	
               9)	
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Outcomes Validation File
                                        #------------------------------------------------------------------
      if (validationMode) {
        condFileAppend <- TRUE
        condFileHeaders <- FALSE
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.OutcomeValidation=cbind(A_TYPE=rep(2, nrow(OSIM.OutcomeValidation)), OSIM.OutcomeValidation)
        write.table(OSIM.OutcomeValidation, file=filename, row.names=FALSE, 
                    col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      
                                        #	Truncate to Actual Outcomes
      tmpOutcomes <- which(OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE == 8)
      OSIM.OutcomeValidation <- 
        OSIM.OutcomeValidation[which(OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE == 8),]
      
      n <- nrow(OSIM.OutcomeValidation)

      OSIM.Outcome <- data.frame(
                                 CONDITION_OCCURRENCE_ID=rep(0,n),
                                 CONDITION_START_DATE=rep(0,n),
                                 PERSON_ID=rep(thisPersonID,n),
                                 CONDITION_END_DATE=rep(NA,n),
                                 CONDITION_OCCUR_TYPE=rep(NA,n),
                                 CONDITION_CONCEPT_ID=rep(0,n),
                                 STOP_REASON=rep(NA,n),
                                 DX_QUALIFIER=rep(NA,n),
                                 SOURCE_CONDITION_CODE=rep(NA,n))

      if (n > 0) {
        OSIM.Outcome$CONDITION_OCCURRENCE_ID <- 
          OSIM.OutcomeValidation$SIMULATED_CONDITION_OCCURRENCE_ID
        OSIM.Outcome$CONDITION_CONCEPT_ID <-
          OSIM.OutcomeValidation$SIMULATED_CONDITION_CONCEPT_CODE
        OSIM.Outcome$CONDITION_START_DATE <-
          yearFloat2CDMdate(OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE)

                                        #------------------------------------------------------------------
                                        #	Write the Simulated Outcomes
                                        #------------------------------------------------------------------
        condFileAppend <- TRUE
        condFileHeaders <- FALSE
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.Outcome=cbind(A_TYPE=rep(2, nrow(OSIM.Outcome)), OSIM.Outcome)
        write.table(OSIM.Outcome, file=filename, row.names=FALSE, 
                    col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }

      if (! OSIM.DEBUG.MODE) { rm(OSIM.Outcome) }
      
                                        #	
                                        #------------------------------------------------------------------
                                        #	INDICATION OUTCOMES
                                        #------------------------------------------------------------------
                                        #
      
      
                                        # Remove later duplicate indications
      OSIM.EarliestIndication <- 
        tapply(OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE,
               OSIM.IndicationValidation$SIMULATED_CONDITION_CONCEPT_CODE, min)
      
      OSIM.IndicationValidation <-
        OSIM.IndicationValidation[which(
					match(
                                              OSIM.IndicationValidation$SIMULATED_CONDITION_CONCEPT_CODE,
                                              row.names(OSIM.EarliestIndication)) &
					match(OSIM.IndicationValidation$SIMULATED_CONDITION_START_DATE,
                                              as.vector(OSIM.EarliestIndication))),]
      
                                        # Evaluate earliest incident of each indication
      OSIM.SimulatedIndOutcomes <-
        merge(OSIM.IndicationValidation, OSIM.IndicationOutcomes,
              by.x="SIMULATED_CONDITION_CONCEPT_CODE", by.y="INDICATION_ID")
      
      OSIM.SimulatedIndOutcomesBP <- data.frame(
                                                CONDITION_PREVALENCE=
                                                OSIM.Conditions$CONDITION_PREVALENCE[
                                                                                     OSIM.SimulatedIndOutcomes$CONDITION_ID],
                                                CONDITION_SENSITIVITY=
                                                OSIM.Conditions$CONDITION_SENSITIVITY[
                                                                                      OSIM.SimulatedIndOutcomes$CONDITION_ID])
      
      OSIM.SimulatedIndOutcomes <- 
        cbind(OSIM.SimulatedIndOutcomes, OSIM.SimulatedIndOutcomesBP)

      OSIM.SimulatedIndOutcomes$IndicationRisk <-
        secondaryDistribution(OSIM.SimulatedIndOutcomes,
                              Col="IND_OUTCOME_ATTRIB_RISK_CATEGORY", 
                              BPCol="CONDITION_PREVALENCE", Dist=IndOutcomeAttrRisk)
      
      OSIM.SimulatedIndOutcomes$Probability <-
        as.vector(1 - exp(-OSIM.SimulatedIndOutcomes$IndicationRisk *
                          (OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson] - 
                           OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson])))

      OSIM.SimulatedIndOutcomes$Probability <- 
        ifelse(OSIM.SimulatedIndOutcomes$Probability < 0,
               0,
               OSIM.SimulatedIndOutcomes$Probability)
      
      n <- nrow(OSIM.SimulatedIndOutcomes)	
      
                                        #	Truncate to Actual Outcomes
      OSIM.SimulatedIndOutcomes <-
        OSIM.SimulatedIndOutcomes[which(runif(n,0,1) < 
					OSIM.SimulatedIndOutcomes$Probability),]
      
                                        #	Eliminate Prior Drug Outcomes
      OSIM.SimulatedIndOutcomes <-
        OSIM.SimulatedIndOutcomes[which(is.na(match(OSIM.SimulatedIndOutcomes$CONDITION_ID,
                                                    OSIM.SimulatedOutcomes$CONDITION_ID))),]
      
      n <- nrow(OSIM.SimulatedIndOutcomes)	
      
      OSIM.SimulatedIndOutcomes$HasRecord <- 
        runif(n,0,1) < OSIM.SimulatedIndOutcomes$CONDITION_SENSITIVITY
      
                                        #	Calculate regardless -- no if check and no NAs for start date calc
      OSIM.SimulatedIndOutcomes$StartDate <- OSIM.SimulatedIndOutcomes$SIMULATED_CONDITION_START_DATE +
        runif(n,0,OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson]-
              OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson])
      
      OSIM.OutcomeValidation <- data.frame(
                                           SIMULATED_CONDITION_OCCURRENCE_ID=rep(0,n),
                                           SIMULATED_PERSON_ID=rep(thisPersonID,n),
                                           SIMULATED_CONDITION_CONCEPT_CODE=OSIM.SimulatedIndOutcomes$CONDITION_ID,
                                           SIMULATED_DRUG_CONCEPT_CODE=rep(NA,n),
                                           CONDITION_RECORDING_TYPE=rep(0,n),
                                           SIMULATED_CONDITION_START_CATEGORY=rep("",n),
                                           SIMULATED_CONDITION_START_DATE=OSIM.SimulatedIndOutcomes$StartDate,
                                           SIMULATED_COND_AGE_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_GENDER_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_RACE_ATTRIB_RISK=rep(NA,n),
                                           SIMULATED_COND_CONFOUND_RISK=rep(NA,n),
                                           SIMULATED_DRUG_ATTRIB_RISK=rep(0,n),
                                           SIMULATED_IND_ATTRIB_RISK=OSIM.SimulatedIndOutcomes$IndicationRisk,
                                           SIMULATED_IND_ID=OSIM.SimulatedIndOutcomes$SIMULATED_CONDITION_CONCEPT_CODE,
                                           SIMULATED_CONDITION_COMBINED_RISK=OSIM.SimulatedIndOutcomes$IndicationRisk,
                                           SIMULATED_CONDITION_INITIAL_PROBABILITY=OSIM.SimulatedIndOutcomes$Probability,
                                           SIMULATED_HAS_CONDITION=rep(TRUE,n),
                                           SIMULATED_HAS_RECORD=OSIM.SimulatedIndOutcomes$HasRecord,
                                           SIMULATED_DRUG_EXPOSURE_START_DATE=rep(0,n),
                                           SIMULATED_CONDITION_NUM_OCCURRENCES=rep(NA,n))
      if (n > 0) {
        OSIM.OutcomeValidation$SIMULATED_CONDITION_OCCURRENCE_ID <-
          thisPersonID * 100000 + (THIS.PERSON.CONDITION.SEED:(THIS.PERSON.CONDITION.SEED+n-1))
        THIS.PERSON.CONDITION.SEED <- THIS.PERSON.CONDITION.SEED + n
      }
      
                                        #	11	- Recorded
                                        #	12	- Not Recorded due to Sensitivity
                                        #	13	- Not in Observation Period
      OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE <-
        ifelse( (OSIM.SimulatedIndOutcomes$HasRecord),
               ifelse( (OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE <
                        rep(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE[
                                                                     thisPerson], n)) |
                      (OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE >
                       rep(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE[
                                                                    thisPerson], n)),
                      13,	
                      11),	
               12)	
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Outcomes Validation File
                                        #------------------------------------------------------------------
      if (validationMode) {
        condFileAppend <- TRUE
        condFileHeaders <- FALSE
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.OutcomeValidation=cbind(A_TYPE=rep(3, nrow(OSIM.OutcomeValidation)), OSIM.OutcomeValidation)
        write.table(OSIM.OutcomeValidation, file=filename, row.names=FALSE, 
                    col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      
                                        #	Truncate to Actual Outcomes
      tmpOutcomes <- which(OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE == 11)
      OSIM.OutcomeValidation <- 
        OSIM.OutcomeValidation[which(OSIM.OutcomeValidation$CONDITION_RECORDING_TYPE == 11),]
      
      n <- nrow(OSIM.OutcomeValidation)

      OSIM.Outcome <- data.frame(
                                 CONDITION_OCCURRENCE_ID=rep(0,n),
                                 CONDITION_START_DATE=rep(0,n),
                                 PERSON_ID=rep(thisPersonID,n),
                                 CONDITION_END_DATE=rep(NA,n),
                                 CONDITION_OCCUR_TYPE=rep(NA,n),
                                 CONDITION_CONCEPT_ID=rep(0,n),
                                 STOP_REASON=rep(NA,n),
                                 DX_QUALIFIER=rep(NA,n),
                                 SOURCE_CONDITION_CODE=rep(NA,n))

      if (n > 0) {
        OSIM.Outcome$CONDITION_OCCURRENCE_ID <- 
          OSIM.OutcomeValidation$SIMULATED_CONDITION_OCCURRENCE_ID
        OSIM.Outcome$CONDITION_CONCEPT_ID <-
          OSIM.OutcomeValidation$SIMULATED_CONDITION_CONCEPT_CODE
        OSIM.Outcome$CONDITION_START_DATE <-
          yearFloat2CDMdate(OSIM.OutcomeValidation$SIMULATED_CONDITION_START_DATE)

                                        #------------------------------------------------------------------
                                        #	Write the Simulated Outcomes
                                        #------------------------------------------------------------------
        condFileAppend <- TRUE
        condFileHeaders <- FALSE
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.Outcome=cbind(A_TYPE=rep(3, nrow(OSIM.Outcome)), OSIM.Outcome)
        write.table(OSIM.Outcome, file=filename, row.names=FALSE, 
                    col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }

      if (! OSIM.DEBUG.MODE) { rm(OSIM.Outcome) }

                                        #	
                                        #	Process Function 2.2.3:  Generate Simulated Condition Occurrences
                                        #	
                                        #	The Generate Simulated Condition Occurrences function generates 
                                        #	Condition Occurrences for each Simulated Person and records 
                                        #	them in the OSIM_CONDITION_OCCURRENCE file.
                                        #	
                                        #	To determine which conditions get added to a patient, this 
                                        #	process examines every condition for each patient and assigns 
                                        #	probability of recording that condition based on the attributes 
                                        #	found in the attribute table for that condition of:  baseline 
                                        #	prevalence, age attributable risk, gender attributable risk, 
                                        #	race attributable risk, and confounder attributable risk.   
                                        #	If the patient has the condition based on the calculated 
                                        #	probability, the condition sensitivity determines whether or 
                                        #	not the value is actually recorded in the database.  If so, 
                                        #	then the number of occurrences to record for the condition are 
                                        #	determined based on the condition occurrence attribute.  A date 
                                        #	for each occurrence is randomly selected between the minimum and 
                                        #	maximum database dates, and if this date falls within the 
                                        #	observation period for that patient, it is recorded in the 
                                        #	condition occurrence file.  False positive conditions are 
                                        #	recorded using the condition specificity value.
                                        #	
                                        #	If the program is run in validation mode, a validation file is 
                                        #	also produced that records all Simulated Conditions, whether or 
                                        #	not they got recorded to the OSIM_CONDITION_ OCCURRENCE FILE.  
                                        #	A specific code to each validation record describing its 
                                        #	ultimate disposition.  Valid codes are:
                                        #	1.	Condition Recorded
                                        #	2.	Condition not Recorded: False Negative (not recorded due to condition sensitivity)
                                        #	3.	Condition not Recorded:  not within Observation Period 
                                        #	4.	Condition Recorded:  False Positive (was recorded based on condition specificity)
                                        #	5.	Condition Not Recorded:  False Positive not within the observation period
                                        #	
      n <- nrow(OSIM.Conditions)
      OSIM.ConditionOccurrenceValidation <- data.frame(
                                                       SIMULATED_CONDITION_OCCURRENCE_ID=rep(0,n),
                                                       SIMULATED_PERSON_ID=rep(thisPersonID,n),
                                                       SIMULATED_CONDITION_CONCEPT_CODE=OSIM.Conditions$CONDITION_ID,
                                                       SIMULATED_DRUG_CONCEPT_CODE=rep(NA,n),
                                                       CONDITION_RECORDING_TYPE=rep("",n),
                                                       SIMULATED_CONDITION_START_CATEGORY=rep("",n),
                                                       SIMULATED_CONDITION_START_DATE=rep(0,n),
                                                       SIMULATED_COND_AGE_ATTRIB_RISK=rep(0,n),
                                                       SIMULATED_COND_GENDER_ATTRIB_RISK=rep(0,n),
                                                       SIMULATED_COND_RACE_ATTRIB_RISK=rep(0,n),
                                                       SIMULATED_COND_CONFOUND_RISK=rep(0,n),
                                                       SIMULATED_DRUG_ATTRIB_RISK=rep(0,n),
                                                       SIMULATED_IND_ATTRIB_RISK=rep(0,n),
                                                       SIMULATED_IND_ID=rep(NA,n),
                                                       SIMULATED_CONDITION_COMBINED_RISK=rep(0,n),
                                                       SIMULATED_CONDITION_INITIAL_PROBABILITY=rep(0,n),
                                                       SIMULATED_HAS_CONDITION=rep(0,n),
                                                       SIMULATED_HAS_RECORD=rep(0,n),
                                                       SIMULATED_DRUG_EXPOSURE_START_DATE=rep(NA,n),
                                                       SIMULATED_CONDITION_NUM_OCCURRENCES=rep(NA,n))
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_OCCURRENCE_ID <- 
        thisPersonID * 100000 + OSIM.Conditions$CONDITION_ID
      
                                        #	Sample for risk components
      OSIM.ConditionOccurrenceValidation$SIMULATED_COND_AGE_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Conditions, Col="CONDITION_AGE_ATTRIB_RISK_CATEGORY", 
                              BPCol="CONDITION_PREVALENCE", Dist=CondAttrRiskAge, 
                              ContValue=as.vector(OSIM.PersonsValidation$SIMULATED_AGE[thisPerson]))
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_COND_GENDER_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Conditions, Col="CONDITION_GENDER_ATTRIB_RISK_CATEGORY", 
                              BPCol="CONDITION_PREVALENCE", Dist=CondAttrRiskGender, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_GENDER[thisPerson]))
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_COND_RACE_ATTRIB_RISK <- 
        secondaryDistribution(OSIM.Conditions, Col="CONDITION_RACE_ATTRIB_RISK_CATEGORY", 
                              BPCol="CONDITION_PREVALENCE", Dist=CondAttrRiskRace, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_RACE[thisPerson]))
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_COND_CONFOUND_RISK <- 
        secondaryDistribution(OSIM.Conditions, Col="CONDITION_CONFOUNDER_ATTRIB_RISK_CATEGORY", 
                              BPCol="CONDITION_PREVALENCE", Dist=CondConfounderRisk, 
                              CatValue=as.vector(OSIM.PersonsValidation$SIMULATED_CONFOUNDER[thisPerson]))
      
                                        #	Combine the individual risk components
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK <- 
        OSIM.ConditionOccurrenceValidation$SIMULATED_COND_AGE_ATTRIB_RISK +
          OSIM.ConditionOccurrenceValidation$SIMULATED_COND_GENDER_ATTRIB_RISK +
            OSIM.ConditionOccurrenceValidation$SIMULATED_COND_RACE_ATTRIB_RISK +
              OSIM.ConditionOccurrenceValidation$SIMULATED_COND_CONFOUND_RISK +
                OSIM.Conditions$CONDITION_PREVALENCE
      
                                        #	 Now factor in Preventative Drug/conditions
      tmpDrugConditionRisk <- merge(OSIM.DrugsTaken, OSIM.DrugOutcomes)
      
      tmpDrugConditionRisk <- merge(tmpDrugConditionRisk, OSIM.ConditionOccurrenceValidation,
                                    by.x="CONDITION_ID", by.y="SIMULATED_CONDITION_CONCEPT_CODE")
      
      tmpDrugConditionRisk <- merge(tmpDrugConditionRisk, OSIM.Conditions)
      
      tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK <-
        ifelse(tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Drug preventative effect",
               as.vector(secondaryDistribution(tmpDrugConditionRisk, 
                                               Col="DRUG_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                               Dist=DrugOutcomeRiskType,BPCol="CONDITION_PREVALENCE")),
               ifelse(tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
                      as.vector(secondaryDistribution(tmpDrugConditionRisk, 
                                                      Col="DRUG_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                                      Dist=DrugOutcomeConstantRiskAttrRisk,BPCol="CONDITION_PREVALENCE")),
                      ifelse(tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK_TYPE=="Constant risk",
                             as.vector(secondaryDistribution(tmpDrugConditionRisk, 
                                                             Col="DRUG_OUTCOME_ATTRIB_RISK_CATEGORY", 
                                                             Dist=DrugOutcomeConstantRiskAttrRisk,BPCol="CONDITION_PREVALENCE")),
                             0
                             )
                      )
               )
      
                                        #	Select negative outcome attributable risk
      tmpDrugConditionRisk <- tmpDrugConditionRisk[
                                                   which(tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK<0),]
      
                                        #	Sum all preventative drug effects for each drug taken
      tmpPreventativeSums <- 
        tapply(tmpDrugConditionRisk$DRUG_OUTCOME_ATTRIB_RISK, 
               tmpDrugConditionRisk$CONDITION_ID, sum)
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_DRUG_ATTRIB_RISK[
                                                                    as.numeric(names(tmpPreventativeSums))] <- as.vector(tmpPreventativeSums)
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK <-
        OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK +
          OSIM.ConditionOccurrenceValidation$SIMULATED_DRUG_ATTRIB_RISK
      
                                        #	 Now factor in Preventative Indication/Conditions	
      tmpIndicationConditionRisk <- merge(OSIM.Indication, OSIM.IndicationOutcomes,
                                          by.x="CONDITION_CONCEPT_ID", by.y="INDICATION_ID")
      
      tmpIndicationConditionRisk <- merge(tmpIndicationConditionRisk, OSIM.ConditionOccurrenceValidation,
                                          by.x="CONDITION_ID", by.y="SIMULATED_CONDITION_CONCEPT_CODE")
      
      tmpIndicationConditionRisk <- merge(tmpIndicationConditionRisk, OSIM.Conditions)
      
      tmpIndicationConditionRisk$IND_OUTCOME_ATTRIB_RISK <-
        secondaryDistribution(tmpIndicationConditionRisk, Col="IND_OUTCOME_ATTRIB_RISK_CATEGORY", 
                              Dist=IndOutcomeAttrRisk,BPCol="CONDITION_PREVALENCE")
      
                                        #	Select negative indication attributable risk
      tmpIndicationConditionRisk <- tmpIndicationConditionRisk[
                                                               which(tmpIndicationConditionRisk$IND_OUTCOME_ATTRIB_RISK<0),]
      
                                        #	Sum all preventative drug effects for each condition
      tmpPreventativeSums <- 
        tapply(tmpIndicationConditionRisk$IND_OUTCOME_ATTRIB_RISK, 
               tmpIndicationConditionRisk$CONDITION_ID, sum)
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_IND_ATTRIB_RISK[
                                                                   as.numeric(names(tmpPreventativeSums))] <- as.vector(tmpPreventativeSums)
      
                                        #	Add the (negative) preventative risks to the combined risk
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK <-
        OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK +
          OSIM.ConditionOccurrenceValidation$SIMULATED_IND_ATTRIB_RISK

                                        #	Convert Rate into Probability
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY <- 
        1 - exp(-OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_COMBINED_RISK *
                (OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson] - 
                 OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson]))

                                        #	Change negative combined risk probabilities to 0
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY <-
        ifelse( OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY < 0,
               0,
               OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY)
      
                                        # If small set and validation mode... output entire condition occurance numbers
      if (validationMode & ((conditionCount * drugCount) < 100000)) {
        condFileAppend <- (thisPerson > 1) 
        condFileHeaders <- (fileHeader && ! condFileAppend)
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_VALID_ALL_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        write.table(OSIM.ConditionOccurrenceValidation, file=filename, 
                    row.names=FALSE, col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }		
      
                                        #	Which are actual conditions?
      OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION <- 
        runif(n,0,1) < 
          OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_INITIAL_PROBABILITY
      
                                        #	Which Conditions are recorded (actual or false)?
      OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_RECORD <-
        ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION, 
               runif(n,0,1) < OSIM.Conditions$CONDITION_SENSITIVITY,
               runif(n,0,1) < (( 1 - OSIM.Conditions$CONDITION_SPECIFICITY ) *
                               OSIM.Conditions$CONDITION_PREVALENCE))
      
      tmpKeepCondition <- 
        OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION | 
      OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_RECORD
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES <-
        ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_RECORD,
               ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION,
                      secondaryDistribution(OSIM.Conditions, Col="CONDITION_OCCURRENCE_CATEGORY", 
                                            Dist=CondOccurrence, ResultType="discrete" ),
                      1),
               0)
      
                                        #	Truncate to only actual and/or recorded Conditions
      OSIM.ConditionOccurrenceValidation <-
        OSIM.ConditionOccurrenceValidation[which(tmpKeepCondition),]
      
      n <- nrow(OSIM.ConditionOccurrenceValidation)
      
      
                                        #	Generate a row per Condition Occurrence data frame
      n <- sum(OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES) +
        length(OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES[
                                                                                      which(OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES==0)])
      
      tmpDF <- data.frame(
                          SIMULATED_CONDITION_OCCURRENCE_ID=rep("",n))

      
                                        #	Create a temp Condition Occurrence Row for each Occurrence
      tmpDF$SIMULATED_CONDITION_OCCURRENCE_ID <- 
        rep(OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_OCCURRENCE_ID,
            ifelse((OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES==0),
                   1,
                   OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_NUM_OCCURRENCES))
      
                                        #	Merge (INNER JOIN) with original Exposure Data Frame by original Exposure ID
      OSIM.ConditionOccurrenceValidation <- 
        merge(tmpDF,OSIM.ConditionOccurrenceValidation, by=c("SIMULATED_CONDITION_OCCURRENCE_ID"))
      
      n <- nrow(OSIM.ConditionOccurrenceValidation)
      
                                        # Renumber
      if (n > 0) {
        OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_OCCURRENCE_ID <-
          thisPersonID * 100000 + (THIS.PERSON.CONDITION.SEED:(THIS.PERSON.CONDITION.SEED+n-1))
        
        THIS.PERSON.CONDITION.SEED <- THIS.PERSON.CONDITION.SEED + n	
      }
      
      OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_START_DATE <-
        ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_RECORD,
               runif(n,
                     OSIM.ObservationPeriodCalcs$MIN_DATE[thisPerson],
                     OSIM.ObservationPeriodCalcs$MAX_DATE[thisPerson]),
               NA)
      
      
                                        #	1 - Has Recorded condition within Observation Period
                                        #	2 - Has Unrecorded Condition
                                        #	3 - Has Recorded Condition, not within Observation Period
                                        #	4 - Falsely Recorded Condition within Observation Period
                                        #	5 - Falsely Recorded Condition not within Observation Period
      OSIM.ConditionOccurrenceValidation$CONDITION_RECORDING_TYPE <-
        ifelse( (OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_RECORD),
               ifelse(((OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_START_DATE < 
                        rep(OSIM.ObservationPeriodCalcs$MIN_OBS_DATE[thisPerson],
                            n)) |
                       (OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_START_DATE >
                        rep(OSIM.ObservationPeriodCalcs$MAX_OBS_DATE[thisPerson],
                            n))),
                      ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION,
                             3,
                             5),
                      ifelse(OSIM.ConditionOccurrenceValidation$SIMULATED_HAS_CONDITION,
                             1,
                             4)),
               2)
      
      tmpRecord <- which((OSIM.ConditionOccurrenceValidation$CONDITION_RECORDING_TYPE == 1) |
                         (OSIM.ConditionOccurrenceValidation$CONDITION_RECORDING_TYPE == 4))
      
      n <- length(tmpRecord)
      
      OSIM.ConditionOccurrence <- data.frame(
                                             CONDITION_OCCURRENCE_ID=rep(0,n),
                                             CONDITION_START_DATE=rep(0,n),
                                             PERSON_ID=rep(thisPersonID,n),
                                             CONDITION_END_DATE=rep(NA,n),
                                             CONDITION_OCCUR_TYPE=rep(NA,n),
                                             CONDITION_CONCEPT_ID=rep(0,n),
                                             STOP_REASON=rep(NA,n),
                                             DX_QUALIFIER=rep(NA,n),
                                             SOURCE_CONDITION_CODE=rep(NA,n))
      
      if (n > 0) {
        OSIM.ConditionOccurrence$CONDITION_OCCURRENCE_ID <- 
          OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_OCCURRENCE_ID[tmpRecord]
        OSIM.ConditionOccurrence$CONDITION_CONCEPT_ID <-
          OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_CONCEPT_CODE[tmpRecord]
        OSIM.ConditionOccurrence$CONDITION_START_DATE <-
          yearFloat2CDMdate(
                            OSIM.ConditionOccurrenceValidation$SIMULATED_CONDITION_START_DATE[tmpRecord])
      }	
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Conditions
                                        #------------------------------------------------------------------
      condFileAppend <- TRUE
      condFileHeaders <- FALSE
      filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                        "_", fileModifier, "_", fileDistNumber, ".txt", sep="")
      OSIM.ConditionOccurrence=cbind(A_TYPE=rep(0, nrow(OSIM.ConditionOccurrence)), OSIM.ConditionOccurrence)
      write.table(OSIM.ConditionOccurrence, file=filename, row.names=FALSE, 
                  col.names=condFileHeaders, 
                  sep="\t", na="", quote=FALSE,  append=condFileAppend)
      if (! OSIM.DEBUG.MODE) { rm(OSIM.ConditionOccurrence) }
      
                                        #------------------------------------------------------------------
                                        #	Write the Simulated Conditions Validation File
                                        #------------------------------------------------------------------
      if (validationMode) {
        filename <- paste(osim.table.path, OSIM.CONDITIONOCCURRENCE.FILENAME, 
                          "_VALID_", fileModifier, "_", fileDistNumber, ".txt", sep="")
        OSIM.ConditionOccurrenceValidation=cbind(A_TYPE=rep(0, nrow(OSIM.ConditionOccurrenceValidation)), OSIM.ConditionOccurrenceValidation)
        write.table(OSIM.ConditionOccurrenceValidation, file=filename, 
                    row.names=FALSE, col.names=condFileHeaders, 
                    sep="\t", na="", quote=FALSE,  append=condFileAppend)
      }
      if (! OSIM.DEBUG.MODE) { rm(OSIM.ConditionOccurrenceValidation) }
      
      if (((thisPerson-currentPerson+1) %% 10000) == 0 ) {
        logMessage(paste("   Thru Person",thisPersonID,"processed.",sep=" "))
      }

    }	#	End Sim Person Loop
    
    logMessage(paste("  ",thisPassPersonCount,"More Persons processed.",sep=" "))
    currentPerson <- currentPerson + thisPassPersonCount
  }
  logMessage(paste("   All (",personCount,") Persons processed.",sep=""))
  
  logMessage("-----------------------------------------------------------------------")
  logMessage("-- END generateSimulatedPersons")
  logMessage("-----------------------------------------------------------------------")
  
} 	#	End Creating Simulated Persons

                                        #------------------------------------------------------------------------------
                                        #	OSIM.Module1:  Generate Simulation Attribute Tables
                                        #
                                        #	The main purpose of Module 1 is to generate the Drugs, Conditions, and 
                                        #	their associated attributes and characteristics based on the input 
                                        #	probability distributions.  The Simulation Attribute Tables record the 
                                        #	relationships and characteristics between drugs, outcomes, and confounding 
                                        #	factors that will be used to create the Simulate Persons.  Therefore, 
                                        #	Simulation Attribute Tables can provide the “answer key” for evaluating 
                                        #	the performance of a particular analytic method. 
                                        #
OSIM.Module1 <- function() {
  Housekeeping(1)
  generateSimulatedConditions()
  generateSimulatedDrugsIndications()
  generateSimulatedDrugOutcomes()
  generateSimulatedIndicationOutcomes()
}

                                        #------------------------------------------------------------------------------
                                        #	OSIM.Module2:  Generate Simulated Persons
                                        #
                                        #	The main purpose of Module 2 is to generate the Simulated Persons, 
                                        #	including their Drug Exposures, Condition Occurrences, and Additional 
                                        #	Outcomes due to Indications or Drugs.  Generation of Simulated Persons 
                                        #	uses the Drugs and Conditions and their associated attributes that were 
                                        #	recorded during Module 1.   There are four output files produced in a 
                                        #	standard run of Module 2.  If the validationMode parameter is set to 
                                        #	True, four additional files are produced, that can be used to validate 
                                        #	the contents and characteristics of the Simulated Person Data.
                                        #
                                        # 	For effiency and date frame reuse, all Module2 functions described in
                                        #	the Process Design Document are combined in the first function.
                                        #
OSIM.Module2 <- function() {
  Housekeeping(2)
  generateSimulatedPersons()
                                        #generateSimulatedObservationPeriod()
                                        #generateDrugExposures()
                                        #generateOutcomes()
                                        #generateSimulatedConditionOccurrences()
}

main <- function() {
  getExecParms()
  if (validationMode) { set.seed(OSIM.VALIDATION.SEED) } # Set a seed for consistant validation output
  if (createSimTables) { OSIM.Module1() }
  if (createSimPersons) { OSIM.Module2() }
  logMessage("Processing Complete")
}
