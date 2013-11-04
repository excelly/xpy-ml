person_config_default='''DistName	Category	Prob	Rule	Lower	Upper	Mean	StDev	Const	Factor	minCut	maxCut	xBP	CatValue
PersonAge	0-10	0.104	unif	0	10								
PersonAge	10-20	0.145	unif	10	20								
PersonAge	20-30	0.161	unif	20	30								
PersonAge	30-40	0.145	unif	30	40								
PersonAge	40-50	0.156	unif	40	50								
PersonAge	50-60	0.144	unif	50	60								
PersonAge	60-70	0.089	unif	60	70								
PersonAge	70-80	0.032	unif	70	80								
PersonAge	80-100	0.023	unif	80	100								
PersonAgeRecorded	AgeMissing	0.05	const					0					
PersonAgeRecorded	AgeRecorded	0.95	const					1					
PersonGender	Male	0.491											
PersonGender	Female	0.509											
PersonGenderRecorded	GenderMissing	0.05	const					0					
PersonGenderRecorded	GenderRecorded	0.95	const					1					
PersonRace	White	0.75						
PersonRace	Non-white	0.25						
PersonRaceRecorded	RaceMissing	0.8	const					0
PersonRaceRecorded	RaceRecorded	0.2	const					1
PersonConfounder	Confounder	0.3	const					0
PersonConfounder	No confounder	0.7	const					1
PersonAgeAtDeath	DeathAge	1	norm	1	100	79	10	'''

cond_config_default='''
CondBaselinePrevalence	0%-0.001%	0.195	unif	0	0.00001			
CondBaselinePrevalence	0.001%-0.01%	0.317	unif	0.00001	0.0001			
CondBaselinePrevalence	0.01%-0.1%	0.294	unif	0.0001	0.001			
CondBaselinePrevalence	0.1%-1%	0.158	unif	0.001	0.01			
CondBaselinePrevalence	1%-10%	0.035	norm	0.01	0.1	0.0236	0.0166	
CondAttrRiskAge	No age effect	0.5	const					0					
CondAttrRiskAge	Older	0.2	cont						0.01			y	
CondAttrRiskAge	Younger	0.2	cont						-0.01			y	
CondAttrRiskAge	>50 only	0.05	cont						-1		50	y	
CondAttrRiskAge	<12 only	0.05	cont						-1	12		y	
CondAttrRiskGender	No effect	0.5	const					0					
CondAttrRiskGender	More male	0.2	cat	0	2							y	Male
CondAttrRiskGender	More female	0.2	cat	0	2							y	Female
CondAttrRiskGender	Only male	0.05	cat	-1	-1							y	Female
CondAttrRiskGender	Only female	0.05	cat	-1	-1							y	Male
CondAttrRiskRace	No effect	0.8	const					0					
CondAttrRiskRace	More white	0.05	cat	0	2							y	White
CondAttrRiskRace	More other	0.15	cat	0	2							y	Non-white
CondConfounderRisk	No effect	0.8	const					0					
CondConfounderRisk	More confounder	0.1	cat	0	1							y	Confounder
CondConfounderRisk	Less confounder	0.1	cat	0	1							y	No confounder
CondSensitivity	0%-10%	0.1	unif	0	0.1			
CondSensitivity	10%-25%	0.1	unif	0.1	0.25			
CondSensitivity	25%-50%	0.1	unif	0.25	0.5			
CondSensitivity	50%-75%	0.1	unif	0.5	0.75			
CondSensitivity	75%-99%	0.1	unif	0.75	0.99			
CondSensitivity	100%	0.5	const					1
CondSpecificity	90%-95%	0.1	unif	0.9	0.95			
CondSpecificity	95%-99%	0.1	unif	0.95	0.99			
CondSpecificity	100%	0.8	const	 				1
CondOccurrence	1	0.909	norm	1	18.05	1	0.85	
CondOccurrence	2	0.072	norm	1	35.23	2	2.75	
CondOccurrence	3+	0.019	norm	1	46.17	3.25	4.18	'''

