#!/usr/bin/python

from ROOT import gROOT,TGraph,TCanvas,TLatex,TLine,TLegend
import os,sys,math,itertools,json
from numpy import linspace
from array import array

gROOT.SetBatch(1)

from tdrStyle import *
setTDRStyle()

lumiPlot = '35.9'
lumiStr = '36p814'
distribution = 'minMlb'
signal = 'TT'
chiral = ''
limitDir='/user_data/jhogan/CMSSW_7_4_14/src/tptp_2016/thetaLimits/limits'#_beforeRebinning/'
postfix = '' # for plot names in order to save them as different files
isRebinned='_rebinned_stat0p3'
xrange_min=900.
xrange_max=1800.
yrange_min=.0003+.01
yrange_max=3.05

massPoints = [900,1000,1100,1200,1300,1400,1500,1600,1700,1800]
mass = array('d', massPoints)
masserr = array('d', [0]*len(massPoints))
mass_str = [str(item) for item in massPoints]

theory_xsec_dicts = {'900':0.0903,'1000':0.0440,'1100':0.0224,'1200':0.0118,'1300':0.00639,'1400':0.00354,'1500':0.00200,'1600':0.001148,'1700':0.000666,'1800':0.000391}#'800':0.196,
theory_xsec = [theory_xsec_dicts[item] for item in mass_str]
xsec = array('d', [1]*len(massPoints)) # scales the limits

theory = TGraph(len(mass))
for i in range(len(mass)):
	theory.SetPoint(i, mass[i], theory_xsec[i])

#cutStrings = [x for x in os.walk(limitDir).next()[1]]
cutStrings = ['templates_M17ak8/deltaRAK8_bW0p5_tZ0p25_tH0p25','templates_M17ak8/minMlbST_bW0p5_tZ0p25_tH0p25','templates_M17/minMlb_bW0p5_tZ0p25_tH0p25','templates_M17/minMlbST_bW0p5_tZ0p25_tH0p25','templates_M17/ST_bW0p5_tZ0p25_tH0p25']
# cutStrings = ['lep50_MET80_NJets5_NBJets0_DR0.75_1jet300_2jet150_3jet0',
# 			  'lep80_MET100_NJets4_NBJets0_DR1_1jet200_2jet90_3jet0',
# 			  ]

bestSelection = 'lep80_MET100_NJets4_NBJets0_DR1_1jet200_2jet90_3jet0'#'lep50_MET100_NJets4_NBJets0_DR0.75_1jet300_2jet150_3jet0'
additionalSelToCompare = []#['lep50_MET100_NJets5_NBJets0_DR1_1jet300_2jet90_3jet0']

#compareCuts = ['lep50_MET100_NJets5_NBJets0_DR1_1jet300_2jet90_3jet0','lep80_MET100_NJets4_NBJets0_DR1_1jet200_2jet90_3jet0']
compareCuts = ['templates_M17ak8/deltaRAK8_bW0p5_tZ0p25_tH0p25','templates_M17ak8/minMlbST_bW0p5_tZ0p25_tH0p25','templates_M17/minMlb_bW0p5_tZ0p25_tH0p25','templates_M17/minMlbST_bW0p5_tZ0p25_tH0p25','templates_M17/ST_bW0p5_tZ0p25_tH0p25']

significance = {}
ind=0
maxSignificanceCut = ''
minSignificanceCut = ''
maxSignificance = -1
minSignificance = 1e9
for cutString in cutStrings:
	if '_bW0p5_' not in cutString: continue
	distribution = (cutString.split('/')[-1]).split('_')[0]
	plotLimits = True
	for kutle in mass_str:
		if not os.path.exists(limitDir+'/'+cutString+'/discovery/templates_'+distribution+'_'+signal+'M'+kutle+chiral+'_bW0p5_tZ0p25_tH0p25_'+lumiStr+'fb'+isRebinned+'.json'): 
			plotLimits = False
	if not plotLimits: continue
	if (ind % 500)==0: 
		print "Finished",ind,"out of",len(cutStrings) 
		print cutString

	significance[cutString] = TGraph(len(mass))

	for i in range(len(mass)):
		try:
			fsig = open(limitDir+'/'+cutString+'/discovery/templates_'+distribution+'_'+signal+'M'+mass_str[i]+chiral+'_bW0p5_tZ0p25_tH0p25_'+lumiStr+'fb'+isRebinned+'.json')
			linesSig = json.load(fsig)
			fsig.close()
			expSig = linesSig[0][0]
		except: 
			print "NO JSON:",cutString,mass[i]
			pass
		if mass[i]==1000:
			if maxSignificance<expSig: 
				maxSignificanceCut=cutString
				maxSignificance=expSig
			if minSignificance>expSig: 
				minSignificanceCut=cutString
				minSignificance=expSig
		significance[cutString].SetPoint(i,mass[i],expSig)

	ind+=1							
	significance[cutString].SetLineColor(ind)
	significance[cutString].SetLineWidth(2)
	significance[cutString].SetLineStyle(1)
