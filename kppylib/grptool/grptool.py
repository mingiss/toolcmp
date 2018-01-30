#!/usr/bin/env python
# coding=UTF-8

__author__ = "Mindaugas Piešina <mindaugas.piesina@vtex.lt>"
__version__ = "0.1"

# --------------------------------
"""
grptool.py
    Grupiškai vykdo nurodytą komandą grupei produkcijos failų
    Abstrakti klasė grupiniam atsitiktiniam gamybos failų testavimui
    Paveldima įrankiuose distcmp, toolcmp, webpdftest, flscmp

Syntax:
    python <inherited>.py <publisher>/<project>/<manuscript> [-n <number_of_ms>] [-o <sort_order>]
            [-t <type_of_ms>] [-i <includes>]

        <publisher>/<project>/<manuscript> - originalių failų kelias - X:/files_DB pakatalogis
        <manuscript> ir <project> galima praleisti, nurodyti <publisher>/<project> ar vien <publisher> be "/" – 
            tada bus analizuojami visų atitinkamo leidėjo projektų (vieno projekto) failai

        -n <number_of_ms> – 10, 20, -5, +5 – kiekvieno pasirinkto projekto testuojamų failų skaičius. 
            Jei priekyje skaičiaus minusas – testuoja paskutinius <number_of_ms> failų, jei pliusas – pirmus. 
            Jei pliuso ar minuso nėra – išbarsto atsitiktinai po visą sąrašą.
        -o <sort_order> - rikiavimo tvarka (taip pat ir žymint failus), pagal nutylėjimą – d:
            n – pagal failo vardą (<ms>),
            d – pagal originalo paskutinio kompiliavimo datą;
                rikiavimo tvarka keičiasi tik projekto viduje, patys projektai abiem ankstesniais atvejais 
                sugrupuoti ir išrikiuoti pagal projekto vardą;
            e - pagal nesutapimų koeficientą; šituo atveju išvedimo metu pagal projektus nebegrupuojama, 
                o žymėjimo metu failai būna išrikiuoti pagal vardą (-o n).

        Originalų atrinkimo kriterijai:
        -t <type_of_ms> - FM, C, C0, C3, * – dokumento tipas (viršelis, priešlapis, pagrindinis straipsnis).
            Tikrinimui atrenkami tik nurodyto tipo failai. Dokumento tipas nustatomas pagal raidines priesagas 
            failo vardo gale (AESCTE261FM1.tex, AESCTE261C3.tex). Galima nurodyti tik priesagos pradžią
            (pvz., nurodžius C, bus atrenkami failai AESCTE261C0.tex, AESCTE261C2.tex ir AESCTE261C3.tex)
            Jeigu parametras praleistas, bus tikrinami tik pagrindiniai straipsniai (be raidžių vardo gale).
            Jei nurodyta reikšmė * – bus tikrinami visų tipų failai.
        -i - naudojamas stilių/klasių failų, kurių įtaką norim patikrinti, sąrašas includes.mcl (lokalus ar šalia distcmp.py).
            Kompiliavimui bus atrenkami tik failai, kuriuose buvo panaudotas bent vienas iš tų stilių.
            Tikrinama pagal atitinkamą .fls failą (TeXInfo)
            
        Paveldėtos klasės konstruktoriuje po galimo naujų parametrų papildymo (m_Parser.add_option()) reikia iškviesti 
            ParseArgs() ir Init()

        Formuojamas originalių failų sąrašas X:/files_db/<publisher>/<project>/*/*, tikrinimui atrenkama reprezentatyvi 
            dalis failų – iš kiekvieno projekto/grupės po kelis. Pasirinktų tikrinimui failų originalai kopijuojami į 
            atitinkamus D:/local aplankus, kompiliuojami, kompiliavimo rezultatas testuojamas paveldėtos klasės
            tikrinimo metodu (pvz., kompiliavimo rezultatai lyginami su ankstesniais X:-e esančiais).

Changelog:
    2013-05-10  mp  initial creation
    2013-08-08  mp  PreCompileProc()/PostCompileProc() - includų lyginimas pagal .fls
    2013-08-08  mp  m_sMsName - pavienio failo testavimas
    2013-08-08  mp  includes.mcl
    
"""

# --------------------------------
import sys
import os
from datetime import datetime
import random
#import win32gui
import re
from optparse import OptionParser

sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/..")
# print sys.path

# from kplib.common.scanf import sscanf
from kppylib.env.common.kperr import KpError, KpException
# from TeXInfo import TeXInfo 


# --------------------------------
class GrpTool(object):
    m_sToolName = "grptool"
    
    m_fRatioSuccess = 1.0