# higher baseline, no other risk, precise recording, single occurrence only
cond_config_alt='''
CondBaselinePrevalence	0%-0.001%	0	unif	0	0.00001			
CondBaselinePrevalence	0.001%-0.01%	0.1	unif	0.00001	0.0001			
CondBaselinePrevalence	0.01%-0.1%	0.3	unif	0.0001	0.001			
CondBaselinePrevalence	0.1%-1%	0.3	unif	0.001	0.01			
CondBaselinePrevalence	1%-10%	0.3	norm	0.01	0.1	0.0236	0.0166	
CondAttrRiskAge	No age effect	1	const					0					
CondAttrRiskAge	Older	0	cont						0.01			y	
CondAttrRiskAge	Younger	0	cont						-0.01			y	
CondAttrRiskAge	>50 only	0	cont						-1		50	y	
CondAttrRiskAge	<12 only	0	cont						-1	12		y	
CondAttrRiskGender	No effect	1	const					0					
CondAttrRiskGender	More male	0	cat	0	2							y	Male
CondAttrRiskGender	More female	0	cat	0	2							y	Female
CondAttrRiskGender	Only male	0	cat	-1	-1							y	Female
CondAttrRiskGender	Only female	0	cat	-1	-1							y	Male
CondAttrRiskRace	No effect	1	const					0					
CondAttrRiskRace	More white	0	cat	0	2							y	White
CondAttrRiskRace	More other	0	cat	0	2							y	Non-white
CondConfounderRisk	No effect	1	const					0					
CondConfounderRisk	More confounder	0	cat	0	1							y	Confounder
CondConfounderRisk	Less confounder	0	cat	0	1							y	No confounder
CondSensitivity	0%-10%	0	unif	0	0.1			
CondSensitivity	10%-25%	0	unif	0.1	0.25			
CondSensitivity	25%-50%	0	unif	0.25	0.5			
CondSensitivity	50%-75%	0	unif	0.5	0.75			
CondSensitivity	75%-99%	0	unif	0.75	0.99			
CondSensitivity	100%	1	const					1
CondSpecificity	90%-95%	0	unif	0.9	0.95			
CondSpecificity	95%-99%	0	unif	0.95	0.99			
CondSpecificity	100%	1	const	 				1
CondOccurrence	1	1	norm	1	18.05	1	0.85	
CondOccurrence	2	0	norm	1	35.23	2	2.75	
CondOccurrence	3+	0	norm	1	46.17	3.25	4.18	'''

ob_config_default='''
ObservationPeriod	0-12	0.41	unif	0	12			
ObservationPeriod	13-36	0.305	unif	13	36			
ObservationPeriod	37-60	0.199	unif	37	60			
ObservationPeriod	61-100	0.086	unif	61	100			'''

# longer minimum length
ob_config_alt='''
ObservationPeriod	6-12	0.41	unif	6	12			
ObservationPeriod	13-36	0.305	unif	13	36			
ObservationPeriod	37-60	0.199	unif	37	60			
ObservationPeriod	61-100	0.086	unif	61	100			'''

drug_config_default='''
DrugBaselinePrevalence	0%-0.001%	0.559	norm	0	0.00001	0.000002	0.000002	
DrugBaselinePrevalence	0.001%-0.01%	0.221	unif	0.00001	0.0001			
DrugBaselinePrevalence	0.01%-0.1%	0.143	unif	0.0001	0.001			
DrugBaselinePrevalence	0.1%-1%	0.068	unif	0.001	0.01			
DrugBaselinePrevalence	1%-10%	0.009	norm	0.01	0.1	0.0223	0.0175						
DrugAttrRiskAge	No effect	0.5	const					0					
DrugAttrRiskAge	Older	0.2	cont						0.01			y	
DrugAttrRiskAge	Younger	0.2	cont						-0.01			y	
DrugAttrRiskAge	>50 only	0.05	cont						-1		50	y	
DrugAttrRiskAge	<12 only	0.05	cont						-1	12		y	
DrugAttrRiskGender	No effect	0.5	const					0					
DrugAttrRiskGender	More male	0.2	cat	0	2							y	Male
DrugAttrRiskGender	More female	0.2	cat	0	2							y	Female
DrugAttrRiskGender	Only male	0.05	cat	-1	-1							y	Female
DrugAttrRiskGender	Only female	0.05	cat	-1	-1							y	Male
DrugAttrRiskRace	No effect	0.8	const					0					
DrugAttrRiskRace	More white	0.1	cat	0	2							y	White
DrugAttrRiskRace	More other	0.1	cat	0	2							y	Non-white
DrugConfounderRisk	No effect	0.8	const					0					
DrugConfounderRisk	More confounder	0.1	cat	0	1							y	Confounder
DrugConfounderRisk	Less confounder	0.1	cat	0	1							y	No confounder
DrugSensitivity	0%-10%	0.1	unif	0	0.1								
DrugSensitivity	10%-25%	0.1	unif	0.1	0.25								
DrugSensitivity	25%-50%	0.1	unif	0.25	0.5								
DrugSensitivity	50%-75%	0.1	unif	0.5	0.75								
DrugSensitivity	75%-99%	0.1	unif	0.75	0.99								
DrugSensitivity	100%	0.5	const					1					
DrugSpecificity	90%-95%	0.1	unif	0.9	0.95								
DrugSpecificity	95%-99%	0.1	unif	0.95	0.99								
DrugSpecificity	100%	0.8	const					1					'''

