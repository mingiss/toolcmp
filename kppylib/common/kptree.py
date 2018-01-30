#!D:\bin\python26\python.exe
# coding=UTF-8

"""
kptree.py
"""

# ----------------------------------
"""
med�io strukt�ra 
"""
class KpTreeElem:
   """
   m_value
   m_father 
   m_first_child
   m_prev_brother
   m_next_brother
   
   jei m_father ir m_prev_brother == None � strukt�ros �akninis elementas
   """

   # ---------------------------------------
   """
   konstruktorius
   value � lizdo reik�m�s objektas
   father, prev_brother � nuorodos � KpTreeElem objektus � med�io kaimynus, prie kuri� naujas elementas priri�amas
   """
   def __init__(self, value, father, prev_brother):
      self.m_value = value
      
      self.m_father = father
      if((father != None) and (prev_brother == None)): father.m_first_child = self
      
      self.m_first_child = None
      
      self.m_prev_brother = prev_brother
      if(prev_brother != None): prev_brother.m_next_brother = self
      
      self.m_next_brother = None


   # ---------------------------------------
   """ �terpia nauj� broli� �ak� po self """
   def insert_after(self, next_brother):
      next_next_brother = self.m_next_brother
      self.m_next_brother = next_brother
      
      next_brother.m_prev_brother = self     

      cur_brother = next_brother
      while(cur_brother != None): # b�gam per visus next_brother atsivestus brolius 
         cur_brother.m_father = self.m_father
      
         next_cur_brother = cur_brother.m_next_brother
      
         if(next_cur_brother == None): # paskutinis atsivestas 
            cur_brother.m_next_brother = next_next_brother
            if(next_next_brother != None): next_next_brother.m_prev_brother = cur_brother
         
         cur_brother = next_cur_brother     


   # ---------------------------------------
   """ prideda nauj� vaik� po paskutinio vaiko """
   def append_child(self, new_child):
      cur_child = self.m_first_child
      if(cur_child == None): # vaik� dar n�ra � sukuriam nauj�
         self.m_first_child = new_child
         new_child.m_prev_brother = None
         cur_child = new_child  
         while(cur_child != None): # perb�gam visus naujo vaiko atsivestus brolius
            cur_child.m_father = self
            cur_child = cur_child.m_next_brother
      else:
         while(cur_child.m_next_brother != None): cur_child = cur_child.m_next_brother
         cur_child.insert_after(new_child)

         
   # ---------------------------------------
   """ i�meta self i� kaimyn� s�ra�o � pakoreguoja nuorodas """
   def delete_entry(self):
      if(self.m_prev_brother != None):
         self.m_prev_brother.m_next_brother = self.m_next_brother
      else:
         if(self.m_father != None):
            self.m_father.m_first_child = self.m_next_brother
#        else: raise KpException(KpError.KP_E_ILLEGAL_CALL)  # �aknin� element� i�metin�ti negerai � nebent turim pasid�j� broli� nuorod� 
         
      if(self.m_next_brother != None):
         self.m_next_brother.m_prev_brother = self.m_prev_brother
                            
                            
   # ---------------------------------------
   """ 
   kopijuoja self su visais gimin�m � nauj� �ak� ir j� gr��ina 
   lizd� reik�mi� nekopijuoja, naudoja tas pa�ias nuorodas
   rei�kia, kopijos reik�mi� keisti negalima � pasikeis ir original� reik�m�s
   classtype � kopijos klas�s vardas, � kuri� reikia sukastinti naujai kuriamus med�io objektus
      classtype � paveld�ta i� KpTreeElem
   """
   def copy_branch(self, classtype):
      result = None
      
      cur_node = self
      cur_res_node = None
      
      while(cur_node != None):
      
         new_node = KpTreeElem(cur_node.m_value, None, None)
         new_node.__class__ = classtype 
         if(cur_res_node != None):
            cur_res_node.insert_after(new_node) 
            cur_res_node = cur_res_node.m_next_brother
         else: 
            cur_res_node = new_node
            result = cur_res_node 

         cur_child = cur_node.m_first_child
         if(cur_child != None):
            new_child = cur_child.copy_branch(classtype)
            cur_res_node.append_child(new_child)
            
         cur_node = cur_node.m_next_brother
      
      return(result)
                                 