# ----------------------------------------------
    def __init__(self):
        """ constructor; analyzes command line parameters and sets object properties """

        # ------------------------------
        """ publisher name string """
        self.m_sPublisherName = None
    
        """ list of project name strings """
        self.m_asProjectNames = []

        """ manuscript name """    
        self.m_sMsName = ""
        
        self.m_sDiffLogFName = "diff.log"
    
        self.m_Cfg = \
        {
            # path to original files
            'OrigPath': "X:/files_db",    
             
            # path to files being compiled
            'DestPath': "D:/local",       
          
            # os ('win'/'ux'), .cfg failo parametras ignoruojamas, 
            # po ReadCfg() nustatomas per jėgą pagal environment 
            'Os': "ux",
    
            # compilation command, parameter at the end – manuscript name
            # 'CompCmd': "vtex 2012 tex_dvi",
            # Jeigu norim, kad TeX-as nestabčiotų po klaidų    
            # 'CompCmd': "vtex 2012 pdftex.exe -fmt=latex -progname=latex -interaction=nonstopmode",
            'CompCmd': "vtex 2012 luatex -fmt=dvilualatex -progname=latex -interaction=nonstopmode",
    
            # comparison command, parameter at the end – manuscript name
            # darbiniam aplanke turi palikti failą diff.log,
            # kuris sėkmės atveju turi būti tuščias (komandos diff rezultatas)
            'DiffCmd': "Z:/data/texgr/utils/grptool/difcmp"
        }
    
        """ parameters depending on os """
        self.m_OsPars = \
        {
            'win':
            {
                # folders delimiter in a path
                'OsPathDelim': "\\",
    
                'Copy': "copy",
                'Del': "del /Q"
            },
            'ux':
            {
                'OsPathDelim': "/",
                'Copy': "cp",
                'Del': "rm"
            }
        }
       
        """ command line options, parsed in constructor """
        self.m_Options = {}
       
        """ rest command line parameters """
        self.m_Args = {}
          
        """ output of TeXInfo.py """
        self.m_TexStats = []
    
        """ contents of the folder self.m_Options.incl """
        self.m_Includes = {}
       
        self.m_bFirst = False # if True, selects first m_Options.number files of each project
        self.m_bLast = False # if True, selects last m_Options.number files of each project
        # both False -- random files selection
    
        """ list of dictionaries - properties and objects of original files """
        self.m_InFiles = [] # elements - dictionaries of following structure:
        # self.m_InFiles[ii]['proj_name']     # <project>, folder name
        # self.m_InFiles[ii]['ms_name']       # <manuscript>, subfolder name
        # self.m_InFiles[ii]['comments']      # string of error messages
        # self.m_InFiles[ii]['check_fl']      # marked for checking
        # self.m_InFiles[ii]['ratio']         # 1.0 -- success, 0.0 -- fail; dvi difference ratio for distcmp
        # self.m_InFiles[ii]['ignore']        # skip file flag
    
        self.m_iNumOfInFiles = 0 # size of m_InFiles[]
        self.m_iNumOfLiveFiles = 0 # number of files ready for checking
    
        # -----------------------------
        """ 
        list of dictionaries - groups of original files
        distcmp – different distributions
        toolcmp – projects  
        """
        self.m_InFileGroups = [] # former m_Distrs[] 
        # elements -- dictionaries of following structure:
        # self.m_InFileGroups[ii]['first_file']   # index of first m_InFiles[] of current distribution
        # self.m_InFileGroups[ii]['file_count']   # number of m_InFiles[] of current distribution
        # self.m_InFileGroups[ii]['proj_name']    # <project>, folder name
    
        # size of m_InFileGroups[]
        self.m_iNumOfGroups = 0 # former m_iNumOfDistrs 
    
        # -----------------------------
        self.m_LogFile = None # log file to duplicate stdout messages
        self.m_sCurPath = None # current working path of distcmp.py
    
        tool_path_split = sys.argv[0].split("\\")
        tool_path_split = tool_path_split[-1].split("/")
        tool_path_split = tool_path_split[-1].split(".")
        del tool_path_split[-1]
        self.m_sToolName = ".".join(tool_path_split) # "grptool"
    
        self.m_sLogFileName = self.m_sToolName + ".log" # log file name
        self.m_sErrLogFileName = self.m_sToolName + ".err.log" # error log file

        # ------------------------------
#       self.m_LogFile = open(self.m_sLogFileName, 'w')
        self.m_sCurPath = os.getcwd()

        # ------------------------------
        self.m_Parser = OptionParser()
      
        # number of files to be processed
        # self.m_Options.number
        self.m_Parser.add_option("-n", "--number", dest = 'number',
            help = "max count of files to process", default = "+999") # str(sys.maxint))

        # file sorting order: d – by project/distribution/date, n – by project/name
        #   e - by error coefficient
        # self.m_Options.order
        self.m_Parser.add_option("-o", "--order", dest = 'order',
            help = "file sort order n/d (by name/date)", default = "d")

        # doc. type
        # self.m_Options.type
        self.m_Parser.add_option("-t", "--type", dest = 'type',
            help = "file type suffix (C, C3, FM), * - all files; only ordinary articles will be processed if option -t is omitted", 
            default = "")

        # path to the folder of style/class files to select only files using them
        # self.m_Options.incl
        self.m_Parser.add_option("-i", "--includes", action = "store_true", dest = 'incl',
            help = "test only files using includes listed in file includes.mcl", default = False)

        # i�kelta į paveldėtą klasę  
        # self.ParseArgs()
        # self.Init()