# more_drug, no other risk, precise recording, 
drug_config_alt='''
DrugBaselinePrevalence	0%-0.001%	0.2	norm	0	0.00001	0.000002	0.000002	
DrugBaselinePrevalence	0.001%-0.01%	0.2	unif	0.00001	0.0001			
DrugBaselinePrevalence	0.01%-0.1%	0.5	unif	0.0001	0.001			
DrugBaselinePrevalence	0.1%-1%	0.09	unif	0.001	0.01			
DrugBaselinePrevalence	1%-10%	0.01	norm	0.01	0.1	0.0223	0.0175						
DrugAttrRiskAge	No effect	1	const					0					
DrugAttrRiskAge	Older	0	cont						0.01			y	
DrugAttrRiskAge	Younger	0	cont						-0.01			y	
DrugAttrRiskAge	>50 only	0	cont						-1		50	y	
DrugAttrRiskAge	<12 only	0	cont						-1	12		y	
DrugAttrRiskGender	No effect	1	const					0					
DrugAttrRiskGender	More male	0	cat	0	2							y	Male
DrugAttrRiskGender	More female	0	cat	0	2							y	Female
DrugAttrRiskGender	Only male	0	cat	-1	-1							y	Female
DrugAttrRiskGender	Only female	0	cat	-1	-1							y	Male
DrugAttrRiskRace	No effect	1	const					0					
DrugAttrRiskRace	More white	0	cat	0	2							y	White
DrugAttrRiskRace	More other	0	cat	0	2							y	Non-white
DrugConfounderRisk	No effect	1	const					0					
DrugConfounderRisk	More confounder	0	cat	0	1							y	Confounder
DrugConfounderRisk	Less confounder	0	cat	0	1							y	No confounder
DrugSensitivity	0%-10%	0	unif	0	0.1								
DrugSensitivity	10%-25%	0	unif	0.1	0.25								
DrugSensitivity	25%-50%	0	unif	0.25	0.5								
DrugSensitivity	50%-75%	0	unif	0.5	0.75								
DrugSensitivity	75%-99%	0	unif	0.75	0.99								
DrugSensitivity	100%	1	const					1					
DrugSpecificity	90%-95%	0	unif	0.9	0.95								
DrugSpecificity	95%-99%	0	unif	0.95	0.99								
DrugSpecificity	100%	1	const					1					'''

drug_exposure_config_default='''
DrugExposureLength	0-7	0.063	norm	1	93	5	6						
DrugExposureLength	7-14	0.212	norm	3	284	11	12						
DrugExposureLength	14-30	0.3	norm	5	513	22	28						
DrugExposureLength	30-90	0.224	norm	7	1032	55	82						
DrugExposureLength	90-180	0.119	norm	6	1682	130	182						
DrugExposureLength	>180	0.082	norm	5	2507	240	311						
DrugNumExposures	1	0.926	norm	1	9.28	1	0.74					
DrugNumExposures	2	0.057	norm	1.07	20.12	2	2.29					
DrugNumExposures	3+	0.017	norm	1.88	20.14	3.71	3.52					'''

# longer exposure, single exposure only
drug_exposure_config_alt='''
DrugExposureLength	0-7	0	norm	1	93	5	6						
DrugExposureLength	7-14	0.25	norm	3	284	11	12						
DrugExposureLength	14-30	0.3	norm	5	513	22	28						
DrugExposureLength	30-90	0.25	norm	7	1032	55	82						
DrugExposureLength	90-180	0.1	norm	6	1682	130	182						
DrugExposureLength	>180	0.1	norm	5	2507	240	311						
DrugNumExposures	1	1	norm	1	9.28	1	0.74					
DrugNumExposures	2	0	norm	1.07	20.12	2	2.29					
DrugNumExposures	3+	0	norm	1.88	20.14	3.71	3.52					'''

drug_outcome_config_default='''
DrugOutcomeRiskType	Drug preventative effect	0.002	cat	-1	0							y
DrugOutcomeRiskType	No effect	0.98	omit									
DrugOutcomeRiskType	Constant risk	0.009										
DrugOutcomeRiskType	Constant rate	0.009										
DrugOutcomeConstantRateOnset	Acute: 0-7 days	0	unif	0	7							
DrugOutcomeConstantRateOnset	Insidious: 0-E	0.9	duration									
DrugOutcomeConstantRateOnset	Delayed: 365-3650 days	0.1	unif	365	3650							
DrugOutcomeConstantRiskOnset	Acute: 0-7 days	0.5	unif	0	7							
DrugOutcomeConstantRiskOnset	Insidious: 0-E	0.4	duration									
DrugOutcomeConstantRiskOnset	Delayed: 365-3650 days	0.1	unif	365	3650							
DrugOutcomeConstantRateAttrRisk	Small drug effect	0.667	cat	0	0.5							y
DrugOutcomeConstantRateAttrRisk	Moderate drug effect	0.278	cat	0.5	1							y
DrugOutcomeConstantRateAttrRisk	Large drug effect	0.055	cat	1	10							y
DrugOutcomeConstantRiskAttrRisk	Small drug effect	0.667	cat	0	0.5							y
DrugOutcomeConstantRiskAttrRisk	Moderate drug effect	0.278	cat	0.5	1							y
DrugOutcomeConstantRiskAttrRisk	Large drug effect	0.055	cat	1	10							y'''

