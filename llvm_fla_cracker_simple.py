import os
import copy
import sys

'''
	format: 
	space between two element

'''

LINE_IDX = 1
VAR_VAL = 0
CTRL_VAL = 0

LEFT_ALL = 2
LEFT_RELATION = 2
LEFT_RELVALUE = 3
LEFT_VARNAME = 1

FROMIDX = 1
TOIDX = 2

#build relation
VALUE_IN = 0
VALUE_OUT = 1
USE = 2


#ctrl_stack
CONTROL_NAME = 0
CONTROL_LINE_IDX = 1

GlobalBranchId = 0
GlobalLoopId = 0

TP_SIMOUT = "SimOut"
TP_CTRLVAR_DECL = ""
TP_CTRLVAR_SET = ""
TP_CTRL = "Ctrl"
TP_LB_L = ""
TP_LB_R = ""
TP_LBL_OUT = "LOut"
TP_LBR_OUT = "ROut"
TP_NEW_BR = "NEW_Br"

SCANTYPE_CTRL = "ctrl"
SCANTYPE_NORMAL = "Normal"
SCANTYPE_DECL = "decl"
SCANTYPE_VALUESET = "valueset"
SCANTYPE_NONE = "None"

SCAN_WHILE = "while"
SCAN_IF = "if"
SCAN_ELSE = "else"
SCAN_ELSEIF = "else if"
SCAN_SWITCH = "switch"
SCAN_CASE = "case"
SCAN_DO = "do"
SCAN_BREAK = "break"
SCAN_GOTO = "goto"

CSTK_DO = "do"
CSTK_WHILE = "while"
CSTK_GOTO = "goto"
CSTK_IF = "if"
CSTK_SWITCH = "switch"
CSTK_LBL = "{"
CSTK_LBR = "}"

log = 1

class PROG_STAT:
	CtrlStack = []
	VarSet = []
	VarVal = []
	Trace = []
	TraceProp = []
	LIdx = 0
	SimOut = []
	def __init__(self, argCtrlStack, argVarSet, argVarVal, argSimOut, argTrace, argTraceProp, argLIdx):
		self.CtrlStack = copy.deepcopy(argCtrlStack)
		self.VarSet = copy.deepcopy(argVarSet)
		self.VarVal = copy.deepcopy(argVarVal)
		self.Trace = copy.deepcopy(argTrace)
		self.TraceProp = copy.deepcopy(argTraceProp)
		self.SimOut = argSimOut
		self.LIdx = argLIdx

def Logging(warning):
	if log == 1:
		print "Log: %s" % warning


def ShortenLine(line):   # skip space and tab before a line
	RetStr = ""
	SpaceStarted = 0
	LineStarted = 0
	for i in range(len(line)):
		if LineStarted == 1:
			if line[i] == " ":
				if SpaceStarted == 1:
					continue
				else:
					RetStr += " "
					SpaceStarted = 1
					continue
			else:
				SpaceStarted = 0
				if line[i] == "\n" or line[i] == "\r":
					continue
				RetStr += line[i]
		else:
			if line[i] == " " or line[i] == "\t":
				continue
			else:
				LineStarted = 1
				RetStr += line[i]
	return RetStr

def ChopLine(line):   # chop a line into elements, for example: "a = 12;" -->  ["a", "=", "12"]
	line = ShortenLine(line)
	words = []
	tmp = ""
	StringCtrl = 0
	start = 0
	for c in line:
		if c == '"':
			StringCtrl = 1 - StringCtrl
			tmp += '"'
			continue
		elif StringCtrl == 1:
			tmp += c
		elif (c == " " or c == "\t") and tmp != "":
			words.append(tmp)
			tmp = ""
		else:
			if c != ";" and c != "\r" and c != "\n":
				tmp += c
			else:
				break
	if tmp != "":
		words.append(tmp)
	return words

def StrToValue(word):
	validnum = "-0123456789"
	for c in word:
		if c not in validnum:
			return ""
	return int(word)