# ----------------------------------------------
    def ParseArgs(self):
        """ argument parser """

        (self.m_Options, self.m_Args) = self.m_Parser.parse_args()

        # converting self.m_Options.number to int
        if (self.m_Options.number[0] == "-"): self.m_bLast = True
        if (self.m_Options.number[0] == "+"): self.m_bFirst = True
      
        # max_nums = sscanf(self.m_Options.number, "%d")
        # KpError.Assert(len(max_nums) >= 1, KpError.KP_E_INVALIDARG, "Non number given in place of max count of files to process (option -n)")
        # max_num_int = max_nums[0]
      
        max_num_int = int(self.m_Options.number)
      
        self.m_Options.number = max_num_int
        if (self.m_Options.number < 0): self.m_Options.number = -self.m_Options.number
      
        # convert self.m_Options.type to regexp of file names, corresponding to types of processed files
        if (self.m_Options.type == ""): # ordinary article without alphanumeric suffixes in the file name
            self.m_Options.type = "^[A-Za-z\\_\\-]*[0-9\\_\\-]*$"
        elif (self.m_Options.type == "*"): # all files
            self.m_Options.type = "^[A-Za-z\\_\\-0-9\\_\\-]*$"
        else: # files, corresponding to the suffix specified
            self.m_Options.type = "^[A-Za-z\\_\\-]*[0-9\\_\\-]*" + self.m_Options.type.lower() + "[0-9]*$"


# ----------------------------------------------
    def Init(self):
        """ 
        local constructor finalisator  
        trina logą, skaito .cfg
        parametrai jau turi būti suparsinti ir
        nustatytas m_sToolName 
        """

        # ----------------------------
        random.seed(datetime.now().microsecond)

        # ----------------------------
        self.ReadCfg(os.path.dirname(sys.argv[0]))
        self.ReadCfg(self.m_sCurPath)

        # ignoruojam .cfg parametrą Os (m_Cfg['Os']), nustatom pagal environment
        self.m_Cfg['Os'] = "ux" 
        try:
            if ((os.environ['windir'] != None) and (os.environ['windir'] != "")):
                self.m_Cfg['Os'] = "win" 
        except:
            pass

        # publisher/project
        KpError.Assert(len(self.m_Args) == 1, KpError.KP_E_INVALIDARG, "Wrong number of inputs specified")
        pub_proj = self.m_Args[0].split("/")
        KpError.Assert(len(pub_proj) <= 3, KpError.KP_E_INVALIDARG, "Invalid publisher/project syntax")
        self.m_sPublisherName = pub_proj[0]
        if (len(pub_proj) > 2):
            self.m_sMsName = pub_proj[2]
        if (len(pub_proj) > 1):
            self.m_asProjectNames.append(pub_proj[1])
        else:
            pub_dir = self.m_Cfg['OrigPath'] + "/" + self.m_sPublisherName
            proj_list = os.listdir(pub_dir)
            for proj in proj_list:
                if (os.path.isdir(pub_dir + "/" + proj)):
                    self.m_asProjectNames.append(proj)

        KpError.Assert(self.m_sPublisherName != None, KpError.KP_E_INVALIDARG, "Publisher name not specified")
        KpError.Assert(len(self.m_asProjectNames) >= 1, KpError.KP_E_NO_FILE, "No projects of specified publisher")

        # ----------------------------
        if (os.path.exists(self.m_sErrLogFileName)):
            os.system(self.m_OsPars[self.m_Cfg['Os']]['Del'] + " " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(self.m_sErrLogFileName.split("/")) + " > nul 2>&1")


# ----------------------------------------------
    def __del__(self):
        """ destructor """
        
#       self.m_LogFile.close()
        pass


# ----------------------------------------------
    def ReadCfg(self, sCfgPath):
        """ scans .cfg file """
        
        cfg_fname = sCfgPath + "/" + self.m_sToolName + ".cfg"

        if (os.path.exists(cfg_fname)):
            cfg_file = open(cfg_fname, 'r')
            cfg_lines = cfg_file.readlines()
            cfg_file.close()
      
            for cfg_line in cfg_lines:
                cfg_com_spl = cfg_line.split("#")
                cfg_par_line = cfg_com_spl[0].strip()
                if (cfg_par_line != ""): 
                    cfg_rec = cfg_par_line.split("=")
                    KpError.Assert(len(cfg_rec) > 1, KpError.KP_E_FILE_FORMAT, cfg_fname + ": " + cfg_line)
                    par_name = cfg_rec[0].strip()
                    del cfg_rec[0]
                    par_val = "=".join(cfg_rec)
                    self.m_Cfg[par_name] = par_val.strip() 


