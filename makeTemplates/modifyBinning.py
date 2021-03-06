#!/usr/bin/python

import os,sys,time,math,fnmatch
parent = os.path.dirname(os.getcwd())
sys.path.append(parent)
from array import array
from weights import *
from modSyst import *
from utils import *
from ROOT import *
start_time = time.time()

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run as:
# > python modifyBinning.py
# 
# Optional arguments:
# -- statistical uncertainty threshold
#
# Notes:
# -- Finds certain root files in a given directory and rebins all histograms in each file
# -- A selection of subset of files in the input directory can be done below under "#Setup the selection ..."
# -- A custom binning choice can also be given by manually filling "xbinsList[chn]" for each channel
#    with the preferred choice of binning
# -- If no rebinning is wanted, but want to add PDF and R/F uncertainties, use a stat unc threshold 
#    that is larger than 100% (i.e, >1.)
# -- If CR and SR templates are in the same file and single bins are required for CR templates,
#    this can be done with "singleBinCR" bool (assumes that the CR templates contain "isCR" tags!).
# -- Use "removalKeys" to remove specific systematics from the output file.
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


iPlot='DnnTprime'
if len(sys.argv)>1: iPlot=str(sys.argv[1])
folder = 'templatesSR_May2020TT_May9'
if len(sys.argv)>2: folder=str(sys.argv[2])
cutString = ''
templateDir = os.getcwd()+'/'+folder+'/'+cutString
print "templateDir: ",templateDir
combinefile = 'yields_'+iPlot+'_35p867fb.root'


rebin4chi2 = False #include data in requirements
rebinCombine = False #else rebins theta templates

normalizeRENORM = False #only for signals
normalizePDF    = False #only for signals
#X53X53, TT, BB, HTB, etc --> this is used to identify signal histograms for combine templates when normalizing the pdf and muRF shapes to nominal!!!!
sigName = 'TT' #MAKE SURE THIS WORKS FOR YOUR ANALYSIS PROPERLY!!!!!!!!!!!
massList = range(1000,1800+1,100)

sigProcList = [sigName+'M'+str(mass) for mass in massList]
if sigName=='TT': 
	sigProcList = [sigName+'M'+str(mass) for mass in massList]
	if not rebinCombine: sigProcList = [sigName+'M'+str(mass) for mass in massList]
bkgProcList = ['top','ewk','qcd'] #put the most dominant process first
era = "13TeV"

stat_saved = 0.3 #statistical uncertainty requirement (enter >1.0 for no rebinning; i.g., "1.1")
if len(sys.argv)>3: stat_saved=float(sys.argv[3])
singleBinCR = False

if rebinCombine:
	dataName = 'data_obs'
	upTag = 'Up'
	downTag = 'Down'
else: #theta
	dataName = 'DATA'
	upTag = '__plus'
	downTag = '__minus'

addCRsys = False
addShapes = True
lumiSys = math.sqrt(0.023**2) #lumi uncertainty plus higgs prop
eltrigSys = 0.03 #electron trigger uncertainty
mutrigSys = 0.03 #muon trigger uncertainty
elIdSys = 0.02 #electron id uncertainty
muIdSys = 0.02 #muon id uncertainty
elIsoSys = 0.01 #electron isolation uncertainty
muIsoSys = 0.01 #muon isolation uncertainty
elcorrdSys = math.sqrt(lumiSys**2+eltrigSys**2+elIdSys**2+elIsoSys**2)
mucorrdSys = math.sqrt(lumiSys**2+mutrigSys**2+muIdSys**2+muIsoSys**2)

removalKeys = {} # True == keep, False == remove
removalKeys['btag__']    = True
removalKeys['ltag__']  = True
removalKeys['trigeff__'] = False
removalKeys['muR__']       = False
removalKeys['muF__']       = False
removalKeys['muRFcorrd__'] = False
removalKeys['jsf__'] = True

def findfiles(path, filtre):
    for root, dirs, files in os.walk(path):
        for f in fnmatch.filter(files, filtre):
            yield os.path.join(root, f)

#Setup the selection of the files to be rebinned:          only those that aren't rebinned and are this plot
if 'BB' in folder: 
	rfiles = [file for file in findfiles(templateDir, '*.root') if 'rebinned' not in file and 'tW' in file and combinefile not in file and '_'+iPlot+'_' in file.split('/')[-1]]
if 'TT' in folder:
        rfiles = [file for file in findfiles(templateDir, '*.root') if 'rebinned' not in file and 'bW' in file and combinefile not in file and '_'+iPlot+'_' in file.split('/')[-1]]
print "templateDir: ",templateDir
print "file: ",file
print "combinefile: ",combinefile
print "iPlot: ",iPlot
print "rfiles: ",rfiles
if rebinCombine: rfiles = [templateDir+'/'+combinefile]

#Open the lowest mass signal for consistency
for rfile in rfiles:
	if 'TTM1100' in rfile or 'BBM1100' in rfile: tfile = TFile(rfile)