def WordScan(Arg_Str):  # scan a line
	if not isinstance(Arg_Str, str):
		print "too many lines for WordScan"
		exit()

	DeclKeyWords = ["unsigned int", "signed int",  "unsigned char", "signed char", "byte", "DWORD", "int", "char"]
	CtrlKeyWords = [SCAN_DO, SCAN_WHILE, SCAN_ELSEIF, SCAN_SWITCH, SCAN_ELSE, SCAN_IF, SCAN_GOTO, SCAN_CASE, SCAN_BREAK]

	words = ChopLine(Arg_Str)
	ScanInfo = []
	if words != []:
		if words[0] in DeclKeyWords or (len(words) > 1 and (words[0] + " " + words[1]) in DeclKeyWords):
			ScanInfo.append(SCANTYPE_DECL)
			ScanInfo.append(words[-1])
		elif words[0] in CtrlKeyWords:
			ctrlidx = 1
			ctrl_name = words[0]
			if len(words) > 1:
				if (words[0] +" "+ words[1]) in CtrlKeyWords:
					ctrl_name = words[0] + " " + words[1]
					ctrlidx = 2
			ScanInfo.append(SCANTYPE_CTRL)
			ScanInfo.append(ctrl_name)
			ScanInfo.append(words[ctrlidx:])
		elif len(words) > 1 and words[1] == "=":
			ScanInfo.append(SCANTYPE_VALUESET)
			ScanInfo.append(words[0])  #dst
			ScanInfo.append(words[2:]) # src
	 	else:
	 		ScanInfo.append(SCANTYPE_NORMAL)
	 		ScanInfo.append(words)
	if ScanInfo == []:
		ScanInfo.append(SCANTYPE_NONE)
 	return ScanInfo

def IsNameLett(str):
	ValidSet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_1234567890"
	for c in str:
		if c not in ValidSet:
			return False
	if ValidSet.find(str[0]) < ValidSet.find("1"):
		return True
	else:
		return False

def BuildRelation(LineBuf):  #scan the whole codetext, find the relations between the variables in the text. 
	VarNameSet = []
	VarRelation = []
	for line in LineBuf:
		line = ShortenLine(line)
		if line == "":
			continue
		ScanInfo = WordScan(line)

		if ScanInfo == []:
			continue

		HeadType = ScanInfo[0]
		if HeadType == SCANTYPE_DECL:

			VarNameSet.append(ScanInfo[1])
			VarRelation.append([[],[],0])
		if HeadType == SCANTYPE_VALUESET:
			src = ScanInfo[2]
			dst = ScanInfo[1]
			if IsNameLett(dst) and dst not in VarNameSet:
				VarNameSet.append(dst)
				VarRelation.append([[], [], 0])
			if len(src) == 1:
				src = src[0]
				if IsNameLett(src) and src not in VarNameSet:
					VarNameSet.append(src)
					VarRelation.append([[], [], 0])
				
				if dst in VarNameSet:
					IdxDst = VarNameSet.index(dst)
					if src in VarNameSet:
						if src not in VarRelation[IdxDst][VALUE_IN]:
							IdxSrc = VarNameSet.index(src)
							VarRelation[IdxSrc][VALUE_OUT].append(dst)
							VarRelation[IdxDst][VALUE_IN].append(src)
					elif StrToValue(src) != "":
						VarRelation[IdxDst][VALUE_IN].append(0)   #zero represents imm value
		if HeadType == SCANTYPE_CTRL:
			if "(" in ScanInfo[2]:
				idx = ScanInfo[2].index("(")
				if idx != -1:
					var = ScanInfo[2][idx + 1]
					if var in VarNameSet:
						VarRelation[VarNameSet.index(var)][USE] += 1
	CtrlVar = []

	for i in range(len(VarNameSet)):
		if VarRelation[i][VALUE_OUT] == []:
			if VarRelation[i][VALUE_IN] != [] and 0 in VarRelation[i][VALUE_IN] and VarRelation[i][USE] > 0:
				CtrlVar.append(VarNameSet[i])

	Logging("build relation completed...")

	return VarNameSet, VarRelation, CtrlVar