# ----------------------------------------------
    def GetTexProps(self):
        """ 
        scans original tex files for compiling properties, partially for included styles/classes; fills m_TexStats[]
        skanuojamas includintų failų sąrašas su TeXInfo.py
        """
        
        self.m_TexStats = []
        if (self.m_Options.incl):
            cmd_line = "python " + os.path.dirname(sys.argv[0]) + "/TeXInfo/TeXInfo.py " + self.m_sPublisherName + \
                (("/" + self.m_asProjectNames[0]) if (len(self.m_asProjectNames) == 1) else "")
            print "Started: " + cmd_line
            os.system(cmd_line)
            print "Ended: " + cmd_line
            
            info_fname = (self.m_asProjectNames[0] if (len(self.m_asProjectNames) == 1) else self.m_sPublisherName) + ".log"
            if (not os.path.exists(info_fname)):
                # raise KpException(KpError.KP_E_NO_FILE, "No TeXInfo output")
                KpError.Warning(KpError.KP_E_NO_FILE, "No TeXInfo output")
            else:
                info_file = open(info_fname, 'r')
                info_cont = info_file.readlines()
                info_file.close()
               
                for info_line in info_cont:
                    info_fields = info_line.split("|")
                    info_record = []
                    ix = 0
                    for info_field in info_fields:
                        if (ix == 7): # " webdoi,xchauthor,SciVerse,secthm,seceqn "
                            info_record.append(info_field.strip().split(","))
                        
                        elif (ix == 8): # "[('apnum2699.aux', '', 'apnum2699.aux', 'apnum2699', '.aux'), ('apnum2699.out', '', 'apnum2699.out', 'apnum2699', '.out')]"
                            records = info_field.strip().split("[(")
                            KpError.Assert(len(records) == 2, KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                            KpError.Assert(records[0] == "", KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                            
                            records = records[1].split(")]")
                            KpError.Assert(len(records) == 2, KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                            KpError.Assert(records[1] == "", KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                            
                            rec_tuple = ()
                            for rec_str_elems_str in records[0].split("), ("): # "'apnum2699.aux', '', 'apnum2699.aux', 'apnum2699', '.aux'"
                                rec_str_elems = rec_str_elems_str.split(", ") # ["'apnum2699.aux'", "''", "'apnum2699.aux'", "'apnum2699'", "'.aux'"]
                                rec_elem = []
                                for rec_str_elem in rec_str_elems: # "'apnum2699.aux'"
                                    rec_elems = rec_str_elem.split("'") # ["", "apnum2699.aux", ""]
                                    KpError.Assert(len(rec_elems) == 3, KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                                    KpError.Assert((rec_elems[0] == "") and (rec_elems[2] == ""), KpError.KP_E_FILE_FORMAT, "Invalid TeXInfo output file format")
                                    rec_elem.append(rec_elems[1])
                                
                                rec_tuple += (rec_elem,)
                            
                            info_record.append(rec_tuple)
                           
                        else: 
                            info_record.append(info_field.strip())
                        
                        ix = ix + 1 
                   
                    self.m_TexStats.append(info_record)            


# ----------------------------------------------
    def ReadIncludes(self, sPath):
        incl_fname = sPath + "/includes.mcl"
        if (os.path.exists(incl_fname)):
            incl_file = open(incl_fname, 'r')
            incl_lines = incl_file.readlines()
            incl_file.close()

            self.m_includes = {}

            for incl_line in incl_lines:
                incl_line_elems = incl_line.split("\n")
                incl_file_elems = incl_line_elems[0].split("/")
                incl_file_elems = incl_file_elems[-1].split("\\")
                self.m_Includes[incl_file_elems[-1].lower()] = True

    def GetIncludes(self):
        """ scans tested include files list to m_Includes[] """
        if (self.m_Options.incl):
            self.ReadIncludes(os.path.dirname(sys.argv[0]))
            self.ReadIncludes(".")

         
# ----------------------------------------------
    @staticmethod
    def GetDictElem(Dict, sKey):
        """ extracts dictionary element, returns None for nonexisting ones """
        
        ret_val = None
        if sKey in Dict.keys(): ret_val = Dict[sKey]
        return ret_val 


# ----------------------------------------------
    def GetInFileProp(self, iCurInFile, sKey):
        """ extracts property of m_InFiles[iCurInFile][sKey] """
        
        ret_val = None

        if ((sKey == 'proj_name') or (sKey == 'ms_name') or (sKey == 'comments')): 
                ret_val = ""
        if ((sKey == 'check_fl') or (sKey == 'ignore')): ret_val = False
        if (sKey == 'ratio'): ret_val = 0.0

        # distcmp properties
        if ((sKey == 'distr') or (sKey == 'format') or (sKey == 'maker') or \
            (sKey == 'cmd_line') or (sKey == 'new_cmd_line')):
                ret_val = ""
        if (sKey == 'comp_time'): ret_val = ""

        if sKey in self.m_InFiles[iCurInFile].keys():
            if (self.m_InFiles[iCurInFile][sKey] != None):
                ret_val = self.m_InFiles[iCurInFile][sKey]
        return ret_val 


# ----------------------------------------------
    def AddComment(self, iCurInFile, sErrMsg):
        """ extracts property of m_InFiles[iCurInFile][sKey] """
        
        old_msg = self.GetInFileProp(iCurInFile, 'comments')
        err_msg = old_msg
        if (err_msg != ""): err_msg += "; "
        self.m_InFiles[iCurInFile]['comments'] = err_msg + sErrMsg
        return old_msg


# ----------------------------------------------
    def MatchIncl(self, iCurInFile):
        """ 
        checks whether m_TexStats[m_InFiles[iCurInFile]['ms_name'] corresponds to include dictionary m_Includes[]
        returns True, if at least one of includes m_Includes[ii] is present in included file list m_TexStats[sMsName][8][jj][2]
        """
        
        ret_val = True
        if (self.m_Options.incl):
            ret_val = False
            stat_ixs = [ii for ii in range(len(self.m_TexStats)) if self.m_TexStats[ii][0].lower() == self.GetInFileProp(iCurInFile, 'ms_name').lower()]
            if (len(stat_ixs) == 0):
                self.AddComment(iCurInFile, "No TeXInfo record")
            else:            
                KpError.AssertW(len(stat_ixs) == 1, KpError.KP_E_FILE_FORMAT, "Multiple records of " + self.GetInFileProp(iCurInFile, 'ms_name') + " in TeXInfo output file")
                stat_ix = stat_ixs[0]
         
                for ii in range(len(self.m_TexStats[stat_ix][8])):
                    if (self.m_TexStats[stat_ix][8][ii][2].lower() in self.m_Includes):
                        ret_val = True
                        break 

        return ret_val      


# ----------------------------------------------
    def ScanDvi(self, iCurInFile):
        """ local scanning of original .dvi file, checking of correspondence with testing parameters """
        pass

    
    def ScanSrc(self, iCurInFile):
        """ local scanning of original .tex file, checking of correspondence with testing parameters """
        pass


# ----------------------------------------------
    def ScanOrigs(self):
        """ local scanning of original file, checking of correspondence with testing parameters """
        
        print 
        print "-----------------------------------"
        print "Scanning origs:"
        print 
        m_InFiles = []
        self.m_iNumOfInFiles = 0
        for proj in self.m_asProjectNames:
            proj_path = self.m_Cfg['OrigPath'] + "/" + self.m_sPublisherName + "/" + proj
            if (self.m_sMsName != ""):
                ms_list = [self.m_sMsName, ]
            else:
                ms_list = os.listdir(proj_path)
            for ii in range(len(ms_list)):
                if (os.path.isdir(proj_path + "/" + ms_list[ii])):
                    msl = ms_list[ii].lower()
                    projl = proj.lower()
                    self.m_InFiles.append({'proj_name': projl, 'ms_name': msl, 'check_fl': False, 'ignore': False, 'ratio': 0.0})
                    self.LogOrigs()
                    if (not re.match(self.m_Options.type, msl)):
                        self.AddComment(self.m_iNumOfInFiles, "Skipped: ne tas failo tipas")
                        self.m_InFiles[self.m_iNumOfInFiles]['ignore'] = True
                    else:
                        if (not self.MatchIncl(self.m_iNumOfInFiles)):
                            if (self.GetInFileProp(self.m_iNumOfInFiles, 'comments') == ""):
                                self.AddComment(self.m_iNumOfInFiles, "Skipped: nenaudoja tikrinamų stilių")
                            self.m_InFiles[self.m_iNumOfInFiles]['ignore'] = True
                        else:
                            self.ScanSrc(self.m_iNumOfInFiles) # skanuoja .tex failo turinį, tikrina atitikimą tikrinimo sąlygoms
                            self.ScanDvi(self.m_iNumOfInFiles) # skanuoja .dvi failo savybes, tikrina atitikimą nurodytoms sąlygoms
                          
                    err_msg = self.GetInFileProp(self.m_iNumOfInFiles, 'comments')
                    print self.m_sPublisherName + "/" + self.GetInFileProp(self.m_iNumOfInFiles, 'proj_name') + "/" + self.GetInFileProp(self.m_iNumOfInFiles, 'ms_name') + \
                        (": " + err_msg if (not (err_msg == "")) else "")
                    self.m_iNumOfInFiles = self.m_iNumOfInFiles + 1
                

# ----------------------------------------------
    def SortOrigsByTime(self):
        """ scans original dvi for compiling properties and fills corresponding record of m_InFiles[] """
      
        self.m_InFiles = sorted(self.m_InFiles, key = lambda file_rec: \
            str(False if GrpTool.GetDictElem(file_rec, 'ignore') else True) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'proj_name')) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'comp_time')))


    def SortOrigsByName(self):
        """ scans original dvi for compiling properties and fills corresponding record of m_InFiles[] """
      
        self.m_InFiles = sorted(self.m_InFiles, key = lambda file_rec: \
            str(False if GrpTool.GetDictElem(file_rec, 'ignore') else True) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'proj_name')) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'ms_name')))


    def SortOrigsByTimeRes(self):
        """ local scanning of original file, checking of correspondence with testing parameters """
        
        self.m_InFiles = sorted(self.m_InFiles, key = lambda file_rec: \
            str(GrpTool.GetDictElem(file_rec, 'proj_name')) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'comp_time')))


    def SortOrigsByNameRes(self):
        """ local scanning of original file, checking of correspondence with testing parameters """
        
        self.m_InFiles = sorted(self.m_InFiles, key = lambda file_rec: \
            str(GrpTool.GetDictElem(file_rec, 'proj_name')) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'ms_name')))


    def SortOrigsByRatioRes(self):
        """ local scanning of original file, checking of correspondence with testing parameters """
        
        self.m_InFiles = sorted(self.m_InFiles, key = lambda file_rec: \
            str(True if GrpTool.GetDictElem(file_rec, 'ignore') else False) + "." + \
            "%5.3f" % (GrpTool.GetDictElem(file_rec, 'ratio'),) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'proj_name')) + "." + \
            str(GrpTool.GetDictElem(file_rec, 'ms_name')))