print tfile
datahists = [k.GetName() for k in tfile.GetListOfKeys() if '__'+dataName in k.GetName()]
print datahists
channels = [hist[hist.find('fb_')+3:hist.find('__')] for hist in datahists if 'isL_' not in hist]
allhists = {chn:[hist.GetName() for hist in tfile.GetListOfKeys() if chn in hist.GetName()] for chn in channels}

DataHists = {}
for hist in datahists:
	channel = hist[hist.find('fb_')+3:hist.find('__')]
	DataHists[channel] = tfile.Get(hist).Clone()
	#DataHists[channel].Rebin(20)

totBkgHists = {}
for hist in datahists:
	channel = hist[hist.find('fb_')+3:hist.find('__')]
	totBkgHists[channel]=tfile.Get(hist.replace('__'+dataName,'__'+bkgProcList[0])).Clone()
	for proc in bkgProcList:
		if proc == bkgProcList[0]: continue
		try: totBkgHists[channel].Add(tfile.Get(hist.replace('__'+dataName,'__'+proc)))
		except: 
			print "Missing",proc,"for category:",hist
			print "WARNING! Skipping this process!!!!"
			pass
	#totBkgHists[channel].Rebin(20)

SigHists = {}
for hist in datahists:
	channel = hist[hist.find('fb_')+3:hist.find('__')]
	SigHists[channel]=tfile.Get(hist.replace('__'+dataName,'__sig')).Clone()
	#SigHists[channel].Rebin(20)

xbinsListTemp = {}
for chn in totBkgHists.keys():
	#if 'notV' in chn and (iPlot == 'Tp2MDnn' or iPlot == 'DnnTprime'): stat = 1.1
	stat = stat_saved

	#print 'Channel',chn,'integral is',totBkgHists[chn].Integral()
	if 'isE' not in chn: continue
	print 'Processing',chn

	Nbins = 0
	if 'notV' in chn: 
#		if 'Counts' not in folder:
#			xbinsListTemp[chn]=[tfile.Get(datahists[0]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[0]).GetXaxis().GetNbins())]
#			Nbins = tfile.Get(datahists[0]).GetNbinsX()
#		else:
			xbinsListTemp[chn]=[tfile.Get(datahists[4]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[4]).GetXaxis().GetNbins())]
			Nbins = tfile.Get(datahists[4]).GetNbinsX()
	else: 