def GetSimulationVarSet(RelationResult):  # get the variable that controls the flow and related vars to it. 
	SensitiveVars = []
	VarNameSet = RelationResult[0]
	VarRelation = RelationResult[1]
	CtrlVar = RelationResult[2]

	if len(CtrlVar) == 0:
		Logging("no control variable found... exit")
		exit()

	tmpCtrlVar = CtrlVar[0]
	if len(CtrlVar) > 1:
		print "more than one control variable: %s    exit" % CtrlVar
		user_define = raw_input("manually input the ctrl var( or just enter to try your luck ) >>> ")
		if user_define == "":
			max_ref = 0
			RefIdx = 0
			for c in CtrlVar:
				t = VarRelation[VarNameSet.index(c)][USE]
				if t > max_ref:
					max_ref = t
					RefIdx = CtrlVar.index(c)
			tmpCtrlVar = CtrlVar[RefIdx]
		else:
			if user_define in CtrlVar:
				tmpCtrlVar = user_define
			else:
				Logging("wrong input...")
				exit() 

	CtrlVar = tmpCtrlVar

	SensitiveVars.append(CtrlVar)
	CtrlVarRelation = VarRelation[VarNameSet.index(CtrlVar)]
	for item in CtrlVarRelation[VALUE_IN]:
		if item != 0:
			SensitiveVars.append(item)
	Logging("control var is: %s" % CtrlVar)
	Logging("get simulation varset completed...")
	Logging("sensitive vars : %s"  % SensitiveVars)
	return SensitiveVars

def ReadByLineAndFormat(arg_str):  #read the file line by line
	f = open(arg_str, "r")
	LineBuf = []
	while 1:
		line = f.readline()
		if not line:
			break
		if line != "":
			LineBuf.append(line)
	f.close()
	return LineBuf

def VarMatchCondition(value, relation, relvalue):
	relvalue = StrToValue(relvalue)
	if "" == relvalue:
		Logging("wrong relation format, in VarMatchCondition...")
		return ""
	if relation == "==":
		if value == relvalue:
			return 1
	if relation == "!=":
		if value != relvalue:
			return 1
	if relation == ">=":
		if value >= relvalue:
			return 1
	if relation == ">":
		if value > relvalue:
			return 1
	if relation == "<":
		if value < relvalue:
			return 1
	if relation == "<=":
		if value <= relvalue:
			return 1
	return 0

def FindNextBlock(LineBuf, lineidx):   #find next code BBL 
	tmplineidx = lineidx + 1
	largeB = 0
	while 1:
		words = ChopLine(LineBuf[tmplineidx])
		tmplineidx += 1
		if words != []:
			if len(words) == 1:
				if words[0] == "{":
					largeB += 1
				elif words[0] == "}":
					largeB -= 1		
			if largeB == 0:
				break
	while 1:
		words = ChopLine(LineBuf[tmplineidx])
		if words != []:
			break
		tmplineidx += 1

	return tmplineidx

def FindMatchingCase(LineBuf, lineidx, CmpVal):   #find the matching case of a switch 
	largeB = 0
	endlineidx = FindNextBlock(LineBuf, lineidx)
	for idx in range(lineidx + 1, endlineidx):
		ScanInfo = WordScan(LineBuf[idx])
		if ScanInfo[0] == SCANTYPE_CTRL and ScanInfo[1] == SCAN_CASE:
			valuestr = ScanInfo[2][0][:-1]
			
			v = StrToValue(valuestr)
			if CmpVal == v and largeB < 2:
				return idx
		if ScanInfo[0] == SCANTYPE_NORMAL:
			if len(ScanInfo[1]) == 1:
				if ScanInfo[1][0] == "{":
					largeB += 1
				elif ScanInfo[1][0] == "}":
					largeB -= 1	
	return ""

def SkipIf(LineBuf, lineidx):  #skip the if structure
	tmplineidx = lineidx
	while 1:
		tmplineidx = FindNextBlock(LineBuf, tmplineidx)
		words = ChopLine(LineBuf[tmplineidx])
		#Logging("tmp skip %d " % (tmplineidx))
		if words == [] or words[0] != "else":
			Logging("skipif to line @ %d" % (tmplineidx))
			return tmplineidx

