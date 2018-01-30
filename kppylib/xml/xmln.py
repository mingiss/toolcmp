#!D:\bin\python26\python.exe
# coding=UTF-8

"""
xmln.py
"""
from kppylib.common.kptree import KpTreeElem
from kppylib.common.scanf import sscanf

# ----------------------------------
"""
KpXmlNode elementas � tupletas i� 
   1) tago vardo ir
   2) 
      2.1) tekstinio turinio stringo arba
      2.2) parametr� �odyno 
Tekstinis turinys galimas tik tagui vardu "@" (tekstinis laukas), jam negalima tur�ti parametr� �odyno elemento.
Tagas vardu "$" � viso failo �akninis mazgas, jame visi kiti tagai � kad �emiausio lygio tagai tur�t� savo vienintel� bendr� t�v�. 
m_tag � pats tupletas, jame du elementai:
   m_tag[0] � tago vardo stringas, tekstiniams tagams � "@", failo tagams - "$"
   m_tag[1] � 
      2.1) tago turinio stringas, jei tagas "@" arba 
      2.2) parametr� �odynas (visiem skitiems tagams), 
      gali b�ti None
TODO: paveld�ti pa�i� klas� i� tupleto 
"""
class KpXmlTag:
   def __init__(self, tag, pars, value):
      if(tag == "$"):
         if((pars != None) or (value != None)): raise KpException(KpError.KP_E_INVALIDARG)
         else: self.m_tag = (tag, )
      elif(tag == "@"):
         if(pars != None): raise KpException(KpError.KP_E_INVALIDARG)
         else:
            if(value == None): raise KpException(KpError.KP_E_INVALIDARG) 
            else: self.m_tag = (tag, value)
      else:
         if(value != None): raise KpException(KpError.KP_E_INVALIDARG)
         else:
            if(pars != None): self.m_tag = (tag, pars)
            else: self.m_tag = (tag, )

