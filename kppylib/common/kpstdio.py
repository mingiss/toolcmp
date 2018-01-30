#!D:\bin\python26\python.exe
# coding=UTF-8

# --------------------------------
"""
kp I/O klasės
"""

from kppylib.env.common.kperr import KpError

# ----------------------------------
class KpFile:
   """
   kp failas; memberiai:
      file m_file_obj – failo objektas
      int m_cur_lpos – einamoji išvedamos eilutės pozicija
   """
   def __init__(self):
      self.m_file_obj = None
      self.m_cur_lpos = 0

   def open(self, fname, fmode):
      if self.m_file_obj != None:
         raise KpException(KpError.KP_E_DOUBLE_CALL)
         self.close()

      self.m_file_obj = open(fname, fmode)
      self.m_cur_lpos = 0

   def close(self):
      if self.m_file_obj != None:
         self.m_file_obj.close()
         self.m_file_obj = None

   def write(self, out_str):
      if self.m_file_obj == None:
         raise KpException(KpError.KP_E_NO_FILE)
      else:
         self.m_file_obj.write(out_str)
      lines = out_str.split("\n")
      num_of_lines = len(lines)
      if(num_of_lines > 1): self.m_cur_lpos = 0
      self.m_cur_lpos += len(lines[num_of_lines - 1])
