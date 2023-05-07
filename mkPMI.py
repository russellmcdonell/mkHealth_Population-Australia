'''
A script to create a CSV file of randomly created patient records

SYNOPSIS
$ python mkPMI.py [-M PMIoutputfile|--PMIfile=PMIoutputfile] [-A addressFile|--addressFile=addressFile]
                  [-r|--makeRandom] [-b|-both] [-a|alias2alias] [-m|-merge2merge] [-i|--IHI] [-x|--extendNames] [-e|--errors] [-v loggingLevel|--loggingLevel=loggingLevel] [-o logfile|--logfile=logfile]

OPTIONS
-M PMIoutputfile|--PMIfile=PMIoutputfile
The PMI output file to be created. Default = master.csv

-A addressFile|--addressFile=addressFile
The file of GNAF_CORE addresses (or subset)

-r|--makeRandom
Make random Australian addresses

-b|--both
PMI records can be both Alias records and Merged records

-a|--alias2alias
PMI records can be Aliases of Alias records

-m|--merge2merge
PMI records can be Merges to already Merged records

-i|--IHI
Add Australian IHI number

-x|--extendNames
Extend names with sequential letters

-e|--errors
Create errors, such as duplicate UR records, merged and aliases that point to non-existent records or point to deleted records.

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want.

-o logfile|--logfile=logfile
The name of a logginf file where you want all messages captured.
'''

import sys
import csv
import io
import argparse
import logging
import configparser
import random
import datetime
import re
from names import nicknames
from randPatients import patients, patientKeys, mkRandPatients, selectFamilyName, selectBoysname, selectGirlsname

def clone(me, other) :
	'''
Clone other onto me
	'''
# namely: familyName,givenName,birthdate,sex,streetNo,streetName,streetType,suburb,state,postcode,longitude,latitude,country,mobile,homePhone,businessPhone,email,medicareNo,IHI,dvaNo,dvaType,height,weight,waist,hips,married,race,deathDate

	cloneInfo = ''
	patients[me]['familyName'] = patients[other]['familyName']
	patients[me]['givenName'] = patients[other]['givenName']
	if random.random() < 0.2 :				# Sometimes the birthdate is wrong
		(year, month, day) = patients[other]['birthdate'].split('-')
		year = int(year)
		month = int(month)
		day = int(day)
		birthdate = datetime.date(year, month, day)
		if random.random() < 0.4 :				# Sometimes the year is wrong
			birthdate += datetime.timedelta(days=365)*(int(random.random()*5.0) - 2)
		if random.random() < 0.3 :				# Sometimes the month is wrong
			birthdate += datetime.timedelta(days=31)*(int(random.random()*5.0) - 2)
		if random.random() < 0.3 :				# Sometimes the day is wrong
			birthdate += datetime.timedelta(days=1)*(int(random.random()*5.0) - 2)
		if birthdate < datetime.date.today() :
			patients[me]['birthdate'] = birthdate.isoformat()
	else :
		cloneInfo = 'bd'
		patients[me]['birthdate'] = patients[other]['birthdate']
	patients[me]['sex'] = patients[other]['sex']
	if cloneInfo == '' :
		cloneInfo = 'sex'
	else :
		cloneInfo += ',sex'
	if random.random() < 0.8 :				# Often the address is correct
		if cloneInfo == '' :
			cloneInfo = 'addr'
		else :
			cloneInfo += ',addr'
		patients[me]['streetNo'] = patients[other]['streetNo']
		patients[me]['streetName'] = patients[other]['streetName']
		patients[me]['streetType'] = patients[other]['streetType']
		patients[me]['shortStreetType'] = patients[other]['shortStreetType']
		patients[me]['suburb'] = patients[other]['suburb']
		patients[me]['state'] = patients[other]['state']
		patients[me]['postcode'] = patients[other]['postcode']
		patients[me]['longitude'] = patients[other]['longitude']
		patients[me]['latitude'] = patients[other]['latitude']
		patients[me]['country'] = patients[other]['country']
	if random.random() < 0.2 :				# Sometimes the phone numbers are wrong
		if cloneInfo == '' :
			cloneInfo = 'ph'
		else :
			cloneInfo += ',ph'
		patients[me]['mobile'] = patients[other]['mobile']
		patients[me]['homePhone'] = patients[other]['homePhone']
		patients[me]['businessPhone'] = patients[other]['businessPhone']
		patients[me]['email'] = patients[other]['email']
	patients[me]['mobile'] = patients[other]['mobile']
	patients[me]['homePhone'] = patients[other]['homePhone']
	patients[me]['businessPhone'] = patients[other]['businessPhone']
	patients[me]['email'] = patients[other]['email']
	if IHI :
		if cloneInfo == '' :
			cloneInfo = 'IHI'
		else :
			cloneInfo += ',IHI'
		patients[me]['IHI'] = patients[other]['IHI']
	patients[me]['medicareNo'] = patients[other]['medicareNo']
	patients[me]['dvaNo'] = patients[other]['dvaNo']
	patients[me]['dvaType'] = patients[other]['dvaType']
	height = float(patients[other]['height'])
	patients[me]['height'] = '%.0f' % random.normalvariate(height, height/50.0)
	oldWeight = float(patients[other]['weight'])
	weight = random.normalvariate(oldWeight, oldWeight/20.0)
	patients[me]['weight'] = '%.1f' % (weight)
	waist = height * 0.49					# a ratio for all ages, both genders for normal, health persons
	waist = waist * (weight/oldWeight)	# scaled by the percentage weight percentage
	if patients[me]['sex'] == 'M' :
		hips = waist / random.normalvariate(0.90, 0.10)
	else :
		hips = waist / random.normalvariate(0.75, 0.10)
	patients[me]['hips'] = hips
	patients[me]['race'] = patients[other]['race']
	patients[me]['married'] = patients[other]['married']
	patients[me]['deathDate'] = patients[other]['deathDate']
	return ('name,' + cloneInfo)