def SensVarRelatedinIf(LineBuf, lineidx, VarSet):   # whether the sensitive variables are involved in the "if" structure.
	startidx = lineidx
	endidx = SkipIf(LineBuf, lineidx)
	sensi = False
	for i in range(startidx, endidx):
		words = ChopLine(LineBuf[i])
		for var in VarSet:
			if var in words:
				sensi = True
				break
	return sensi


def CplxSimulation(LineBuf, ProgInitStat):
	global GlobalLoopId, GlobalBranchId

	#CtrlStack = copy.deepcopy(ProgInitStat.CtrlStack)   #  ["do", XXX], ["while", XXX], ["if", XXX], ["switch", XXX], ["{", xxx]
	#VarSet = copy.deepcopy(ProgInitStat.VarSet)
	VarVal = copy.deepcopy(ProgInitStat.VarVal)
	#Trace = copy.deepcopy(ProgInitStat.Trace)    # [ val, lineidx], [ xxx, xxx]
	#TraceProp = copy.deepcopy(ProgInitStat.TraceProp)   # ["SimOut", ""]
	
	VarSet = ProgInitStat.VarSet
	CtrlStack = ProgInitStat.CtrlStack
 	Trace = ProgInitStat.Trace
 	TraceProp = ProgInitStat.TraceProp
	CtrlVar = VarSet[CTRL_VAL]

	Loop = []  # ["Loop_1", fromidx, toidx]
	#BranchStack = []   # [[varvalstat, ctrlstack, xxx], [varvalstat, controlstack, xxx], ]    when branch, 0 first  1 next
	#SimOut = []   #[line, lineidx]
	SimOut = ProgInitStat.SimOut
	lineidx = ProgInitStat.LIdx

	MaxIdx = len(LineBuf)
	preidx = -1

	ThisBranchId = GlobalBranchId

	Trace.append("Br %d started..." % ThisBranchId)
	TraceProp.append(TP_NEW_BR)

	while lineidx < MaxIdx:
		if preidx == lineidx:
			Logging("processing stuck...")
			return SimOut, Loop

		preidx = lineidx
		Logging("------------------")
		Logging("line:" + str(lineidx))
		line =  ShortenLine(LineBuf[lineidx])
		Stat = [VarVal[CTRL_VAL], lineidx]
#		Logging("trace before: " + str(Trace[-1]))
		Logging("ctrl stack:" + str(CtrlStack))
#-----------------------------------------------check loop
		if Stat in Trace:  # loop found
			Logging("loop found, stat:" + str(Stat))
			TmpTraceProp = copy.deepcopy(TraceProp)
			fromLineIdx = 0
			toLineIdx = 0
			while 1:   				  # fromidx
				if TmpTraceProp != []:
					label = TmpTraceProp.pop()
				else:
					Logging("wrong identified loop...")
					exit()
				if label == TP_SIMOUT:
					fromLineIdx = Trace[len(TmpTraceProp)][LINE_IDX]
					break
					
			loopidx = Trace.index(Stat)
			for i in range(loopidx, len(TraceProp)):  # toidx
				if TraceProp[i] == TP_SIMOUT:
					toLineIdx = Trace[i][LINE_IDX]
					break

			LoopId = "Loop_" + str(GlobalBranchId)
			GlobalLoopId += 1

			for i in range(len(SimOut)):
				if SimOut[i][LINE_IDX] == toLineIdx and SimOut[i][2] == VarVal[CTRL_VAL]:
					SimOut.insert(i, [LoopId + ":", -1, VarVal[CTRL_VAL]])
					Logging("insert: %s" % str(SimOut[i]))
					break

			SimOut.append(["goto " + LoopId + ";", -1, VarVal[CTRL_VAL]])

			Loop.append(["Loop_" + str(GlobalBranchId), fromLineIdx, toLineIdx])

			Logging("loop found: line %d ---> line %d" %(fromLineIdx, toLineIdx))
			break   #loop found, quit simulating...