# ----------------------------------------------
    def CountLiveFiles(self):
        """ calculates self.m_iNumOfLiveFiles – number of files suitable for testing """
        
        self.m_iNumOfLiveFiles = 0
        for ii in range(len(self.m_InFiles)):
            if (not self.GetInFileProp(ii, 'ignore')):
                self.m_iNumOfLiveFiles = self.m_iNumOfLiveFiles + 1


# ----------------------------------------------
    def ExtractGroups(self):
        """ extracts m_InFileGroups[] -- list of different projects of m_InFiles[] """
        
        self.m_InFileGroups = []
        self.m_iNumOfGroups = 0
        for ii in range(len(self.m_InFiles)):
            do_append = False
            
            if (self.m_iNumOfGroups < 1): do_append = True
            else:
                if (self.m_InFileGroups[self.m_iNumOfGroups - 1]['proj_name'] != self.GetInFileProp(ii, 'proj_name')):
                    do_append = True
                else:
                    self.m_InFileGroups[self.m_iNumOfGroups - 1]['file_count'] += 1
            
            if (do_append):
                self.m_InFileGroups.append({'first_file': ii, 'file_count': 1, \
                    'proj_name': self.GetInFileProp(ii, 'proj_name')})
                self.m_iNumOfGroups = self.m_iNumOfGroups + 1