#		if 'Counts' not in folder:
#			xbinsListTemp[chn]=[tfile.Get(datahists[4]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[4]).GetXaxis().GetNbins())]
#			Nbins = tfile.Get(datahists[4]).GetNbinsX()
#		else:
			xbinsListTemp[chn]=[tfile.Get(datahists[0]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[0]).GetXaxis().GetNbins())]
			Nbins = tfile.Get(datahists[0]).GetNbinsX()
	
	totTempBinContent_E = 0.
	totTempBinContent_M = 0.
	totTempBinErrSquared_E = 0.
	totTempBinErrSquared_M = 0.
	totTempDataContent_E = 0.
	totTempDataContent_M = 0.
	totTempDataErrSquared_E = 0.
	totTempDataErrSquared_M = 0.
	totTempSigContent_E = 0;
	totTempSigContent_M = 0;
	for iBin in range(1,Nbins+1):
		totTempBinContent_E += totBkgHists[chn].GetBinContent(Nbins+1-iBin)
		totTempBinContent_M += totBkgHists[chn.replace('isE','isM')].GetBinContent(Nbins+1-iBin)
		totTempBinErrSquared_E += totBkgHists[chn].GetBinError(Nbins+1-iBin)**2
		totTempBinErrSquared_M += totBkgHists[chn.replace('isE','isM')].GetBinError(Nbins+1-iBin)**2
		try:
			totTempSigContent_E += SigHists[chn].GetBinContent(Nbins+1-iBin)
			totTempSigContent_M += SigHists[chn.replace('isE','isM')].GetBinContent(Nbins+1-iBin)
		except: pass
		totTempDataContent_E += DataHists[chn].GetBinContent(Nbins+1-iBin)
		totTempDataContent_M += DataHists[chn.replace('isE','isM')].GetBinContent(Nbins+1-iBin)
		totTempDataErrSquared_E += totBkgHists[chn].GetBinError(Nbins+1-iBin)**2
		totTempDataErrSquared_M += totBkgHists[chn.replace('isE','isM')].GetBinError(Nbins+1-iBin)**2
		
		#print 'totTempBinContent =',totTempBinContent_E,' ',totTempBinContent_M,', totTempBinErrSquared =',totTempBinErrSquared_E,' ',totTempBinErrSquared_M
		#print 'totTempSigContent =',totTempSigContent_E,' ',totTempSigContent_M

		if totTempBinContent_E>0. and totTempBinContent_M>0.:
			#if 'CR' in templateDir or 'ttbar' in templateDir or 'wjets' in templateDir or 'higgs' in templateDir or (totTempSigContent_E>0. and totTempSigContent_M>0):
			#if rebin4chi2 and (totTempDataContent_E == 0 or totTempDataContent_M == 0): continue
			if math.sqrt(totTempBinErrSquared_E)/totTempBinContent_E<=stat and math.sqrt(totTempBinErrSquared_M)/totTempBinContent_M<=stat:
				if not rebin4chi2 or (math.sqrt(totTempDataErrSquared_E)/totTempDataContent_E<=stat and math.sqrt(totTempDataErrSquared_M)/totTempDataContent_M<=stat):
					totTempBinContent_E = 0.
					totTempBinContent_M = 0.
					totTempBinErrSquared_E = 0.
					totTempBinErrSquared_M = 0.
					totTempDataContent_E = 0.
					totTempDataContent_M = 0.
					totTempDataErrSquared_E = 0.
					totTempDataErrSquared_M = 0.
					totTempSigContent_E = 0.
					totTempSigContent_M = 0.
					#print 'Appending bin edge',totBkgHists[chn].GetXaxis().GetBinLowEdge(Nbins+1-iBin)
					xbinsListTemp[chn].append(totBkgHists[chn].GetXaxis().GetBinLowEdge(Nbins+1-iBin))

	## Going right to left -- if the last entry isn't 0 add it
	if ((iPlot != 'DnnTprime' and iPlot != 'DnnBprime') or 'CR' in folder) and xbinsListTemp[chn][-1]!=0: xbinsListTemp[chn].append(0)
	if (iPlot == 'DnnTprime' or iPlot == 'DnnBprime') and 'templatesSR' in folder:
		if xbinsListTemp[chn][-1]>0.5: xbinsListTemp[chn].append(0.5)
		elif xbinsListTemp[chn][-1]!=0.5: xbinsListTemp[chn][-1] = 0.5
	elif (iPlot == 'DnnTprime' or iPlot == 'DnnBprime') and 'CR' in folder and xbinsListTemp[chn][0]!=0.5: xbinsListTemp[chn][0] = 0.5 
	
	## If the 1st bin is empty or too small, make the left side wider
	if totBkgHists[chn].GetBinContent(1)==0. or totBkgHists[chn.replace('isE','isM')].GetBinContent(1)==0.: 
		if len(xbinsListTemp[chn])>2: del xbinsListTemp[chn][-2]
	elif totBkgHists[chn].GetBinError(1)/totBkgHists[chn].GetBinContent(1)>stat or totBkgHists[chn.replace('isE','isM')].GetBinError(1)/totBkgHists[chn.replace('isE','isM')].GetBinContent(1)>stat: 
		if len(xbinsListTemp[chn])>2: del xbinsListTemp[chn][-2]

	## Set mu and el bins equal
	xbinsListTemp[chn.replace('isE','isM')]=xbinsListTemp[chn]

	## Ignore all this if stat is > 1
	if stat>1.0:
		if 'notV' in chn: xbinsListTemp[chn] = [tfile.Get(datahists[0]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[0]).GetXaxis().GetNbins())]
		else: xbinsListTemp[chn] = [tfile.Get(datahists[4]).GetXaxis().GetBinUpEdge(tfile.Get(datahists[4]).GetXaxis().GetNbins())]
		for iBin in range(1,Nbins+1): 
			xbinsListTemp[chn].append(totBkgHists[chn].GetXaxis().GetBinLowEdge(Nbins+1-iBin))
		xbinsListTemp[chn.replace('isE','isM')] = xbinsListTemp[chn]

print "==> Here is the binning I found with",stat_saved*100,"% uncertainty threshold: "
print "//"*40
xbinsList = {}
for chn in xbinsListTemp.keys():
	xbinsList[chn] = []
	for bin in range(len(xbinsListTemp[chn])): xbinsList[chn].append(xbinsListTemp[chn][len(xbinsListTemp[chn])-1-bin])
	if 'isCR' in chn and singleBinCR: xbinsList[chn] = [xbinsList[chn][0],xbinsList[chn][-1]]
	print chn,"=",xbinsList[chn]
print "//"*40



xbins = {}
for key in xbinsList.keys(): xbins[key] = array('d', xbinsList[key])

#os._exit(1)

### Updated for 2017, JH August 2019
muSFsUp = {'TTM1000':0.744,'TTM1100':0.747,'TTM1200':0.742,'TTM1300':0.741,'TTM1400':0.738,'TTM1500':0.740,'TTM1600':0.735,'TTM1700':0.721,'TTM1800':0.746}
muSFsDn = {'TTM1000':1.312,'TTM1100':1.306,'TTM1200':1.315,'TTM1300':1.316,'TTM1400':1.322,'TTM1500':1.319,'TTM1600':1.329,'TTM1700':1.354,'TTM1800':1.311}
pdfSFsUp = {'TTM1000':0.997,'TTM1100':0.996,'TTM1200':0.995,'TTM1300':0.994,'TTM1400':0.991,'TTM1500':0.986,'TTM1600':0.984,'TTM1700':0.980,'TTM1800':0.966}
pdfSFsDn = {'TTM1000':1.005,'TTM1100':1.007,'TTM1200':1.008,'TTM1300':1.011,'TTM1400':1.015,'TTM1500':1.022,'TTM1600':1.027,'TTM1700':1.031,'TTM1800':1.050}