#os._exit(1)

print "********************************************************************************"
print "Run over", ind, "sets of cuts"
print "********************************************************************************"
print "The best set of cuts are ", maxSignificanceCut
print "with significance", maxSignificance
print "********************************************************************************"
print "The worst set of cuts are ", minSignificanceCut
print "with significance", minSignificance
                                               
c0 = TCanvas("c0","Limits", 1000, 800)
c0.SetBottomMargin(0.15)
c0.SetRightMargin(0.06)
#c0.SetLogy()
	
significance[maxSignificanceCut].Draw('AL')
significance[maxSignificanceCut].GetYaxis().SetRangeUser(yrange_min,yrange_max)
significance[maxSignificanceCut].GetXaxis().SetRangeUser(xrange_min,xrange_max)
if 'X53' in signal:
	significance[maxSignificanceCut].GetXaxis().SetTitle('X_{5/3} mass [GeV]')
	significance[maxSignificanceCut].GetYaxis().SetTitle('Expected Significance - '+chiral.replace('left','LH').replace('right','RH'))
else:
	significance[maxSignificanceCut].GetXaxis().SetTitle('T mass [GeV]')
	significance[maxSignificanceCut].GetYaxis().SetTitle('Expected Significance ')

for key in significance.keys():
	if key == maxSignificanceCut: continue
	significance[key].Draw("same")

# sensitivityline = TLine(sensitivity,yrange_min,sensitivity,yrange_max)
# sensitivityline.Draw("same")
# insensitivityline = TLine(insensitivity,yrange_min,insensitivity,yrange_max)
# insensitivityline.Draw("same")

prelimtex = TLatex()
prelimtex.SetNDC()
prelimtex.SetTextSize(0.03)
prelimtex.SetTextAlign(11) # align right
prelimtex.DrawLatex(0.58, 0.96, "CMS Preliminary, " + str(lumiPlot) + " fb^{-1} (13 TeV)")

folder='.'
if not os.path.exists(folder+'/'+limitDir.split('/')[-1]+'plots'): os.system('mkdir '+folder+'/'+limitDir.split('/')[-1]+'plots')
c0.SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+isRebinned+'.pdf')
c0.SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+isRebinned+'.jpg')
c0.SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+isRebinned+'.eps')
#os._exit(1)

legends = {}
legends['comp']  = TLegend(.6,.70,.93,.93) # for varying discriminants
legends['lep']  = TLegend(.3,.70,.93,.93) # for varying lepPt
legends['MET']  = TLegend(.3,.70,.93,.93) # for varying MET
legends['1jet'] = TLegend(.3,.72,.93,.93) # for varying jet1Pts
legends['2jet'] = TLegend(.3,.76,.93,.93) # for varying jet2Pts
legends['3jet'] = TLegend(.3,.70,.93,.93) # for varying jet3Pts
legends['NJets']= TLegend(.3,.82,.93,.93) # for varying Njets
legends['DR']   = TLegend(.3,.76,.93,.93) # for varying DRs