def mkLuhn(card) :
	sum = 0
	for i in (range(len(card) - 1, -1, -2)) :
		digit = int(card[i]) * 2
		sum += int(digit / 10)
		sum += digit  % 10
	for i in (range(len(card) - 2, -1, -2)) :
		sum += int(card[i])
	return((sum * 9) % 10)


def csvString(row) :

	si = io.StringIO()
	cw = csv.writer(si)
	cw.writerow(row)
	return si.getvalue().rstrip('\r\n')



if __name__ == '__main__' :
	'''
The main code
	'''

	# Save the program name
	progName = sys.argv[0]
	progName = progName[0:-3]		# Strip off the .py ending

	parser = argparse.ArgumentParser()
	parser.add_argument ('-M', '--PMIoutputfile', metavar='PMIoutputfile', dest='PMIoutputfile', default='master.csv', help='The name of the PMI csv file to be created')
	parser.add_argument ('-A', '--addressFile', metavar='addressFile', dest='addressFile', default='GNAF_CORE.psv', help='The file of GNAF_CORE addresses (or subset)')
	parser.add_argument ('-r', '--makeRandom', dest='makeRandom', action='store_true', help='Make random Australian addresses')
	parser.add_argument ('-b', '--both', dest='both', action='store_true', help='PMI records can be both merged and an alias')
	parser.add_argument ('-a', '--alias2alias', dest='alias2alias', action='store_true', help='Allow aliases to aliased or merged patient')
	parser.add_argument ('-m', '--merg2merge', dest='merge2merge', action='store_true', help='Allow merges to aliased or merged patient')
	parser.add_argument ('-i', '--IHI', dest='IHI', action='store_true', help='Add Australian IHI number')
	parser.add_argument ('-x', '--extendNames', dest='extendNames', action='store_true', help='Extend names with sequential letters')
	parser.add_argument ('-e', '--errors', dest='errors', action='store_true', help='Create PMI with errors')
	parser.add_argument ('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0,5), help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
	parser.add_argument ('-o', '--logfile', metavar='logfile', dest='logfile', action='store', help='The name of a logging file')
	args = parser.parse_args()

	# Parse the command line options
	logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
	logfmt = progName + ' [%(asctime)s]: %(message)s'
	if args.loggingLevel :	# Change the logging level from "WARN" if the -v vebose option is specified
		loggingLevel = args.loggingLevel
		if args.logfile :		# and send it to a file if the -o logfile option is specified
			logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
								filemode='w', filename=args.logfile)
		else :
			logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
	else :
		if args.logfile :		# send the default (WARN) logging to a file if the -o logfile option is specified
			logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p',
								filemode='w', filename=args.logfile)
		else :
			logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')
	PMIoutputfile = args.PMIoutputfile
	addressFile = args.addressFile
	makeRandom = args.makeRandom
	both = args.both
	alias2alias = args.alias2alias
	merge2merge = args.merge2merge
	IHI = args.IHI
	extendNames = args.extendNames
	errors = args.errors

	# Then read in the configuration from mkPMI.cfg
	config = configparser.ConfigParser(allow_no_value=True)
	config.optionxform = str
	try :
		config.read('mkPMI.cfg')
		startPID = config.getint('PMI', 'startPID')
		startUR = config.getint('PMI', 'startUR')
		endUR = config.getint('PMI', 'endUR')
		skipUR = config.getint('PMI', 'skipUR')
		if IHI :
			startIHI = config.getint('IHI', 'startIHI') % 10000000
			skipIHI = config.getint('IHI', 'skipIHI')
			percentIHI = config.getfloat('IHI', 'percentIHI')
			if (percentIHI > 100.0) or (percentIHI < 0.0) :
				percentIHI = 10.0
		fields = config.get('Fields', 'PMIfields')
		dialect = csv.Sniffer().sniff(fields)
		dialect.skipinitialspace = True
		for row in csv.reader([fields], dialect) :
			fields = row
			break
		minAge = config.getint('AgeRange', 'minAge')
		maxAge = config.getint('AgeRange', 'maxAge')
		aliases = config.getfloat('Profile', 'aliases')
		if (aliases > 100.0) or (aliases < 0.0) :
			aliases = 10.0
		merged = config.getfloat('Profile', 'merged')
		if (merged > 100.0) or (merged < 0.0) :
			merged = 5.0
		deleted = config.getfloat('Profile', 'deleted')
		if (deleted > 100.0) or (deleted < 0.0) :
			deleted = 2.0
		deceased = config.getfloat('Profile', 'deceased')
		if (deceased > 100.0) or (deceased < 0.0) :
			deceased = 2.0
		if errors :
			dupUR = config.getfloat('Errors', 'dupUR')
			if (dupUR > 100.0) or (dupUR < 0.0) :
				dupUR = 2.0
			potDup = config.getfloat('Errors', 'potDup')
			if (potDup > 100.0) or (potDup < 0.0) :
				potDup = 7.0
			orphanAliases = config.getfloat('Errors', 'orphanAliases')
			if (orphanAliases > 100.0) or (orphanAliases < 0.0) :
				orphanAliases = 5.0
			orphanMerges = config.getfloat('Errors', 'orphanMerges')
			if (orphanMerges > 100.0) or (orphanMerges < 0.0) :
				orphanMerges = 3.0
			undelAliases = config.getfloat('Errors', 'undeletedAliases')
			if (undelAliases > 100.0) or (undelAliases < 0.0) :
				undelAliases = 15.0
			undelMerges = config.getfloat('Errors', 'undeletedMerges')
			if (undelMerges > 100.0) or (undelMerges < 0.0) :
				undelMerges = 25.0
			familyNameErrors = config.getfloat('Errors', 'familyNameErrors')
			if (familyNameErrors > 100.0) or (familyNameErrors < 0.0) :
				familyNameErrors = 2.0
			givenNameErrors = config.getfloat('Errors', 'givenNameErrors')
			if (givenNameErrors > 100.0) or (givenNameErrors < 0.0) :
				givenNameErrors = 2.0
	except (configparser.MissingSectionHeaderError, configparser.NoSectionError, configparser.NoOptionError, configparser.ParsingError) as detail :
		logging.fatal('%s', detail)
		sys.exit(1)

	startPID = int(startPID)
	startUR = int(startUR)
	endUR = int(endUR)
	skipUR = int(skipUR)
	if skipUR < 1 :
		skipUR = 1
	if IHI :
		IHIno = int(startIHI)
		skipIHI = int(skipIHI)
		if skipIHI < 1 :
			skipIHI = 1
	URno = startUR
	PID = startPID
	patient = 0
	noOfPMIrecords = int(((endUR - startUR)/skipUR)*1.5)

	UsedIDs = {}
	mkRandPatients(addressFile, noOfPMIrecords, extendNames, False, makeRandom, minAge, maxAge, UsedIDs, False)		# Create enough random patient

	# Create the PMI
	with open(PMIoutputfile, 'wt', newline='') as csvfile :
		csvwriter = csv.writer(csvfile, dialect=csv.excel)
		PMIfields = ['PID', 'UR', 'Alias', 'Merged', 'Deleted']
		if IHI :
			PMIfields.append('IHI')
		PMIfields += fields
		csvwriter.writerow(PMIfields)
		masterMe = []			# not alias/not merged/not deleted patients
		masterDelMe = []		# deleted, but not alias/not merged patients
		skippedUR = []
		rCount = 0
		aCount = 0
		mCount = 0
		dCount = 0
		dAcount = 0
		dMcount = 0
		dBcount = 0
		bCount = 0
		dupCount = 0
		potDupCount = 0
		actDupCount = 0
		orphMcount = 0
		orphAcount = 0
		undelMcount = 0
		undelAcount = 0
		GNEcount = 0
		FNEcount = 0
		clones = []
		while URno < endUR :
			me = patientKeys[patient]
			patients[me]['PID'] = PID		# Create a new patient records
			patients[me]['UR'] = URno
			patients[me]['Alias'] = None
			patients[me]['Merged'] = None
			patients[me]['Deleted'] = None
			if IHI :
				if random.random()*100 < percentIHI :					# Check IHI required
					patients[me]['IHI'] = '%d%d' % (800360990000000 + IHIno, mkLuhn('%s' % (800360990000000 + IHIno)))
					if skipIHI == 0 :
						IHIno += 1
					elif skipIHI < 3 :
						IHIno += skipIHI
					else :
						IHIno += random.randrange(skipIHI - 1, skipIHI + 1)
					IHIno %= 10000000
				else :
					patients[me]['IHI'] = None
			if random.random()*100 < deceased :					# Check if time for a deceased person
				(year, month, day) = patients[me]['birthdate'].split('-')
				year = int(year)
				month = int(month)
				day = int(day)
				birthdate = datetime.date(year, month, day)
				today = datetime.date.today()
				age = today - birthdate
				deathDay = int(random.random()*age.days)
				deathDate = birthdate + datetime.timedelta(deathDay)
				patients[me]['deathDate'] = deathDate.isoformat()
			else :
				patients[me]['deathDate'] = None

			infoText = ''
			cloneInfo = ''
			rCount += 1
			if patient < 10 :			# Make sure we have a small pool of not alias/not merged/not deleted records
				masterMe.append(me)			# Keep track of not alias/not merged/not deleted patients
				masterDelMe.append(me)			# Keep track of not alias/not merged, but may be deleted, patients
			else :
				dupMe = None
				isAlias  = False
				isMerge  = False
				if random.random()*100 < aliases :					# Check if time for an alias record
					if alias2alias :
						dupMe =  patientKeys[random.randrange(0, patient)]
					else :
						dupMe =  random.choice(masterDelMe)
					patients[me]['Alias'] = patients[dupMe]['UR']
					infoText = 'to Alias'
					isAlias = True
					aCount += 1

					# Duplicate some patient data
					cloneInfo = clone(me, dupMe)

					# Then change a name (family name for females, given name for everything else)
					if patients[me]['sex'] == 'F' :
						familyName = selectFamilyName()
						infoText += ' fn'
						if patients[me]['married'] == 'M' :				# Two options if married
							prevName = re.search(' \(| \[|\^', patients[me]['familyName'])
							if prevName :
								patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]		# remove previous name
							if random.random() < 0.5 :
								patients[me]['familyName'] = '%s (%s)' % (patients[me]['familyName'], familyName)	# add previous name
							else :
								patients[me]['familyName'] = '%s (nee %s)' % (patients[me]['familyName'], familyName)	# add previous name
						else :
							hyphen = re.search('-', patients[me]['familyName'])
							if hyphen :
								patients[me]['familyName'] = patients[me]['familyName'][0:hyphen.start()]		# de-hyphenate
							patients[me]['familyName'] += '-' + familyName					# hyphenate
					else :
						infoText += ' gn'
						givenName = selectBoysname()
						patients[me]['givenName'] = givenName			# simple substitution
					if patients[dupMe]['Deleted'] == 'D' :
						if errors and (random.random()*100 < undelAliases) :		# Check if time for an undeleted alias of a deleted record
							infoText += ',of Del'
							undelAcount += 1
						else :
							patients[me]['Deleted'] = 'D'
					elif errors and (random.random()*100 < orphanAliases) :			# Check if time for an orphaned alias record
						infoText += ',badUR'
						if len(skippedUR) > 0 :
							patients[me]['UR'] = random.choice(skippedUR)
							del skippedUR[skippedUR.index(patients[me]['UR'])]
						else :
							patients[me]['UR'] = '%sX' % (patients[me]['UR'])
						orphAcount += 1
				if ((dupMe == None) or both) and (random.random()*100 < merged) :	# Check if time for a merged record	
					if dupMe == None :
						if merge2merge :
							dupMe =  patientKeys[random.randrange(0, patient)]
						else :
							dupMe =  random.choice(masterDelMe)
						# Duplicate some patient data
						cloneInfo = clone(me, dupMe)

					patients[me]['Merged'] = patients[dupMe]['UR']
					if infoText == '' :
						infoText = 'to Merged'
					else :
						infoText + ',Merged'
					mCount += 1
					isMerge = True
					if isAlias :
						bCount += 1

					if patients[dupMe]['Deleted'] == 'D' :
						if errors and (random.random()*100 < undelMerges) :	# Check if time for an undeleted merge of a deleted record
							infoText += ',of Del'
							undelMcount += 1
						else :
							patients[me]['Deleted'] = 'D'
					elif errors and (random.random()*100 < orphanMerges) :		# Check if time for an orphaned merged record
						infoText += ',badUR'
						if len(skippedUR) > 0 :
							patients[me]['UR'] =  random.choice(skippedUR)
							del skippedUR[skippedUR.index(patients[me]['UR'])]
						else :
							patients[me]['UR'] = '%sX' % (patients[me]['UR'])
						orphMcount += 1
				isDel = False
				if random.random()*100 < deleted :					# Check if time for a deleted record
					patients[me]['Deleted'] = 'D'
					if infoText == '' :
						infoText = 'to Deleted'
					else :
						infoText + ',Deleted'
					mCount += 1
					isDel = True
					dCount += 1
					if isAlias :
						if isAlias and isMerge :
							dBcount += 1
						else :
							dAcount += 1
					elif isMerge :
						dMcount += 1
					else :
						masterDelMe.append(me)		# Keep track of deleted, but not alias/not merged patients
				elif errors and (dupMe == None) :
					if random.random()*100 < dupUR :			# Check if time for a duplicate UR record
						dupMe =  random.choice(masterMe)
						patients[me]['UR'] = patients[dupMe]['UR']
						infoText = 'to DupUR'
						dupCount += 1
						skippedUR.append(URno)
					elif random.random()*100 < potDup :			# Check if time for a potential duplicate
						dupMe =  random.choice(masterMe)
						infoText = 'to potDup'
						actDup = False

						# Duplicate some patient data
						cloneInfo = clone(me, dupMe)

						actDup = True
						if random.random() < 0.3 :			# Sometimes the marital status is wrong
							infoText += ' married'
							if patients[me]['married'] == 'M' :
								patients[me]['married'] = 'S'
							else :
								patients[me]['married'] = 'M'
							actDup = False
						if patients[me]['birthdate'] != patients[dupMe]['birthdate'] :
							if infoText == 'to potDup' :
								infoText += ' bd'
							else :
								infoText += ',bd'
							actDup = False
						if random.random() < 0.25 :			# Sometimes the given name is wrong
							givenName = patients[me]['givenName']
							if patients[me]['sex'] == 'F' :
								patients[me]['givenName'] = selectGirlsname()
							else :
								patients[me]['givenName'] = selectBoysname()
							if patients[me]['givenName'] == givenName :
								actDup = True
							else :
								if infoText == 'to potDup' :
									infoText += ' gn'
								else :
									infoText += ',gn'
							actDup = False
						if random.random() < 0.333 :			# Sometimes the family name is wrong
							familyName = patients[me]['familyName']
							patients[me]['familyName'] = selectFamilyName()
							if patients[me]['familyName'] == familyName :
								actDup = True
							else :
								if infoText == 'to potDup' :
									infoText += ' fn'
								else :
									infoText += ',fn'
							actDup = False
						if random.random() < 0.5 :			# Sometimes the sex is wrong
							if infoText == 'to potDup' :
								infoText += ' sex'
							else :
								infoText += ',sex'
							if patients[me]['sex'] == 'M' :
								patients[me]['sex'] = 'F'
							else :
								patients[me]['sex'] = 'M'
							actDup = False
						thisKey = patients[me]['familyName'] + '~' + patients[me]['givenName'] + '~'
						thisKey += patients[me]['sex'] + '~' + patients[me]['birthdate']
						if thisKey in clones :
							actDupCount += 1
						else :
							clones.append(thisKey)
							if actDup :
								actDupCount += 1
							else :
								potDupCount += 1
					else :
						masterMe.append(me)		# Keep track of not alias/not merged/not deleted patients
				if errors and (dupMe == None) and (not isDel) :
					if random.random()*100 < familyNameErrors :		# Check if time for a family name error
						infoText = 'fn error'
						FNEcount += 1
						prevName = re.search(' \(| \[|\^', patients[me]['familyName'])
						if prevName :
							patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]		# remove previous name
						if (patients[me]['sex'] == 'F') and (patients[me]['married'] == 'M') :
							familyName = selectFamilyName()
							if random.random() < 0.3 :
								patients[me]['familyName'] = '%s (%s)' % (patients[me]['familyName'], familyName)	# previous name in round brackets
							elif random.random() < 0.6 :
								patients[me]['familyName'] = '%s [%s]' % (patients[me]['familyName'], familyName)	# previous name in square brackets
							else :
								patients[me]['familyName'] = '%s (nee %s)' % (patients[me]['familyName'], familyName)	# previous name as (nee ...)
						else :
							suffix = re.search(' ', patients[me]['familyName'])
							if (not suffix) and (random.random() < 0.2) :
								patients[me]['familyName'] += ' III'
							elif (not suffix) and (random.random() < 0.5) :
								patients[me]['familyName'] += ' JNR'
							elif random.random() < 0.95 :
								if suffix :			# Remove suffix
									patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]		# remove suffix name
								patients[me]['familyName'] += '-' + selectFamilyName()
							else :
								if suffix :			# Remove suffix
									patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]		# remove suffix name
								patients[me]['familyName'] += '^' + selectFamilyName()
					if random.random()*100 < givenNameErrors :		# Check if time for a given name error
						if infoText == '' :
							infoText = 'gn error'
						else :
							infoText += ',gn error'
						GNEcount += 1
						prevNickname = re.search(' \(| \*', patients[me]['familyName'])
						if (not prevNickname) and (patients[me]['givenName'] in nicknames) :
							nickname = random.choice(nicknames[patients[me]['givenName']])
							if random.random() < 0.5 :
								patients[me]['givenName'] += ' *' + nickname
							else :
								patients[me]['givenName'] += ' (' + nickname + ')'
						else :
							(year, month, day) = patients[me]['birthdate'].split('-')
							year = int(year)
							month = int(month)
							day = int(day)
							birthdate = datetime.date(year, month, day)
							today = datetime.date.today()
							age = today - birthdate
							if age < datetime.timedelta(days=60) :		# a baby
								patients[me]['givenName'] = 'TWIN 1'
							else :
								if prevNickname :				# Remove previous nick name
									patients[me]['givenName'] = patients[me]['givenName'][0:prevNickname.start()]
								hyphen = re.search('-', patients[me]['givenName'])
								if hyphen :					# Remove second name
									patients[me]['givenName'] = patients[me]['givenName'][0:hyphen.start()]
								if patients[me]['sex'] == 'M' :
									patients[me]['givenName'] += ' (' + selectBoysname() + ')'
								else :
									patients[me]['givenName'] += ' (' + selectGirlsname() + ')'
			PMI = []
			for field in (PMIfields) :
				PMI.append(patients[me][field])
			csvwriter.writerow(PMI)
			if infoText != '' :
				if dupMe != None :
					if cloneInfo != '' :
						dupPMI = ['cloned (%s)' % (cloneInfo)]
					else :
						dupPMI = ['cloned']
					for field in (PMIfields) :
						dupPMI.append(patients[dupMe][field])
					logging.info(csvString(dupPMI))
				info = [infoText] + PMI
				logging.info(csvString(info))
			patient += 1
			PID += 1
			if skipUR == 0 :
				URno += 1
			elif skipUR < 3 :
				URno += skipUR
			else :
				URno += random.randrange(skipUR - 1, skipUR + 1)

	# Report the results
	print('%d\tPMI Records created' % (rCount))
	print('%d\t\talias records' % (aCount))
	print('%d\t\tmerged records' % (mCount))
	if both :
		print('\t\tof which %d were both aliases and merged records' % (bCount))
	print('%d\t\tdeleted records' % (dCount))
	print('\t\tof which %d were aliases records' % (dAcount))
	print('\t\tand %d were merged records' % (dMcount))
	if both :
		print('\t\t\tof which %d were both aliases and merged records' % (dBcount))
	if errors :
		print
		print('Introduced errors')
		print('%d\trecords given a duplicate UR' % (dupCount))
		print('%d\trecords are duplicates records (different UR)' % (actDupCount))
		print('%d\t(at least) records are potential duplicates (different UR)' % (potDupCount))
		print('%d\torphaned alias records' % (orphAcount))
		print('%d\torphaned merged records' % (orphMcount))
		print('%d\tundeleted alias of deleted records' % (undelAcount))
		print('%d\tundeleted merges of deleted records' % (undelMcount))
		print()
		print('%d\tNon-standard given names' % (GNEcount))
		print('%d\tNon-standard family names' % (FNEcount))