if sigName == 'BB':
	muSFsUp = {'BBM1000':0.742,'BBM1100':0.743,'BBM1200':0.742,'BBM1300':0.741,'BBM1400':0.739,'BBM1500':0.735,'BBM1600':0.735,'BBM1700':0.733,'BBM1800':0.731}
	muSFsDn = {'BBM1000':1.315,'BBM1100':1.314,'BBM1200':1.316,'BBM1300':1.318,'BBM1400':1.321,'BBM1500':1.329,'BBM1600':1.329,'BBM1700':1.331,'BBM1800':1.337}
	pdfSFsUp = {'BBM1000':0.997,'BBM1100':0.997,'BBM1200':0.996,'BBM1300':0.994,'BBM1400':0.991,'BBM1500':0.987,'BBM1600':0.984,'BBM1700':0.979,'BBM1800':0.970}
	pdfSFsDn = {'BBM1000':1.005,'BBM1100':1.006,'BBM1200':1.008,'BBM1300':1.011,'BBM1400':1.015,'BBM1500':1.019,'BBM1600':1.027,'BBM1700':1.037,'BBM1800':1.049}


iRfile=0
yieldsAll = {}
yieldsErrsAll = {}
yieldsSystErrsAll = {}
stat = stat_saved
for rfile in rfiles: 
	print "REBINNING FILE:",rfile
	tfiles = {}
	outputRfiles = {}
	tfiles[iRfile] = TFile(rfile)	
	if not rebin4chi2: outputRfiles[iRfile] = TFile(rfile.replace('.root','_rebinned_stat'+str(stat).replace('.','p')+'.root'),'RECREATE')
	else: outputRfiles[iRfile] = TFile(rfile.replace('.root','_chi2_rebinned_stat'+str(stat).replace('.','p')+'.root'),'RECREATE')

	signame = rfile.split('/')[-1].split('_')[2]
	if 'TTM' not in signame and 'BBM' not in signame: print 'DIDNT STORE SIGNAME: ',signame

	print "PROGRESS:"
	for chn in channels:
		print "         ",chn
		rebinnedHists = {}
		#Rebinning histograms
		for hist in allhists[chn]:
			#temphist=tfiles[iRfile].Get(hist).Rebin(20)
			rebinnedHists[hist] = tfiles[iRfile].Get(hist).Rebin(len(xbins[chn])-1,hist,xbins[chn])
			rebinnedHists[hist].SetDirectory(0)
			if '__pdf' in hist:
				if 'Up' not in hist or 'Down' not in hist: continue
			if any([item in hist and not removalKeys[item] for item in removalKeys.keys()]): continue
			rebinnedHists[hist].Write()

			if 'W0p5' in rfile:
				yieldHistName = hist
				if not rebinCombine: yieldHistName = hist.replace('_sig','_'+rfile.split('_')[-5]) ### ASSUMING BR IS IN FILE NAME

				yieldsAll[yieldHistName] = rebinnedHists[hist].Integral()
				yieldsErrsAll[yieldHistName] = 0.
				for ibin in range(1,rebinnedHists[hist].GetXaxis().GetNbins()+1):
					yieldsErrsAll[yieldHistName] += rebinnedHists[hist].GetBinError(ibin)**2
				yieldsErrsAll[yieldHistName] = math.sqrt(yieldsErrsAll[yieldHistName])

			
		##Check for empty signal bins
		#sighist = rebinnedHists[iPlot+'_36p814fb_'+chn+'__sig']
		#for ibin in range(1,sighist.GetNbinsX()+1):
		#	if sighist.GetBinContent(ibin) == 0: print 'chn = '+chn+', mass = '+sigName+', empty minMlb > '+str(sighist.GetBinLowEdge(ibin))
			


		#Constructing muRF shapes
		muRUphists = [k.GetName() for k in tfiles[iRfile].GetListOfKeys() if 'muR'+upTag in k.GetName() and chn in k.GetName()]
		for hist in muRUphists:
			newMuRFNameBase = 'muRFcorrdNew'
			if 'qcd__' in hist: newMuRFName = newMuRFNameBase+'QCD'
			if 'ewk__' in hist: newMuRFName = newMuRFNameBase+'Ewk'
			if 'top__' in hist: newMuRFName = newMuRFNameBase+'Top'
			if 'sig__' in hist: newMuRFName = newMuRFNameBase+'Sig'
			muRFcorrdNewUpHist = rebinnedHists[hist].Clone(hist.replace('muR'+upTag,newMuRFName+upTag))
			muRFcorrdNewDnHist = rebinnedHists[hist].Clone(hist.replace('muR'+upTag,newMuRFName+downTag))
			histList = [
				rebinnedHists[hist[:hist.find('__mu')]], #nominal
				rebinnedHists[hist], #renormWeights[4]
				rebinnedHists[hist.replace('muR'+upTag,'muR'+downTag)], #renormWeights[2]
				rebinnedHists[hist.replace('muR'+upTag,'muF'+upTag)], #renormWeights[1]
				rebinnedHists[hist.replace('muR'+upTag,'muF'+downTag)], #renormWeights[0]
				rebinnedHists[hist.replace('muR'+upTag,'muRFcorrd'+upTag)], #renormWeights[5]
				rebinnedHists[hist.replace('muR'+upTag,'muRFcorrd'+downTag)] #renormWeights[3]
				]
			for ibin in range(1,histList[0].GetNbinsX()+1):
				weightList = [histList[ind].GetBinContent(ibin) for ind in range(len(histList))]
				indCorrdUp = weightList.index(max(weightList))
				indCorrdDn = weightList.index(min(weightList))

				muRFcorrdNewUpHist.SetBinContent(ibin,histList[indCorrdUp].GetBinContent(ibin))
				muRFcorrdNewDnHist.SetBinContent(ibin,histList[indCorrdDn].GetBinContent(ibin))

				muRFcorrdNewUpHist.SetBinError(ibin,histList[indCorrdUp].GetBinError(ibin))
				muRFcorrdNewDnHist.SetBinError(ibin,histList[indCorrdDn].GetBinError(ibin))
			if ('sig__mu' in hist and normalizeRENORM) or (rebinCombine and '__'+sigName in hist and '__mu' in hist and normalizeRENORM): #normalize the renorm/fact shapes to nominal
				scalefactorUp = muSFsUp[signame]
				scalefactorDn = muSFsDn[signame]
				muRFcorrdNewUpHist.Scale(scalefactorUp)
				muRFcorrdNewDnHist.Scale(scalefactorDn)
 				# renormNomHist = tfiles[iRfile].Get(hist[:hist.find('__mu')]).Clone()
				# muRFcorrdNewUpHist.Scale(renormNomHist.Integral()/muRFcorrdNewUpHist.Integral())
				# muRFcorrdNewDnHist.Scale(renormNomHist.Integral()/muRFcorrdNewDnHist.Integral())
			muRFcorrdNewUpHist.Write()
			muRFcorrdNewDnHist.Write()
			yieldsAll[muRFcorrdNewUpHist.GetName().replace('_sig','_'+rfile.split('_')[-2])] = muRFcorrdNewUpHist.Integral()
			yieldsAll[muRFcorrdNewDnHist.GetName().replace('_sig','_'+rfile.split('_')[-2])] = muRFcorrdNewDnHist.Integral()

		#Constructing PDF shapes
		pdfUphists = [k.GetName() for k in tfiles[iRfile].GetListOfKeys() if 'pdf0' in k.GetName() and chn in k.GetName()]
		newPDFName = 'pdfNew'
		for hist in pdfUphists:
			pdfNewUpHist = rebinnedHists[hist].Clone(hist.replace('pdf0',newPDFName+upTag))
			pdfNewDnHist = rebinnedHists[hist].Clone(hist.replace('pdf0',newPDFName+downTag))
			for ibin in range(1,pdfNewUpHist.GetNbinsX()+1):
				weightList = [rebinnedHists[hist.replace('pdf0','pdf'+str(pdfInd))].GetBinContent(ibin) for pdfInd in range(100)]
				indPDFUp = sorted(range(len(weightList)), key=lambda k: weightList[k])[83]
				indPDFDn = sorted(range(len(weightList)), key=lambda k: weightList[k])[15]
				pdfNewUpHist.SetBinContent(ibin,rebinnedHists[hist.replace('pdf0','pdf'+str(indPDFUp))].GetBinContent(ibin))
				pdfNewDnHist.SetBinContent(ibin,rebinnedHists[hist.replace('pdf0','pdf'+str(indPDFDn))].GetBinContent(ibin))
				pdfNewUpHist.SetBinError(ibin,rebinnedHists[hist.replace('pdf0','pdf'+str(indPDFUp))].GetBinError(ibin))
				pdfNewDnHist.SetBinError(ibin,rebinnedHists[hist.replace('pdf0','pdf'+str(indPDFDn))].GetBinError(ibin))
			if ('sig__pdf' in hist and normalizePDF) or (rebinCombine and '__'+sigName in hist and '__pdf' in hist and normalizePDF): #normalize the renorm/fact shapes to nominal
				scalefactorUp = pdfSFsUp[signame]
				scalefactorDn = pdfSFsDn[signame]
				#print 'Mass',signame,': assigning SFup =',scalefactorUp,', SFdn =',scalefactorDn
				pdfNewUpHist.Scale(scalefactorUp)
				pdfNewDnHist.Scale(scalefactorDn)
				#pdfNewUpHist.Scale(renormNomHist.Integral()/pdfNewUpHist.Integral())
				#pdfNewDnHist.Scale(renormNomHist.Integral()/pdfNewDnHist.Integral())
			pdfNewUpHist.Write()
			pdfNewDnHist.Write()
			yieldsAll[pdfNewUpHist.GetName().replace('_sig','_'+rfile.split('_')[-2])] = pdfNewUpHist.Integral()
			yieldsAll[pdfNewDnHist.GetName().replace('_sig','_'+rfile.split('_')[-2])] = pdfNewDnHist.Integral()

	tfiles[iRfile].Close()
	outputRfiles[iRfile].Close()
	iRfile+=1