canvs = {}
'''
for sel in bestSelection.split('_'):
	if 'NBJets' in sel or '3jet' in sel: continue
	variedCut = ''
	for key in legends.keys():
		if key in sel: variedCut = key
	postfix = 'vary'+variedCut

	cutStrs = sorted([item for item in significance.keys() if (bestSelection.split(sel)[0] in item and bestSelection.split(sel)[1] in item)], key=lambda cut: float(cut[cut.find(variedCut)+len(variedCut):cut.find(variedCut)+cut[cut.find(variedCut):].find('_')]))
	cutStrs = cutStrs+additionalSelToCompare
		
	canvs[variedCut] = TCanvas(variedCut,"Limits", 1000, 800)
	canvs[variedCut].SetBottomMargin(0.15)
	canvs[variedCut].SetRightMargin(0.06)
	#canvs[variedCut].SetLogy()
	
	significance[cutStrs[0]].Draw('AL')
	significance[cutStrs[0]].SetLineColor(1)
	significance[cutStrs[0]].SetLineWidth(2)
	significance[cutStrs[0]].SetLineStyle(1)
	significance[cutStrs[0]].GetYaxis().SetRangeUser(yrange_min,yrange_max)
	significance[cutStrs[0]].GetXaxis().SetRangeUser(xrange_min,xrange_max)
	if 'X53' in signal:
		significance[cutStrs[0]].GetXaxis().SetTitle('X_{5/3} mass [GeV]')
		significance[cutStrs[0]].GetYaxis().SetTitle('Expected Significance - '+chiral.replace('left','LH').replace('right','RH'))
	else:
		significance[cutStrs[0]].GetXaxis().SetTitle('T mass [GeV]')
		significance[cutStrs[0]].GetYaxis().SetTitle('Expected Significance')
		
	ind=2
	for cutString in cutStrs:
		if cutString == cutStrs[0]: continue
		#if not (bestSelection.split(sel)[0] in cutString and bestSelection.split(sel)[1] in cutString): continue						
		significance[cutString].SetLineColor(ind)
		significance[cutString].SetLineWidth(2)
		significance[cutString].SetLineStyle(1)
		significance[cutString].Draw("same")
		ind+=1
	
	for cutString in cutStrs:
		#if not (bestSelection.split(sel)[0] in cutString and bestSelection.split(sel)[1] in cutString): continue
		legendStr=cutString.replace('_NBJets0','').replace('_1jet','_Ljet').replace('_2jet','_SLjet').replace('_3jet0','')
		try: legends[variedCut].AddEntry(significance[cutString], legendStr, "l")
		except: 
			print "Couldn't add the legend !!!!"
			pass
	
# 	sensitivityline = TLine(sensitivity,yrange_min,sensitivity,yrange_max)
# 	sensitivityline.SetLineStyle(2)
# 	sensitivityline.Draw("same")
# 	insensitivityline = TLine(insensitivity,yrange_min,insensitivity,yrange_max)
# 	insensitivityline.Draw("same")
# 	insensitivityline.SetLineStyle(2)

	prelimtex = TLatex()
	prelimtex.SetNDC()
	prelimtex.SetTextSize(0.03)
	prelimtex.SetTextAlign(11) # align right
	prelimtex.DrawLatex(0.58, 0.96, "CMS Preliminary, " + str(lumiPlot) + " fb^{-1} (13 TeV)")

	legends[variedCut].SetShadowColor(0);
	legends[variedCut].SetFillColor(0);
	legends[variedCut].SetLineColor(0);
	legends[variedCut].Draw()                                               
	canvs[variedCut].RedrawAxis()

	folder='.'
	if not os.path.exists(folder+'/'+limitDir.split('/')[-1]+'plots'): os.system('mkdir '+folder+'/'+limitDir.split('/')[-1]+'plots')
	canvs[variedCut].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.pdf')
	canvs[variedCut].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.jpg')
	canvs[variedCut].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.eps')
'''
variedCut = 'discrim'
postfix = 'comp'
cutStrs = compareCuts
	
canvs['comp'] = TCanvas(variedCut,"Limits", 1000, 800)
canvs['comp'].SetBottomMargin(0.15)
canvs['comp'].SetRightMargin(0.06)
#canvs[variedCut].SetLogy()

significance[cutStrs[0]].Draw('AL')
significance[cutStrs[0]].SetLineColor(1)
significance[cutStrs[0]].SetLineWidth(2)
significance[cutStrs[0]].SetLineStyle(1)
significance[cutStrs[0]].GetYaxis().SetRangeUser(yrange_min,yrange_max)
significance[cutStrs[0]].GetXaxis().SetRangeUser(xrange_min,xrange_max)
if 'X53' in signal:
	significance[cutStrs[0]].GetXaxis().SetTitle('X_{5/3} mass [GeV]')
	significance[cutStrs[0]].GetYaxis().SetTitle('Expected Significance - '+chiral.replace('left','LH').replace('right','RH'))
else:
	significance[cutStrs[0]].GetXaxis().SetTitle('T mass [GeV]')
	significance[cutStrs[0]].GetYaxis().SetTitle('Expected Significance')
	
ind=2
for cutString in cutStrs:
	if cutString == cutStrs[0]: continue
	significance[cutString].SetLineColor(ind)
	significance[cutString].SetLineWidth(2)
	significance[cutString].SetLineStyle(1)
	significance[cutString].Draw("same")
	ind+=1

for cutString in cutStrs:
	#legendStr=cutString.replace('_NBJets0','').replace('_1jet','_Ljet').replace('_2jet','_SLjet').replace('_3jet0','')
	legendStr=cutString.replace('_bW0p5_tZ0p25_tH0p25','').replace('templates_M17/','DRjet2, ').replace('templates_M17ak8/','DRak8, ')
	legends['comp'].AddEntry(significance[cutString], legendStr, "l")
	#except: 
	#	print "Couldn't add the legend !!!!"
	#	pass

prelimtex = TLatex()
prelimtex.SetNDC()
prelimtex.SetTextSize(0.03)
prelimtex.SetTextAlign(11) # align right
prelimtex.DrawLatex(0.58, 0.96, "CMS Preliminary, " + str(lumiPlot) + " fb^{-1} (13 TeV)")

legends['comp'].SetShadowColor(0);
legends['comp'].SetFillColor(0);
legends['comp'].SetLineColor(0);
legends['comp'].Draw()                                               
canvs['comp'].RedrawAxis()

folder='.'
if not os.path.exists(folder+'/'+limitDir.split('/')[-1]+'plots'): os.system('mkdir '+folder+'/'+limitDir.split('/')[-1]+'plots')
canvs['comp'].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.pdf')
canvs['comp'].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.jpg')
canvs['comp'].SaveAs(folder+'/'+limitDir.split('/')[-1]+'plots/PlotCombined'+distribution+postfix+limitDir.split('/')[-2]+'.eps')