#*******************
		ScanInfo = WordScan(line)

		if ScanInfo[0] == SCANTYPE_NONE:
			lineidx += 1
			continue

		HeadType = ScanInfo[0]
		Logging(HeadType +", " + line)
		if SCANTYPE_DECL == HeadType:
			if ScanInfo[1] in VarSet:	
				Logging("skip declaration... %s " % ScanInfo[1])
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_CTRLVAR_DECL)
			else:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_SIMOUT)
				SimOut.append([line, lineidx, VarVal[CTRL_VAL]])
			lineidx += 1

		if SCANTYPE_VALUESET == HeadType:    #if var is in sensitive var set then simulate, if not, output it. 
			dst = ScanInfo[1]
			if dst in VarSet:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_CTRLVAR_SET)
				src = ScanInfo[2]
				if len(src) == 1:
					val = StrToValue(src[0])
					if val != "":
						VarVal[VarSet.index(dst)] = val    #imm set
					elif src[0] in VarSet:
						VarVal[VarSet.index(dst)] = VarVal[VarSet.index(src[0])]  #var set
				else:
					print "var not resolved:   %s" % line
			else:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_SIMOUT)
				SimOut.append([line, lineidx, VarVal[CTRL_VAL]])
			lineidx += 1

		if SCANTYPE_CTRL == HeadType:	
			if ScanInfo[1] == SCAN_IF or ScanInfo[1] == SCAN_ELSEIF:
				var = ScanInfo[LEFT_ALL][LEFT_VARNAME]
				if var in VarSet:     # condition can be resolved. 
					Trace.append([VarVal[CTRL_VAL], lineidx])
					TraceProp.append(TP_CTRL)
					vv = VarVal[VarSet.index(var)]
					if vv != "":
						if VarMatchCondition(vv, ScanInfo[LEFT_ALL][LEFT_RELATION], ScanInfo[LEFT_ALL][LEFT_RELVALUE]) == 1:
							Logging("if matched : %d %s %s" % (vv, ScanInfo[LEFT_ALL][LEFT_RELATION], ScanInfo[LEFT_ALL][LEFT_RELVALUE]))
							CtrlStack.append([CSTK_IF, lineidx])
							lineidx += 1
						else:
							lineidx = FindNextBlock(LineBuf, lineidx)
							Logging("try next if branch.. @ %d" % (lineidx) )
					else:
						print "use %s before initialization. " % var
						exit()
				else:   # cannot be resolved.   ASSUME: all if is related with sensitive vars
					if ScanInfo[1] == SCAN_IF and not SensVarRelatedinIf(LineBuf, lineidx, VarSet):
						Logging("if branch not sensitive... @ line %d" % lineidx)
						if_endidx = SkipIf(LineBuf, lineidx)
						for i in range(lineidx, if_endidx):
							Trace.append([VarVal[CTRL_VAL], i])
							TraceProp.append(TP_SIMOUT)
							SimOut.append([ShortenLine(LineBuf[i]), i, VarVal[CTRL_VAL]])
						lineidx =  if_endidx
					else:
						Logging("UNRESOLVED BRANCH!!!!!! @line %d" % (lineidx))
						
						Trace.append([VarVal[CTRL_VAL], lineidx])
						TraceProp.append(TP_SIMOUT)
						SimOut.append([line[ line.find("if"): ], lineidx, VarVal[CTRL_VAL]])
						SimOut.append(["{", -1, VarVal[CTRL_VAL]])
						
						GlobalBranchId += 1
						TmpProgStat = PROG_STAT(CtrlStack, VarSet, VarVal, SimOut, Trace, TraceProp, lineidx + 1)#argCtrlStack, argVarSet, argVarVal, argTrace, argTraceProp, argLayerId
						SubSimOut, SubLoop = CplxSimulation(LineBuf, TmpProgStat)
						#SimOut += SubSimOut
						Loop += SubLoop

						SimOut.append(["}", -1,  VarVal[CTRL_VAL]])
						SimOut.append(["else", -1,  VarVal[CTRL_VAL]])
						SimOut.append(["{", -1,  VarVal[CTRL_VAL]])

						lineidx = FindNextBlock(LineBuf, lineidx)

						GlobalBranchId += 1
						TmpProgStat = PROG_STAT(CtrlStack, VarSet, VarVal, SimOut, Trace, TraceProp, lineidx)#argCtrlStack, argVarSet, argVarVal, argTrace, argTraceProp, argLayerId
						SubSimOut, SubLoop = CplxSimulation(LineBuf, TmpProgStat)
						#SimOut += SubSimOut
						Loop += SubLoop	

						SimOut.append(["}", -1,  VarVal[CTRL_VAL]])

						Logging("UNRESOLVED BRANCH COMPLETED")
						break
					#lineidx = SkipCtrl(lineidx)
			if ScanInfo[1] == SCAN_ELSE:
				Trace.append([VarVal[0], lineidx])
				TraceProp.append(TP_CTRL)
				lineidx += 1

			if ScanInfo[1] == SCAN_SWITCH:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_CTRL)


				var = ScanInfo[LEFT_ALL][LEFT_VARNAME]
				if var in VarSet:   # ASSUME: var is in VarSet
					CmpVal = VarVal[VarSet.index(var)]
					tmplineidx = FindMatchingCase(LineBuf, lineidx, CmpVal)
					if tmplineidx == "":
						Logging("no matching %d @ line %d" % (CmpVal, lineidx))
						lineidx = FindNextBlock(LineBuf, lineidx)
					else:
						CtrlStack.append([CSTK_SWITCH, lineidx])
						CtrlStack.append([CSTK_LBL, lineidx + 1])
						lineidx = tmplineidx
						Logging("switch matched %d @ line %d" % (CmpVal, lineidx))
						
				else:
					Logging("*****************switch unkown var encountered... @line %d" % lineidx)
					exit()
			if ScanInfo[1] == SCAN_CASE:
				lineidx += 1
			if ScanInfo[1] == SCAN_WHILE:
				var = ScanInfo[LEFT_ALL][LEFT_VARNAME]
				Trace.append([ VarVal[CTRL_VAL], lineidx ])
				TraceProp.append(TP_CTRL)
				if var in VarSet:
					vv = VarVal[VarSet.index(var)]
					if VarMatchCondition(vv, ScanInfo[LEFT_ALL][LEFT_RELATION], ScanInfo[LEFT_ALL][LEFT_RELVALUE]) == 1:
						CtrlStack.append([CSTK_WHILE, lineidx])
						lineidx += 1
					else:
						lineidx = FindNextBlock(LineBuf, lineidx)
				elif var == "1":				
					CtrlStack.append([CSTK_WHILE, lineidx])
					lineidx += 1

			if ScanInfo[1] == SCAN_DO:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_CTRL)
				CtrlStack.append([CSTK_DO, lineidx])
				lineidx += 1
			if ScanInfo[1] == SCAN_GOTO:
				Logging("*********************goto encountered. %d" % lineidx)
				exit()
			if ScanInfo[1] == SCAN_BREAK:
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_CTRL)
				while 1:
					if CtrlStack == []:
						Logging("wrong 'break'... @ %d" % lineidx)
						exit()
					CtrlLabel = CtrlStack.pop()
					if CtrlLabel[CONTROL_NAME] == CSTK_WHILE or CtrlLabel[CONTROL_NAME] == CSTK_SWITCH or CtrlLabel[CONTROL_NAME] == CSTK_DO:
						lineidx = FindNextBlock(LineBuf, CtrlLabel[CONTROL_LINE_IDX])
						if CtrlLabel[CONTROL_NAME] == CSTK_DO:
							lineidx += 1
						break	
		elif SCANTYPE_NORMAL == HeadType:
#------------ check "{" and "}"
			if "{" == ScanInfo[1][0]:
				CtrlStack.append([CSTK_LBL, lineidx])
			elif "}" == ScanInfo[1][0]:
				if CtrlStack == [] or CtrlStack[-1][0] != CSTK_LBL:
					Logging("bracelet not matached...")
					exit()
				else:
					CtrlStack.pop()
#*******************
			else:
				SimOut.append([line, lineidx, VarVal[CTRL_VAL]])
				Trace.append([VarVal[CTRL_VAL], lineidx])
				TraceProp.append(TP_SIMOUT)
			lineidx += 1

		if HeadType != SCANTYPE_CTRL and CtrlStack != []:
			if CtrlStack[-1][CONTROL_NAME] == CSTK_IF:
				lineidx = SkipIf(LineBuf, CtrlStack[-1][CONTROL_LINE_IDX])
				CtrlStack.pop()
			elif CtrlStack[-1][CONTROL_NAME] == CSTK_WHILE:
				lineidx = CtrlStack[-1][CONTROL_LINE_IDX]  # repeat
				CtrlStack.pop()
			elif CtrlStack[-1][CONTROL_NAME] == CSTK_SWITCH:
				lineidx = FindNextBlock(LineBuf, CtrlStack[-1][LINE_IDX])
				CtrlStack.pop()
			elif CtrlStack[-1][CONTROL_NAME] == CSTK_DO:
				do_lineidx = CtrlStack[-1][LINE_IDX]
				CtrlStack.pop()
				lineidx = FindNextBlock(LineBuf, do_lineidx)
				ScanInfo = WordScan(ShortenLine(LineBuf[lineidx]))
				if ScanInfo[0] == SCANTYPE_CTRL and ScanInfo[1] == SCAN_WHILE:
					var = ScanInfo[LEFT_ALL][LEFT_VARNAME]
					if var in VarSet:
						Trace.append([VarVal[CTRL_VAL], lineidx])
						TraceProp.append("")
						vv = VarVal[VarSet.index(var)]
						if VarMatchCondition(vv, ScanInfo[LEFT_ALL][LEFT_RELATION], ScanInfo[LEFT_ALL][LEFT_RELVALUE]) == 1:
							lineidx = do_lineidx + 1
						else:
							lineidx += 1
					elif var == "1":
						lineidx = do_lineidx + 1
					else:
						print "unknown while type...@ line %d" % lineidx
						return SimOut, Loop
				else:
					Logging( "no 'while' to match 'do' on line %d..." % do_lineidx)
					exit()			
		Logging("trace: " + str(Trace[-1]))
		Logging("next: " + str(lineidx))
	Trace.append("Br %d completed..." % ThisBranchId)
	TraceProp.append(TP_NEW_BR)
	return SimOut, Loop

