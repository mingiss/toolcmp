#!/usr/bin/env python
# coding=UTF-8

# --------------------------------
"""
XML failo parseris
sukelia xml failą į KpXmlNode struktūrą
"""


from HTMLParser import HTMLParser
from kppylib.env.common.kperr import KpError
from kppylib.xml.xmln import KpXmlTag, KpXmlNode


# ----------------------------------
class KpXmlParser(HTMLParser):

   def __init__(self):
      HTMLParser.__init__(self)
      self.InitProperties()

   def __init__(self, sFileName):
      HTMLParser.__init__(self)
      self.InitProperties()
      self.ReadFile(sFileName) 

   def InitProperties(self):
      self.m_KpXmlDoc = KpXmlNode(KpXmlTag("$", None, None), None, None) # KpXmlNode objektas - suparsintas xml failas
      self.m_CurNode = self.m_KpXmlDoc # pointeris į KpXmlNode objektą - šiuo metu skaitiomą tagą
   
   def handle_starttag(self, tag, attrs):
      # attrs yra listas iš tupletų – (vardo, reikšmės) porų:
      # [("vardas", "reikšmė"), ("vardas", "reikšmė"), ("vardas", "reikšmė")]
      # verčiam į žodyną
      pars = {}
      for ii in range(0, len(attrs)):
         pars[attrs[ii][0]] = attrs[ii][1]
      if(self.m_CurNode.m_value.m_tag[0] == "@"):
         self.m_CurNode = self.m_CurNode.m_father      
      new_node = KpXmlNode(KpXmlTag(tag, pars, None), None, None)
      self.m_CurNode.append_child(new_node)
      self.m_CurNode = new_node
      
   def handle_endtag(self, tag):
      if(self.m_CurNode.m_value.m_tag[0] == "@"):
         self.m_CurNode = self.m_CurNode.m_father      
      KpError.Assert(self.m_CurNode.m_value.m_tag[0] == tag, KpError.KP_E_FILE_FORMAT, 
         "<" + self.m_CurNode.m_value.m_tag[0] + ">...</" + tag + ">")
      self.m_CurNode = self.m_CurNode.m_father      

   def handle_startendtag(self, tag, attrs):
      if(self.m_CurNode.m_value.m_tag[0] == "@"):
         self.m_CurNode = self.m_CurNode.m_father      
      new_node = KpXmlNode(KpXmlTag(tag, attrs, None), None, None)
      self.m_CurNode.append_child(new_node)

   def handle_data(self, data):
      if(self.m_CurNode.m_value.m_tag[0] == "@"):
         self.m_CurNode.m_value.m_tag[1] = self.m_CurNode.m_value.m_tag[1] + data
      else:  
         new_node = KpXmlNode(KpXmlTag("@", None, data), None, None)
         self.m_CurNode.append_child(new_node)
         self.m_CurNode = new_node

   def handle_entityref(self, name):
      pass

   def handle_charref(self, name):
      pass

   def handle_comment(self, data):
      pass

   def handle_decl(self, decl):
      # DOCTYPE's praleidžiam
      # print decl
      pass

   def handle_pi(self, data):
      pass

   def unknown_decl(self, data):
      pass

   """ xml failo skaitymas į m_KpXmlDoc """
   def ReadFile(self, sFileName): 
      in_file = open(sFileName, 'rb')
      in_file_cont = in_file.read()
      in_file.close()

      self.feed(in_file_cont)