# more and large effect
drug_outcome_config_alt='''
DrugOutcomeRiskType	Drug preventative effect	0.002	cat	-1	0							y
DrugOutcomeRiskType	No effect	0.9	omit									
DrugOutcomeRiskType	Constant risk	0.049										
DrugOutcomeRiskType	Constant rate	0.049										
DrugOutcomeConstantRateOnset	Acute: 0-7 days	0	unif	0	7							
DrugOutcomeConstantRateOnset	Insidious: 0-E	0.9	duration									
DrugOutcomeConstantRateOnset	Delayed: 365-3650 days	0.1	unif	365	3650							
DrugOutcomeConstantRiskOnset	Acute: 0-7 days	0.5	unif	0	7							
DrugOutcomeConstantRiskOnset	Insidious: 0-E	0.4	duration									
DrugOutcomeConstantRiskOnset	Delayed: 365-3650 days	0.1	unif	365	3650							
DrugOutcomeConstantRateAttrRisk	Small drug effect	0.2	cat	1	5							y
DrugOutcomeConstantRateAttrRisk	Moderate drug effect	0.5	cat	5	10							y
DrugOutcomeConstantRateAttrRisk	Large drug effect	0.3	cat	10	20							y
DrugOutcomeConstantRiskAttrRisk	Small drug effect	0.2	cat	1	5							y
DrugOutcomeConstantRiskAttrRisk	Moderate drug effect	0.5	cat	5	10							y
DrugOutcomeConstantRiskAttrRisk	Large drug effect	0.3	cat	10	20							y'''

ind_config_default='''
DrugPriorIndication	0	0.1	const					0				
DrugPriorIndication	1%-75%	0.25	unif	0.01	0.75							
DrugPriorIndication	75%-99%	0.25	unif	0.75	0.99							
DrugPriorIndication	100%	0.4	const					1				
DrugsPerIndication	1	0.25	const					1				
DrugsPerIndication	2	0.25	const					2				
DrugsPerIndication	3-10	0.25	unif	3	10							
DrugsPerIndication	11-50	0.25	unif	11	50							
IndOutcomeAttrRisk	>2x more outcomes	0.01	cat	1	3							y
IndOutcomeAttrRisk	1-2x more outcomes	0.04	cat	0	1							y
IndOutcomeAttrRisk	No effect	0.9	omit									
IndOutcomeAttrRisk	Fewer outcomes	0.05	cat	-1	0							
IndStartDate	Before first exposure	0.25	unif	-3650	0							
IndStartDate	Within 30 days prior	0.25	unif	-30	0			
IndStartDate	Day of first exposure	0.2	const					0
IndStartDate	Within 30 days after	0.15	unif	0	30			
IndStartDate	After first exposure	0.15	unif	0	3650			'''

# no indications outcome
ind_config_alt='''
DrugPriorIndication	0	0.1	const					0				
DrugPriorIndication	1%-75%	0.25	unif	0.01	0.75							
DrugPriorIndication	75%-99%	0.25	unif	0.75	0.99							
DrugPriorIndication	100%	0.4	const					1				
DrugsPerIndication	1	0.25	const					1				
DrugsPerIndication	2	0.25	const					2				
DrugsPerIndication	3-10	0.25	unif	3	10							
DrugsPerIndication	11-50	0.25	unif	11	50							
IndOutcomeAttrRisk	>2x more outcomes	0	cat	1	3							y
IndOutcomeAttrRisk	1-2x more outcomes	0	cat	0	1							y
IndOutcomeAttrRisk	No effect	1	omit									
IndOutcomeAttrRisk	Fewer outcomes	0	cat	-1	0							y
IndStartDate	Before first exposure	0.25	unif	-3650	0							
IndStartDate	Within 30 days prior	0.25	unif	-30	0			
IndStartDate	Day of first exposure	0.2	const					0
IndStartDate	Within 30 days after	0.15	unif	0	30			
IndStartDate	After first exposure	0.15	unif	0	3650			'''