tfile.Close()
print ">> Rebinning Done!"

for chn in channels:
	modTag = chn[chn.find('is'):]
	modelingSys[dataName+'_'+modTag]=0.
	modelingSys['qcd_'+modTag]=0.
	if not addCRsys: #else CR uncertainties are defined in modSyst.py module
		for proc in bkgProcList:
			modelingSys[proc+'_'+modTag] = 0.
	
isEMlist =[]
algolist = []
taglist = []
for chn in channels:
	if chn.split('_')[0+rebinCombine] not in isEMlist: isEMlist.append(chn.split('_')[0+rebinCombine])
	if chn.split('_')[1+rebinCombine] not in taglist: taglist.append(chn.split('_')[1+rebinCombine])
	if chn.split('_')[2+rebinCombine] not in algolist: algolist.append(chn.split('_')[2+rebinCombine])

print "List of systematics for "+bkgProcList[0]+" process and "+channels[0]+" channel:"
print "        ",sorted([hist[hist.find(bkgProcList[0])+len(bkgProcList[0])+2:hist.find(upTag)] for hist in yieldsAll.keys() if channels[0] in hist and '__'+bkgProcList[0]+'__' in hist and upTag in hist])

def getShapeSystUnc(proc,chn):
	if not addShapes: return 0
	systematicList = sorted([hist[hist.find(proc)+len(proc)+2:hist.find(upTag)] for hist in yieldsAll.keys() if chn in hist and '__'+proc+'__' in hist and upTag in hist])
	totUpShiftPrctg=0
	totDnShiftPrctg=0
	histoPrefix = allhists[chn][0][:allhists[chn][0].find('__')+2]
	nomHist = histoPrefix+proc
	for syst in systematicList:
		for ud in [upTag,downTag]:
			shpHist = histoPrefix+proc+'__'+syst+ud
			shift = yieldsAll[shpHist]/(yieldsAll[nomHist]+1e-20)-1
			if shift>0.: totUpShiftPrctg+=shift**2
			if shift<0.: totDnShiftPrctg+=shift**2
	shpSystUncPrctg = (math.sqrt(totUpShiftPrctg)+math.sqrt(totDnShiftPrctg))/2 #symmetrize the total shape uncertainty up/down shifts
	return shpSystUncPrctg	