# ----------------------------------------------
    def InitialMark(self):
        """ 
        local initial marking tool
        use property m_iMarked for marked files count 
        """
        pass


# ----------------------------------------------
    def MarkFiles(self):
        """ marks selective files for checking """
        
        self.m_iMarked = 0
        file_cnt = self.m_Options.number * len(self.m_asProjectNames)
        self.PutLogMsg("file_cnt: {0}  self.m_Options.number: {1}  len(self.m_asProjectNames): {2}".format(\
                          file_cnt, self.m_Options.number, len(self.m_asProjectNames)))  
        
        # local initial marking
        self.InitialMark()
        
        # mark rest
        while((self.m_iMarked < file_cnt) and (self.m_iMarked < self.m_iNumOfLiveFiles)):
            self.PutLogMsg("m_iMarked: {0} file_cnt: {1}".format(self.m_iMarked, file_cnt))  
            for ii in range(self.m_iNumOfGroups):
                for jj in range(self.m_InFileGroups[ii]['file_count']):
                    self.PutLogMsg("ii: {0} jj: {1}  m_iMarked: {2}  file_cnt: {3}".format(ii, jj, self.m_iMarked, file_cnt))  
                    if (self.m_iMarked >= file_cnt): break
                    ix = self.m_InFileGroups[ii]['first_file']
                    if (self.m_bLast): ix += self.m_InFileGroups[ii]['file_count'] - jj - 1
                    else: ix += jj
                    self.PutLogMsg("self.m_Options.number: {0}  ix {1}   self.m_InFiles[ix]['proj_name']: {2}  self.m_InFiles[ix]['ms_name']: {3}  self.GetInFileProp(ix, 'distr'): {4}  self.GetInFileProp(ix, 'format'): {5}  self.GetInFileProp(ix, 'ignore'): {6}  self.GetInFileProp(ix, 'check_fl'): {7}".format(\
                                     self.m_Options.number,      ix,     self.m_InFiles[ix]['proj_name'],        self.m_InFiles[ix]['ms_name'],      self.GetInFileProp(ix, 'distr'),    self.GetInFileProp(ix, 'format'),       self.GetInFileProp(ix, 'ignore'),       self.GetInFileProp(ix, 'check_fl')))  
                    if ((not self.GetInFileProp(ix, 'ignore')) and (not self.GetInFileProp(ix, 'check_fl'))):
                            if ((not self.m_bLast) and (not self.m_bFirst)): # random selection
                                prob_mul = random.randint(0, self.m_iNumOfLiveFiles) # probability * num. of files
                                weight = self.m_iNumOfLiveFiles + file_cnt / self.m_InFileGroups[ii]['file_count'] + 1
                                prob = prob_mul * weight / (self.m_iNumOfLiveFiles * self.m_iNumOfLiveFiles + 1)
                                if (prob):
                                    self.m_InFiles[ix]['check_fl'] = True
                                    self.m_iMarked = self.m_iMarked + 1
                            else: # if ((not self.m_bLast) and (not self.m_bFirst)):
                                self.PutLogMsg("ii: {0}  jj: {1}  self.m_Options.number: {2}  ix: {3}  self.m_InFiles[ix]['proj_name']: {4}  self.m_InFiles[ix]['ms_name']: {5}".format(\
                                                ii,     jj,         self.m_Options.number,  ix,         self.m_InFiles[ix]['proj_name'], self.m_InFiles[ix]['ms_name']))  
                                if (jj < self.m_Options.number):
                                    self.m_InFiles[ix]['check_fl'] = True
                                    self.PutLogMsg("pažymėtas")  
                                self.m_iMarked = self.m_iMarked + 1
                                break # skip to next group 


