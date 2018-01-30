#!/usr/bin/env python
# coding=UTF-8

__author__ = "Mindaugas Piešina <mindaugas.piesina@vtex.lt>"
__version__ = "0.1"

# --------------------------------
"""
toolcmp.py
    Grupiškai vykdo nurodytą komandą, lygina rezultatus

Syntax:
    python toolcmp.py <publisher>/<project> [GrpTool options]
      
        Gali būti naudojami motininės klasės GrpTool parametrai (žr. grptool.py)

        Atrinkti originalūs failai X:/files_db/<publisher>/<project>/*/* kompiliuojami konfigūracijos faile 
            nurodyta kompiliavimo komanda, rezultatai lyginami nurodyta lyginimo komanda. Pastaroji 
            lokaliame darbiniame manuskripto kompiliavimo aplanke turi suformuoti lyginimo rezultatų failą diff.log,
            kuris sėkmės atveju turi būti tuščias (komandos diff rezultatas).  

Examples:
    python toolcmp.py esch/apnum
    python toolcmp.py esch -n 10
    python toolcmp.py esme/aescte -t FM
    python toolcmp.py esme/apnum -t * -i test
    python toolcmp.py esch -t CFM -i test
    python toolcmp.py esch/comgeo -n -10 -o n

Changelog:
    2013-05-10  mp  initial creation
"""

# --------------------------------
import sys
import os

# sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/..")
# print sys.path

from kppylib.env.common.kperr import KpError, KpException

from kppylib.grptool.grptool import GrpTool


# --------------------------------
class ToolCmp(GrpTool):

# ----------------------------------------------
    def __init__(self):
        """ constructor; analyzes command line parameters and sets object properties """
        
        # self.m_sToolName = "toolcmp"
        
        super(ToolCmp, self).__init__()

        self.ParseArgs()
        self.Init()

# --------------------------------
try:
    chk_obj = ToolCmp()
   
    chk_obj.Process()

    # chk_obj.DumpProperties()

except Exception, exc:
    KpError.Catch(exc)
except SystemExit, exc:
    if (str(exc) != "0"):
        KpError.Error(KpError.KP_E_SYSTEM_ERROR, "Exit code: " + str(exc), True)
except:
    KpError.Error(KpError.KP_E_SYSTEM_ERROR, "Unhandled exception", True)