def FormatOutput(SimOut):
	Logging("formatting code...")
	tabnum = 0
	Output = []
	AddTab = 0
	for item in SimOut:
		if item[0] == "}":
			tabnum -= 1
		Output.append(tabnum * "\t" + item[0] + "\n")
		
		if item[0] == "{":
			tabnum += 1

	for i in range(len(Output)):
		item = Output[i]
		ScanInfo = WordScan(item)
		if ScanInfo[0] == SCANTYPE_CTRL and ScanInfo[1] != SCAN_GOTO and ShortenLine(Output[i + 1]) != "{":
			Output[i + 1] = "\t" + Output[i + 1]

	Logging("formatting completed.")
	return Output

def NormCode(lines):
	pass

def CodeSimulation(FileName):  #simulate the code, extract the original flow
	lines = ReadByLineAndFormat(FileName)   #Normalized code

	SimRet = BuildRelation(lines)
	SimVars = GetSimulationVarSet(SimRet)
	InitVarVals = []
	for i in range(len(SimVars)):
		InitVarVals.append("")

	InitStat = PROG_STAT([],SimVars, InitVarVals,[],[],[], 0)

	SimOut, Loop = CplxSimulation(lines, InitStat)
	Logging("Loop: %s" % str(Loop))
	return FormatOutput(SimOut)

#------------------------*****************************************

output =  CodeSimulation(sys.argv[1])

Logging("-----------------------*************************")

outputfile = sys.argv[2]
fileout = open(outputfile, "w")

for c in output:
	fileout.write(c)

fileout.close()
Logging("output to %s finished. \n\n" % outputfile)


