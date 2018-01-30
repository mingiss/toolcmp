#!D:\bin\python26\python.exe
# coding=UTF-8

"""
xmln.py
"""
from kppylib.common.kptree import KpTreeElem
from kppylib.common.scanf import sscanf

# ----------------------------------
"""
KpXmlNode elementas – tupletas ið 
   1) tago vardo ir
   2) 
      2.1) tekstinio turinio stringo arba
      2.2) parametrø þodyno 
Tekstinis turinys galimas tik tagui vardu "@" (tekstinis laukas), jam negalima turëti parametrø þodyno elemento.
Tagas vardu "$" – viso failo ðakninis mazgas, jame visi kiti tagai – kad þemiausio lygio tagai turëtø savo vienintelá bendrà tëvà. 
m_tag – pats tupletas, jame du elementai:
   m_tag[0] – tago vardo stringas, tekstiniams tagams – "@", failo tagams - "$"
   m_tag[1] – 
      2.1) tago turinio stringas, jei tagas "@" arba 
      2.2) parametrø þodynas (visiem skitiems tagams), 
      gali bûti None
TODO: paveldëti paèià klasæ ið tupleto 
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
XML turinio medis, elementai – KpXmlTag 
"""
class KpXmlNode(KpTreeElem):
   """
   tag – KpXmlTag struktûra – naujas XML medþio elementas
   father, prev_brother – medþio kaimynai, prie kuriø naujas elementas pririðamas
   """
   
   # ---------------------------------------
   m_indent = 0 # einamasis atitraukimas iðvedant (tagø steko gylis)
   
   # ---------------------------------------
   """
   konstruktorius
   tag – KpXmlTag objektas lizdo turiniui 
   father, prev_brother – nuorodos á KpXmlNode objektus – medþio kaimynus, prie kuriø naujas elementas pririðamas
   """
   def __init__(self, tag, father, prev_brother):
      KpTreeElem.__init__(self, tag, father, prev_brother)

   # ---------------------------------------
   """
   iðveda medá á failà, pradedant nuo self
   p_out_file – iðvedimo failas
   open_tag_fmt – atidaranèio tago iðvedimo formatas, jame du %s laukai: pirmas – tago vardui, 
      antras – parametrø þodynui, konvertuotam á stringà
   close_tag_fmt – uþdaranèio tago iðvedimo formatas, vienas laukas %s tago vardui arba tiesiog stringas be laukø  
   par_fmt – tago parametrø iðvedimo formatas, du %s laukai: pirmas – parametro vardas, antras – reikðmë,
      parametrai formatuojant skiriami tarpais
   """
   def write(self, p_out_file, open_tag_fmt = "<%s%s>", close_tag_fmt = "</%s>", par_fmt = "%s=\"%s\""):
      cur_node = self
      while(cur_node != None):
         if(cur_node.m_value.m_tag[0] == "@"): # tekstiniai tagai
            p_out_file.write(cur_node.m_value.m_tag[1])

         else: # normalûs tagai         
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
               p_out_file.write(close_tag_fmt % (cur_node.m_value.m_tag[0], )) # uþdarantis tagas
            else: p_out_file.write(close_tag_fmt)
         
         cur_node = cur_node.m_next_brother
          
          
   # ---------------------------------------
   """ 
   ieðko tagø pagal tago vardà ir vienà parametrà
   gràþina listà ið KpXmlNode elementø, kuriø tago vardas tag_name, turi parametrà parameter ir jo reikðmë sutampa
   tag_name – tago vardo stringas
   parameter – parametrø þodynas ið vienos parametro vardo/reikðmës poros
      jei parameter == None – parametro atitikimo netikrina 
   search_children – ar lásti gilyn á vaikus
      jei False – ieðko tik tarp self kartos jaunesniø broliø (áskaitant ir self)
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
   skanuoja tagus pagal tago vardà ir vienà parametrà
   tag_name – tago vardo stringas
   parameter – parametrø þodynas ið vienos parametro vardo/reikðmës poros
   format - parametrø reikðmiø parsinimo ir lyginimo formatas: "%s" – string, 
               kiti variantai ("%d", "%o" etc.) – int
   gràþina tupletà ið dviejø elementø:
      1) nuoroda á tagø medþio elementà, broliø grupëje einantá prieð tag_name/parameter atitinkantá elementà
            tikrina, ar sekanèio elemento tagas yra tag_name, ar turi parametrà parameter, o jo reikðmë
               ne maþesnë uþ nurodytà
            skanuoja pirma gilyn pagal vaikus, tada pagal brolius
            jei surastas sekantis elementas yra broliø grupës pradþioje – gràþina None – tokiam atvejui reikia 
               kaþkokios kitos paieðkos procedûros
      2) vëliavëlë, kad rastas sekantis elementas yra broliø grupës pradþioje
         nuoroda á medþio lizdà (pirmas rezultato tupleto elementas) tada gràþinama None 
   TODO: jei nurodyto tago nerado – gràþina paskutiná vyriausios kartos brolá 
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
                     result = (None, True) # einamasis (pirmas grupës) brolis jau tenkina sàlygà – blogai  

            if(not result[1]):
               if(next_brother != None): 
                  if(next_brother.m_value.m_tag[0] == tag_name): 
                     next_brother_pars = next_brother.m_value.m_tag[1]
                     if(key in next_brother_pars.keys()):
                        if(sscanf(next_brother_pars[key], format)[0] >= key_value): 
                           result = (cur_node, False) # radom lizdà, kurio tolesnis brolis tenkina sàlygà

         cur_node = next_brother
      
      return(result)


   # ---------------------------------------
   """ 
   iðtraukia tago tekstiná turiná (t.y., pirmo vaiko "@" turiná)
   jeigu turinio nëra, gràþina "" 
   """
   def GetValue(self):
      value = ""
      if(self.m_first_child != None):
         if(self.m_first_child.m_value != None):
            if(len(self.m_first_child.m_value.m_tag) > 1):
               if(self.m_first_child.m_value.m_tag[1] != None):
                  value = self.m_first_child.m_value.m_tag[1]
      return(value)
      