table = []
for isEM in isEMlist:
	if isEM=='isE': corrdSys = elcorrdSys
	if isEM=='isM': corrdSys = mucorrdSys
	for tag in ['tagged','notV']:
		table.append(['break'])
		table.append(['',isEM+'_'+tag+'_yields'])
		table.append(['break'])
		table.append(['YIELDS']+[chn for chn in channels if isEM in chn and tag in chn]+['\\\\'])
		for proc in bkgProcList+['totBkg',dataName,'dataOverBkg']+sigProcList:
			row = [proc]
			for chn in channels:
				if not (isEM in chn and tag in chn): continue
				modTag = chn[chn.find('is'):]
				histoPrefix = allhists[chn][0][:allhists[chn][0].find('__')+2]
				yieldtemp = 0.
				yielderrtemp = 0.
				if proc=='totBkg' or proc=='dataOverBkg':
					for bkg in bkgProcList:
						try:
							yieldtemp += yieldsAll[histoPrefix+bkg]
							yielderrtemp += yieldsErrsAll[histoPrefix+bkg]**2
							yielderrtemp += (modelingSys[bkg+'_'+modTag]*yieldsAll[histoPrefix+bkg])**2
							yielderrtemp += (getShapeSystUnc(bkg,chn)*yieldsAll[histoPrefix+bkg])**2
						except:
							if bkg != 'qcd': print "Missing",bkg,"for channel in totBkg or dataOverBkg:",chn
							pass
					yielderrtemp += (corrdSys*yieldtemp)**2
					if proc=='dataOverBkg':
						dataTemp = yieldsAll[histoPrefix+dataName]+1e-20
						dataTempErr = yieldsErrsAll[histoPrefix+dataName]**2
						yielderrtemp = ((dataTemp/yieldtemp)**2)*(dataTempErr/dataTemp**2+yielderrtemp/yieldtemp**2)
						yieldtemp = dataTemp/yieldtemp
				else:
					try:
						yieldtemp += yieldsAll[histoPrefix+proc]
						yielderrtemp += yieldsErrsAll[histoPrefix+proc]**2
						yielderrtemp += (getShapeSystUnc(proc,chn)*yieldsAll[histoPrefix+proc])**2
					except:
						if proc != 'qcd': print "Missing",proc,"for channel individual:",chn
						pass
					if proc in sigProcList:
						signal=proc
						if 'left' in signal: signal=proc.replace('left','')+'left'
						if 'right' in signal: signal=proc.replace('right','')+'right'
						yieldtemp*=xsec[signal]
						yielderrtemp*=xsec[signal]**2
					else: yielderrtemp += (modelingSys[proc+'_'+modTag]*yieldtemp)**2
					yielderrtemp += (corrdSys*yieldtemp)**2
				yielderrtemp = math.sqrt(yielderrtemp)
				if proc==dataName: row.append(' & '+str(int(yieldsAll[histoPrefix+proc])))
				else: row.append(' & '+str(round_sig(yieldtemp,5))+' $\pm$ '+str(round_sig(yielderrtemp,2)))
			row.append('\\\\')
			table.append(row)
			