# ----------------------------------------------
    def LogOrigs(self):
        """ outputs m_InFiles[] to log """
        
        # skaičiuojam max. ms vardo ir cmd_line vardo ilgius
        max_ms_len = 10
        max_cmd_len = 10
        for ii in range(self.m_iNumOfInFiles):
            ms_len = len(self.m_sPublisherName + "/" + self.GetInFileProp(ii, 'proj_name') + "/" + self.GetInFileProp(ii, 'ms_name'))
            if (ms_len > max_ms_len): max_ms_len = ms_len 
            cmd_len = len(self.GetInFileProp(ii, 'new_cmd_line'))
            if (cmd_len > max_cmd_len): max_cmd_len = cmd_len 
        ms_fmt = "%-" + str(max_ms_len) + "s |" 
        cmd_fmt = "%-" + str(max_cmd_len) + "s |" 
       
        self.m_LogFile = open(self.m_sCurPath + "/" + self.m_sLogFileName, 'w')
        for ii in range(self.m_iNumOfInFiles):
            ratio = self.GetInFileProp(ii, 'ratio')
            if ((ratio > 0.999) and (ratio < 1.0)): ratio = 0.999
            print >> self.m_LogFile, \
                "*" if self.GetInFileProp(ii, 'check_fl') else " ", "|", \
                ms_fmt % (self.m_sPublisherName + "/" + self.GetInFileProp(ii, 'proj_name') + "/" + self.GetInFileProp(ii, 'ms_name'),), \
                "%5.3f" % (ratio,) if (self.GetInFileProp(ii, 'ratio') != None) else "     ", "|", \
                "%-35s |" % (self.GetInFileProp(ii, 'comments'),), \
                cmd_fmt % (self.GetInFileProp(ii, 'new_cmd_line'),), \
                "%-30s |" % (self.GetInFileProp(ii, 'cmd_line'),), \
                self.m_InFiles[ii]
        self.m_LogFile.close()
        self.m_LogFile = None


# ----------------------------------------------
    def PutLogMsg(self, msg):
        """ outputs m_InFiles[] to log """
        
        log_file = open(self.m_sErrLogFileName, 'a')
        print >> log_file, msg
        log_file.close()


# ----------------------------------------------
    def ScanTexLogSingle(self, iCurInFile, sLogFName):
        """ scans tex log file <ms>.log for errors """
        
        if (os.path.exists(sLogFName)):
            log_file = open(sLogFName, 'r')
            log_file_lines = log_file.readlines()
            log_file.close()
            
            err_pref = ""
            for in_file_line in log_file_lines:
                if (err_pref != ""):
                    err_msgs = in_file_line.strip().split(" ")
                    add_msg = err_msgs[-1].strip()
                    self.AddComment(iCurInFile, err_pref + ((": " + add_msg) if (add_msg != "") else ""))  
                    err_pref = ""
                else:
                    err_chk = in_file_line.split("!")
                    if ((len(err_chk) > 1) and (err_chk[0] == "")):
                        # numetam paskutinį tašką
                        err_chk = err_chk[1].split(".")
                        del err_chk[-1]
                        err_pref = ".".join(err_chk).strip()
                        
                        err_chk = err_pref.split("LaTeX Error:")
                        if (len(err_chk) > 1):
                            err_pref = err_chk[1].strip() 
                        
                        if (err_pref == "Emergency stop"): err_pref = ""


    def ScanTexLog(self, iCurInFile):
        """ scans tex log file <ms>.log for errors """
        
        log_fname = self.m_Cfg['DestPath'] + "/" + self.m_sPublisherName + "/" + \
            self.GetInFileProp(iCurInFile, 'proj_name') + "/" + self.GetInFileProp(iCurInFile, 'ms_name') + "/" + \
            self.GetInFileProp(iCurInFile, 'ms_name') + ".log"
        
        self.ScanTexLogSingle(iCurInFile, log_fname)

        # log_fname = self.m_Cfg['DestPath'] + "/" + self.m_sPublisherName + "/" + \
        #   self.GetInFileProp(iCurInFile, 'proj_name') + "/" + self.GetInFileProp(iCurInFile, 'ms_name') + "/" + \
        #   "tex.full.log"
        
        # self.ScanTexLogSingle(iCurInFile, log_fname)


# ----------------------------------------------
    def ScanEdDvipsLog(self, iCurInFile):
        """ scans ed_dvips log file ed_dvips.full.log for errors """
        
        log_fname = self.m_Cfg['DestPath'] + "/" + self.m_sPublisherName + "/" + \
            self.GetInFileProp(iCurInFile, 'proj_name') + "/" + self.GetInFileProp(iCurInFile, 'ms_name') + "/" + \
            "ed_dvips.full.log"
        
        if (os.path.exists(log_fname)):
            log_file = open(log_fname, 'r')
            log_file_lines = log_file.readlines()
            log_file.close()
            
            for in_file_line in log_file_lines:
                err_chk = in_file_line.split("!")
                if (len(err_chk) > 1):
                    if (err_chk[0] != "ed_dvips: "):
                        if (err_chk[1] != "ed_dvips: "): err_chk[0] = "ed_dvips: " 
                        else: del err_chk[0]
                    err_msg = "".join(err_chk)
                    # numetam paskutinį tašką
                    err_chk = err_msg.split(".")
                    del err_chk[-1]
                    err_msg = ".".join(err_chk).strip()
                    
                    self.AddComment(iCurInFile, err_msg)
                    break  


# ----------------------------------------------
# virtualūs callback-ai paveldėtai klasei, iškviečiami iškart prieš kompiliavimą ir iškart po kompiliavimo
    def PreCompileProc(self, iCurInFile, sFullMsName, sOrigPath):
        pass
    def PostCompileProc(self, iCurInFile, sFullMsName, sOrigPath):
        pass
        