# ----------------------------------
"""
XML turinio medis, elementai � KpXmlTag 
"""
class KpXmlNode(KpTreeElem):
   """
   tag � KpXmlTag strukt�ra � naujas XML med�io elementas
   father, prev_brother � med�io kaimynai, prie kuri� naujas elementas priri�amas
   """
   
   # ---------------------------------------
   m_indent = 0 # einamasis atitraukimas i�vedant (tag� steko gylis)
   
   # ---------------------------------------
   """
   konstruktorius
   tag � KpXmlTag objektas lizdo turiniui 
   father, prev_brother � nuorodos � KpXmlNode objektus � med�io kaimynus, prie kuri� naujas elementas priri�amas
   """
   def __init__(self, tag, father, prev_brother):
      KpTreeElem.__init__(self, tag, father, prev_brother)

   # ---------------------------------------
   """
   i�veda med� � fail�, pradedant nuo self
   p_out_file � i�vedimo failas
   open_tag_fmt � atidaran�io tago i�vedimo formatas, jame du %s laukai: pirmas � tago vardui, 
      antras � parametr� �odynui, konvertuotam � string�
   close_tag_fmt � u�daran�io tago i�vedimo formatas, vienas laukas %s tago vardui arba tiesiog stringas be lauk�  
   par_fmt � tago parametr� i�vedimo formatas, du %s laukai: pirmas � parametro vardas, antras � reik�m�,
      parametrai formatuojant skiriami tarpais
   """
   def write(self, p_out_file, open_tag_fmt = "<%s%s>", close_tag_fmt = "</%s>", par_fmt = "%s=\"%s\""):
      cur_node = self
      while(cur_node != None):
         if(cur_node.m_value.m_tag[0] == "@"): # tekstiniai tagai
            p_out_file.write(cur_node.m_value.m_tag[1])

         else: # normal�s tagai         
            # TODO: tik grupiniams tagams
            for ii in range(0, self.m_indent): p_out_file.write("   ")

            pars = ""
            if(len(cur_node.m_value.m_tag) > 1): # yra parametrai
               pars = " " + " ".join([
                  (
                     (
                        (par_fmt % (key, value)) 
                        if(value != None) 
                        else key
                     )
                     if(key != "@")
                     else value
                  ) 
                  for (key, value) in cur_node.m_value.m_tag[1].items()]) 

            p_out_file.write(open_tag_fmt % (cur_node.m_value.m_tag[0], pars)) # atidarantis tagas su parametrais

            cur_child = cur_node.m_first_child
            if(cur_child != None):
               # TODO: tik grupiniams tagams
               p_out_file.write("\n")
              
               cur_child.m_indent = self.m_indent + 1
               cur_child.write(p_out_file, open_tag_fmt, close_tag_fmt, par_fmt)

               # TODO: tik grupiniams tagams
               for ii in range(0, self.m_indent + 1): p_out_file.write("   ")
               if(len(close_tag_fmt.split("\n")) < 2): p_out_file.write("\n")  

            if(len(close_tag_fmt.split("%s")) == 2): 
               p_out_file.write(close_tag_fmt % (cur_node.m_value.m_tag[0], )) # u�darantis tagas
            else: p_out_file.write(close_tag_fmt)
         
         cur_node = cur_node.m_next_brother
          
          
   # ---------------------------------------
   """ 
   ie�ko tag� pagal tago vard� ir vien� parametr�
   gr��ina list� i� KpXmlNode element�, kuri� tago vardas tag_name, turi parametr� parameter ir jo reik�m� sutampa
   tag_name � tago vardo stringas
   parameter � parametr� �odynas i� vienos parametro vardo/reik�m�s poros
      jei parameter == None � parametro atitikimo netikrina 
   search_children � ar l�sti gilyn � vaikus
      jei False � ie�ko tik tarp self kartos jaunesni� broli� (�skaitant ir self)
   """
   def search_tag_by_name_pars(self, tag_name, parameter = None, search_children = True):
      result = []
       
      cur_node = self
      while(cur_node != None):
      
         if(cur_node.m_value.m_tag[0] == tag_name):
            if(parameter != None): 
               key = parameter.keys()[0]
               cur_node_pars = cur_node.m_value.m_tag[1]
               if(key in cur_node_pars.keys()):
                  if(cur_node_pars[key] == parameter[key]): 
                     result.append(cur_node)
            else: 
               result.append(cur_node)

         if(search_children):
            cur_child = cur_node.m_first_child
            if(cur_child != None):
               result.extend(cur_child.search_tag_by_name_pars(tag_name, parameter))

         cur_node = cur_node.m_next_brother
      
      return(result)


   # ---------------------------------------
   """ 
   skanuoja tagus pagal tago vard� ir vien� parametr�
   tag_name � tago vardo stringas
   parameter � parametr� �odynas i� vienos parametro vardo/reik�m�s poros
   format - parametr� reik�mi� parsinimo ir lyginimo formatas: "%s" � string, 
               kiti variantai ("%d", "%o" etc.) � int
   gr��ina tuplet� i� dviej� element�:
      1) nuoroda � tag� med�io element�, broli� grup�je einant� prie� tag_name/parameter atitinkant� element�
            tikrina, ar sekan�io elemento tagas yra tag_name, ar turi parametr� parameter, o jo reik�m�
               ne ma�esn� u� nurodyt�
            skanuoja pirma gilyn pagal vaikus, tada pagal brolius
            jei surastas sekantis elementas yra broli� grup�s prad�ioje � gr��ina None � tokiam atvejui reikia 
               ka�kokios kitos paie�kos proced�ros
      2) v�liav�l�, kad rastas sekantis elementas yra broli� grup�s prad�ioje
         nuoroda � med�io lizd� (pirmas rezultato tupleto elementas) tada gr��inama None 
   TODO: jei nurodyto tago nerado � gr��ina paskutin� vyriausios kartos brol� 
   """
   def search_last_tag_before_name_pars(self, tag_name, parameter, format):
      result = (None, False)
       
      cur_node = self
      while((cur_node != None) and (result[0] == None) and (not result[1])):

         cur_child = cur_node.m_first_child
         if(cur_child != None):
            result = cur_child.search_last_tag_before_name_pars(tag_name, parameter, format)

         key = parameter.keys()[0]
         key_value = sscanf(parameter[key], format)[0]
         next_brother = cur_node.m_next_brother

         if((result[0] == None) and (not result[1])):
            if(cur_node.m_value.m_tag[0] == tag_name): 
               cur_node_pars = cur_node.m_value.m_tag[1]
               if(key in cur_node_pars.keys()):
                  if(sscanf(cur_node_pars[key], format)[0] >= key_value): 
                     result = (None, True) # einamasis (pirmas grup�s) brolis jau tenkina s�lyg� � blogai  

            if(not result[1]):
               if(next_brother != None): 
                  if(next_brother.m_value.m_tag[0] == tag_name): 
                     next_brother_pars = next_brother.m_value.m_tag[1]
                     if(key in next_brother_pars.keys()):
                        if(sscanf(next_brother_pars[key], format)[0] >= key_value): 
                           result = (cur_node, False) # radom lizd�, kurio tolesnis brolis tenkina s�lyg�

         cur_node = next_brother
      
      return(result)


   # ---------------------------------------
   """ 
   i�traukia tago tekstin� turin� (t.y., pirmo vaiko "@" turin�)
   jeigu turinio n�ra, gr��ina "" 
   """
   def GetValue(self):
      value = ""
      if(self.m_first_child != None):
         if(self.m_first_child.m_value != None):
            if(len(self.m_first_child.m_value.m_tag) > 1):
               if(self.m_first_child.m_value.m_tag[1] != None):
                  value = self.m_first_child.m_value.m_tag[1]
      return(value)
      