for tag in ['tagged','notV']:
	table.append(['break'])
	table.append(['','isL_'+tag+'_yields'])
	table.append(['break'])
	table.append(['YIELDS']+[chn.replace('isE','isL') for chn in channels if 'isE' in chn and tag in chn]+['\\\\'])
	for proc in bkgProcList+['totBkg',dataName,'dataOverBkg']+sigProcList:
		row = [proc]
		for chn in channels:
			if not ('isE' in chn and tag in chn): continue
			modTag = chn[chn.find('is'):]
			histoPrefixE = allhists[chn][0][:allhists[chn][0].find('__')+2]
			histoPrefixM = histoPrefixE.replace('isE','isM')
			yieldtemp = 0.
			yieldtempE = 0.
			yieldtempM = 0.
			yielderrtemp = 0. 
			if proc=='totBkg' or proc=='dataOverBkg':
				for bkg in bkgProcList:
					yieldEplusMtemp = 0
					try:
						yieldtempE += yieldsAll[histoPrefixE+bkg]
						yieldtemp += yieldsAll[histoPrefixE+bkg]
						yieldEplusMtemp += yieldsAll[histoPrefixE+bkg]
						yielderrtemp += yieldsErrsAll[histoPrefixE+bkg]**2
						yielderrtemp += (getShapeSystUnc(bkg,chn)*yieldsAll[histoPrefixE+bkg])**2
					except:
						if bkg != 'qcd': print "Missing",bkg,"for channel in totBkg:",chn
						pass
					try:
						yieldtempM += yieldsAll[histoPrefixM+bkg]
						yieldtemp += yieldsAll[histoPrefixM+bkg]
						yieldEplusMtemp += yieldsAll[histoPrefixM+bkg]
						yielderrtemp += yieldsErrsAll[histoPrefixM+bkg]**2
						yielderrtemp += (getShapeSystUnc(bkg,chn.replace('isE','isM'))*yieldsAll[histoPrefixM+bkg])**2
					except:
						if bkg != 'qcd': print "Missing",bkg,"for channel in totBkg:",chn.replace('isE','isM')
						pass
					yielderrtemp += (modelingSys[bkg+'_'+modTag]*yieldEplusMtemp)**2 #(addSys*(Nelectron+Nmuon))**2 --> correlated across e/m
				yielderrtemp += (elcorrdSys*yieldtempE)**2+(mucorrdSys*yieldtempM)**2
				if proc=='dataOverBkg':
					dataTemp = yieldsAll[histoPrefixE+dataName]+yieldsAll[histoPrefixM+dataName]+1e-20
					dataTempErr = yieldsErrsAll[histoPrefixE+dataName]**2+yieldsErrsAll[histoPrefixM+dataName]**2
					yielderrtemp = ((dataTemp/yieldtemp)**2)*(dataTempErr/dataTemp**2+yielderrtemp/yieldtemp**2)
					yieldtemp = dataTemp/yieldtemp
			else:
				try:
					yieldtempE += yieldsAll[histoPrefixE+proc]
					yieldtemp  += yieldsAll[histoPrefixE+proc]
					yielderrtemp += yieldsErrsAll[histoPrefixE+proc]**2
					yielderrtemp += (getShapeSystUnc(proc,chn)*yieldsAll[histoPrefixE+proc])**2
				except:
					if proc != 'qcd': print "Missing",proc,"for channel individual:",chn
					pass
				try:
					yieldtempM += yieldsAll[histoPrefixM+proc]
					yieldtemp  += yieldsAll[histoPrefixM+proc]
					yielderrtemp += yieldsErrsAll[histoPrefixM+proc]**2
					yielderrtemp += (getShapeSystUnc(proc,chn.replace('isE','isM'))*yieldsAll[histoPrefixM+proc])**2
				except:
					if proc != 'qcd': print "Missing",proc,"for channel individual:",chn.replace('isE','isM')
					pass
				if proc in sigProcList:
					signal=proc
					if 'left' in signal: signal=proc.replace('left','')+'left'
					if 'right' in signal: signal=proc.replace('right','')+'right'
					yieldtempE*=xsec[signal]
					yieldtempM*=xsec[signal]
					yieldtemp*=xsec[signal]
					yielderrtemp*=xsec[signal]**2
				else: yielderrtemp += (modelingSys[proc+'_'+modTag]*yieldtemp)**2 #(addSys*(Nelectron+Nmuon))**2 --> correlated across e/m
				yielderrtemp += (elcorrdSys*yieldtempE)**2+(mucorrdSys*yieldtempM)**2
			yielderrtemp = math.sqrt(yielderrtemp)
			if proc==dataName: row.append(' & '+str(int(yieldsAll[histoPrefixE+proc]+yieldsAll[histoPrefixM+proc])))
			else: row.append(' & '+str(round_sig(yieldtemp,5))+' $\pm$ '+str(round_sig(yielderrtemp,2)))
		row.append('\\\\')
		table.append(row)
	