# ----------------------------------------------
    def CompileSingle(self, iCurInFile, sFullMsName, sOrigPath):
        """ 
        execute single file compilation command, fill appropriate fields of m_InFiles[iCurInFile] 
        sFullMsName – "publisher/project/ms" 
        """
        
        print "Compilation started: " + sFullMsName + "\n"
        old_comment = self.AddComment(iCurInFile, "Compilation started...")
        self.LogOrigs()

        cmd_line = self.m_Cfg['CompCmd']
        cmd_line += " " + self.GetInFileProp(iCurInFile, 'ms_name')
        os.system(cmd_line)

        print "Compilation ended: " + sFullMsName + "\n"
        self.m_InFiles[iCurInFile]['comments'] = old_comment
        self.ScanTexLog(iCurInFile)
        if (self.GetInFileProp(iCurInFile, 'comments') == ""):      
            self.AddComment(iCurInFile, "Compiled")

        print "Compare tool started: " + sFullMsName + "\n"

        if (os.path.exists(self.m_sDiffLogFName)):
            os.system(self.m_OsPars[self.m_Cfg['Os']]['Del'] + " " + self.m_sDiffLogFName + " > nul 2>&1")

        cmd_line = self.m_Cfg['DiffCmd']
        cmd_line += " " + self.GetInFileProp(iCurInFile, 'ms_name')
        os.system(cmd_line)

        ratio = 0.0
        if (os.path.exists(self.m_sDiffLogFName)):
            if (os.path.getsize('diff.log') == 0): ratio = 1.0         
        self.m_InFiles[iCurInFile]['ratio'] = self.GetInFileProp(iCurInFile, 'ratio') + ratio

        print "Compare tool ended: " + sFullMsName + "\n"


# ----------------------------------------------
    def CompileOrigs(self):
        """ compiles all marked m_InFiles[]['check_fl'] """
        
        for ii in range(self.m_iNumOfInFiles):
            if (self.GetInFileProp(ii, 'check_fl')):
                os.chdir(self.m_Cfg['DestPath'])
                
                ms_path = self.m_sPublisherName
                os.system("mkdir " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + " > nul 2>&1")
                ms_path = ms_path + "/" + self.GetInFileProp(ii, 'proj_name')
                os.system("mkdir " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + " > nul 2>&1")
                ms_path = ms_path + "/" + self.GetInFileProp(ii, 'ms_name')
                os.system("mkdir " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + " > nul 2>&1")
                ms_path = self.m_Cfg['DestPath'] + "/" + ms_path
                full_ms_name = self.m_sPublisherName + "/" + self.GetInFileProp(ii, 'proj_name') + "/" + self.GetInFileProp(ii, 'ms_name')
                orig_path = self.m_Cfg['OrigPath'] + "/" + full_ms_name
                
                os.system(self.m_OsPars[self.m_Cfg['Os']]['Copy'] + " " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join((orig_path + "/* " + ms_path).split("/")))
                
                os.chdir(ms_path)
                
                self.PreCompileProc(ii, full_ms_name, orig_path)
                self.CompileSingle(ii, full_ms_name, orig_path)
                self.PostCompileProc(ii, full_ms_name, orig_path)

                os.chdir(self.m_sCurPath)
                
                # trinam darbinius failus
                if ((self.m_InFiles[ii]['comments'] == "Compiled") and (self.GetInFileProp(ii, 'ratio') == self.m_fRatioSuccess)):
                    os.system(self.m_OsPars[self.m_Cfg['Os']]['Del'] + " " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'] + "temp" + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'] + "*.* > nul 2>&1")
                    os.system("rmdir " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'] + "temp > nul 2>&1")
                    os.system(self.m_OsPars[self.m_Cfg['Os']]['Del'] + " " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'] + "*.* > nul 2>&1")
                    os.system("rmdir " + self.m_OsPars[self.m_Cfg['Os']]['OsPathDelim'].join(ms_path.split("/")) + " > nul 2>&1")
                

# ----------------------------------------------
    def DumpProperties(self):
        """ debugging tool """
        
        print
        print "-----------------------------------"
        print "publisher:       ", self.m_sPublisherName
        print "projects:        ", self.m_asProjectNames
        print "max. files:      ", self.m_Options.number
        print "f. name pattern: ", self.m_Options.type
        print
        print "-----------------------------------"
        for info_record in self.m_TexStats:
            for ii in range(len(info_record[8])): 
                # if (info_record[8][ii][4].lower() == ".cls"): 
                    print info_record[8][ii][2],
            print
        print "-------------------------------------"
        print self.m_Includes
        print "-------------------------------------"
        print self.m_Cfg
        print "-------------------------------------"
        pass


# ----------------------------------------------
    def Process(self):
        """ main entry of whole procedure """
        
        if (self.m_Options.incl):
            self.GetTexProps()  # skanuojamas includintų failų sąrašas su TeXInfo.py 
            self.GetIncludes()  # formuoja m_Includes[]
        
        self.ScanOrigs()
        
        if (self.m_Options.order == "d"): self.SortOrigsByTime()
        else: self.SortOrigsByName()

        self.CountLiveFiles()
        self.ExtractGroups()
        
        self.MarkFiles()
        self.LogOrigs()
        
        self.CompileOrigs()

        if (self.m_Options.order == "d"): self.SortOrigsByTimeRes()
        elif (self.m_Options.order == "n"): self.SortOrigsByNameRes()
        else: self.SortOrigsByRatioRes()
        
        self.LogOrigs()
        print "Verification completed, report written to the file " + self.m_sLogFileName
