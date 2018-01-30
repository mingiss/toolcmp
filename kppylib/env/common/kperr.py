#!D:\bin\python26\python.exe
# coding=UTF-8


# --------------------------------------
import sys, traceback


# --------------------------------------
class KpException(Exception):

    m_ErrCode = None # int: KpError.KP_E_...
    m_ErrMsg = None # string

    def __init__(self, err_code, err_msg):
        self.m_ErrCode = err_code
        self.m_ErrMsg = err_msg


# --------------------------------------
class KpError:

    KP_E_INVALIDARG     = 0
    KP_E_FILE_FORMAT    = 1
    KP_E_NO_FILE        = 2
    KP_E_SYSTEM_ERROR   = 3
    KP_E_FILE_NOT_FOUND = 4
    KP_E_CANCEL         = 5

    m_messages = [
        "Blogi argumentai",        # 0 KP_E_INVALIDARG
        "Blogas failo formatas",   # 1 KP_E_FILE_FORMAT
        "Failas neatvertas",       # 2 KP_E_NO_FILE
        "Sisteminë klaida",        # 3 KP_E_SYSTEM_ERROR
        "Failas nerastas",         # 4 KP_E_FILE_NOT_FOUND
        "Operacija nutraukta",     # 5 KP_E_CANCEL
    ]

    @staticmethod
    def Warning(err_code, msg = ""): # former warning()
        print >> sys.stderr, "Warning: " + KpError.m_messages[err_code] + ": " + msg

    @staticmethod
    def Error(err_code, err_msg = "", was_exception = False): # former error()
        print >> sys.stderr, "Error: " + KpError.m_messages[err_code] + ": " + err_msg
        if(was_exception): traceback.print_exc()
        else:
            # traceback.print_stack(myProgramFile)
            traceback.print_stack()
            # for line in traceback.format_stack():
                # print line.strip()

    @staticmethod
    def LogMsg(msg): # former log_msg()
        print msg

    @staticmethod
    def AppendMsg(msg_buf, msg):
        if ((msg_buf == None) or (msg_buf == "")): err_msg = msg
        else: err_msg += "; " + msg         

    @staticmethod
    def Catch(exc):
        err_code = KpError.KP_E_SYSTEM_ERROR
        err_msg = ""
        if (type(exc) is KpException):
            err_code = exc.m_ErrCode 
            err_msg = exc.m_ErrMsg
        elif (type(exc) is KeyError): 
            err_code = KpError.KP_E_INVALIDARG
            KpError.AppendMsg(err_msg, "Key is not in the dictionary")
        elif (type(exc) is WindowsError): 
            if(exc.args[0] == 2):
                err_code = KpError.KP_E_FILE_NOT_FOUND
            else:
                KpError.AppendMsg(err_msg, "WindowsError " + str(exc.args[0]))
            KpError.AppendMsg(err_msg, exc.args[1])
        elif (type(exc) is KeyboardInterrupt): 
            err_code = KpError.KP_E_CANCEL
        else:
            KpError.AppendMsg(err_msg, str(type(exc)))
             
        if (hasattr(exc, 'child_traceback')): print exc.child_traceback # subprocess.Popen child process stack # OSError?
        
        KpError.Error(err_code, err_msg, True)

    @staticmethod
    def Assert(cond, err_code, err_msg): 
        if(not cond): raise KpException(err_code, err_msg)
      
    @staticmethod
    def AssertW(cond, err_code, err_msg): 
        if(not cond): KpError.Warning(err_code, err_msg)