#systematics
table.append(['break'])
table.append(['','Systematics'])
table.append(['break'])
for proc in bkgProcList+sigProcList:
	table.append([proc]+[chn for chn in channels]+['\\\\'])
	systematicList = sorted([hist[hist.find(proc)+len(proc)+2:hist.find(upTag)] for hist in yieldsAll.keys() if channels[0] in hist and '__'+proc+'__' in hist and upTag in hist])
	for syst in systematicList:
		for ud in [upTag,downTag]:
			row = [syst+ud]
			for chn in channels:
				histoPrefix = allhists[chn][0][:allhists[chn][0].find('__')+2]
				nomHist = histoPrefix+proc
				shpHist = histoPrefix+proc+'__'+syst+ud
				try: row.append(' & '+str(round(yieldsAll[shpHist]/(yieldsAll[nomHist]+1e-20),2)))
				except:
					if proc != 'qcd': print "Missing",proc,"for channel:",chn,"and systematic:",syst
					pass
			row.append('\\\\')
			table.append(row)
	table.append(['break'])

postFix = ''
if addShapes: postFix+='_addShps'
if not addCRsys: postFix+='_noCRunc'
out=open(templateDir+'/'+combinefile.replace('templates','yields').replace('.root','_rebinned_stat'+str(stat).replace('.','p'))+postFix+'.txt','w')
printTable(table,out)

# print "       WRITING SUMMARY TEMPLATES: "
# lumiStr = combinefile.split('_')[-1][:-7]
# for signal in sigProcList:
# 	print "              ... "+signal
# 	yldRfileName = templateDir+'/templates_YLD_'+signal+'_'+lumiStr+'fb_rebinned_stat'+str(stat).replace('.','p')+'.root'
# 	yldRfile = TFile(yldRfileName,'RECREATE')
# 	for isEM in isEMlist:		
# 		for proc in bkgProcList+[dataName,signal]:
# 			yldHists = {}
# 			yldHists[isEM+proc]=TH1F('YLD_'+lumiStr+'fb_'+isEM+'_nH0p_nW0p_nB0p_nJ0p__'+proc.replace(signal,'sig').replace('data','DATA'),'',len(channels)/2,0,len(channels)/2)
# 			systematicList = sorted([hist[hist.find(proc)+len(proc)+2:hist.find(upTag)] for hist in yieldsAll.keys() if channels[0] in hist and '__'+proc+'__' in hist and upTag in hist])
# 			for syst in systematicList:
# 				for ud in [upTag,downTag]: yldHists[isEM+proc+syst+ud]=TH1F('YLD_'+lumiStr+'fb_'+isEM+'_nH0p_nW0p_nB0p_nJ0p__'+proc.replace(signal,'sig').replace('data','DATA')+'__'+syst+ud,'',len(channels)/2,0,len(channels)/2)
# 			ibin = 1
# 			for chn in channels:
# 				if isEM not in chn: continue
# 				nHtag = chn.split('_')[-4][2:]
# 				nWtag = chn.split('_')[-3][2:]
# 				nbtag = chn.split('_')[-2][2:]
# 				njets = chn.split('_')[-1][2:]
# 				binStr = ''
# 				if nHtag!='0p':
# 					if '1b' in nHtag: binStr+='H1b/'
# 					elif '2b' in nHtag: binStr+='H2b/'
# 					else: binStr+=nHtag+'H/'
# 				if nWtag!='0p' or 'b' in nHtag:
# 					if 'p' in nWtag: binStr+='#geq'+nWtag[:-1]+'W/'
# 					else: binStr+=nWtag+'W/'
# 				if nbtag!='0p':
# 					if 'p' in nbtag: binStr+='#geq'+nbtag[:-1]+'b/'
# 					else: binStr+=nbtag+'b/'
# 				if njets!='3p' and len(njetslist)>1:
# 					if 'p' in njets: binStr+='#geq'+njets[:-1]+'j'
# 					else: binStr+=njets+'j'
# 				if binStr.endswith('/'): binStr=binStr[:-1]
# 				histoPrefix = allhists[chn][0][:allhists[chn][0].find('__')+2]
# 				try: 
# 					yldTemp = yieldsAll[histoPrefix+proc]
# 					yldErrTemp = yieldsErrsAll[histoPrefix+proc]
# 				except: 
# 					print "Missing "+proc+" for channel: "+chn+" (setting yield to zero!!!)"
# 					yldTemp = 0
# 					yldErrTemp = 0
# 				yldHists[isEM+proc].SetBinContent(ibin,yldTemp)
# 				yldHists[isEM+proc].SetBinError(ibin,yldErrTemp)
# 				yldHists[isEM+proc].GetXaxis().SetBinLabel(ibin,binStr)
# 				for syst in systematicList:
# 					for ud in [upTag,downTag]:
# 						try: yldTemp = yieldsAll[histoPrefix+proc+'__'+syst+ud]
# 						except: yldTemp = 0
# 						yldHists[isEM+proc+syst+ud].SetBinContent(ibin,yldTemp)
# 						yldHists[isEM+proc+syst+ud].GetXaxis().SetBinLabel(ibin,binStr)
# 				ibin+=1
# 			yldHists[isEM+proc].Write()
# 			for syst in systematicList:
# 				for ud in [upTag,downTag]: yldHists[isEM+proc+syst+ud].Write()
# 	yldRfile.Close()

print("--- %s minutes ---" % (round((time.time() - start_time)/60,2)))



