from itertools import combinations



file= open("Projects/Project3/Groceries_dataset.csv","r") 

file1=file.readline()
list_pur=[]

file2=file.read()
file2=file2.split('\n')[:-1]
lst=[]
for i in file2:
  i=i.split(',')
  lst.append(i)
#print(lst)

def creating_dict_for_customers(l):
  dct=dict()
  for q in l:
    im=q[0]
    date=q[1]
    prod=q[2]
    if (im,date) in dct:
      dct[(im,date)]=dct[(im,date)]+[prod]
    else:
      dct[(im,date)]=[prod]
  return dct

basket_dict=(creating_dict_for_customers(lst))

final_lst=list(basket_dict.values())


#print(final_lst)

item_dict=dict()
for i1 in final_lst:
  for j1 in i1:
    if j1 in item_dict:
      item_dict[j1]+=1
    else:
      item_dict[j1]=1

#print(item_dict)
freq_dict=dict()
freq1_lst=[]
for element in item_dict:
   if item_dict[element]>=18:
     freq_dict[element]=item_dict[element]
     freq1_lst.append(element)
#print(freq_dict)

def frequent2(basketlst,freqitemset,k):
  itsets=list(combinations(freqitemset, k))
  #print(itsets)
  
  
  
  b=dict()
  for is1 in itsets:#(Milk,eggs) 
     
     count=0
     for z in basketlst: #z=[milk,eggs,chicken]
      
      if all(elem in z for elem in is1):
          count+=1
      
     #print(is1,count)
     if count>=18:
       b[is1]=count
  if len(b)==0:
     return []
  else:
    return b




freq2=[]
di=frequent2(final_lst,freq1_lst,2)

if len(di)!=0:
   for ix in di : 
     freq2.append((list(ix)))


final_item_set_list=[]
for jq in freq1_lst:
   jq=[jq]
   final_item_set_list.append(jq)


def thres_check(basketlst,lst):
    ret_list=[]
    for is1 in lst: 
     
     
     count=0
     for z in basketlst:
       
       if all(elem in z for elem in is1):
         count+=1
     
     if count>=18:
       ret_list.append(sorted(is1))
    
    if len(ret_list)==0:
      return 0
    else:
     return ret_list



def apriori(basketlst,lst,k):
 a=[]
 for x in lst:
      for y in lst:
          if x!=y:
              new=set(x).union(y)
              if len(new) == k:
                if sorted(list(new)) not in a:
                  a.append(sorted(list(new)))
 return thres_check(basketlst,a)


final_item_set_list+=freq2
#print(len(final_item_set_list))
k=3
while True:
  w = apriori(final_lst,freq2,k)
  
  if w==0:
     break
  else:
     l=apriori(final_lst,freq2,k)
     final_item_set_list+=l
      
  k+=1
  freq2=l
  

# print(dq)
#print("xxxxxxxxx")
#dqq=[['tropical fruit', 'other vegetables', 'whole milk'], ['rolls/buns', 'other vegetables', 'whole milk'], ['soda', 'rolls/buns', 'whole milk'], ['yogurt', 'rolls/buns', 'whole milk'], ['soda', 'rolls/buns', 'other vegetables'], ['yogurt', 'rolls/buns', 'other vegetables'], ['sausage', 'other vegetables', 'whole milk'], ['soda', 'other vegetables', 'whole milk'], ['yogurt', 'other vegetables', 'whole milk'], ['bottled water', 'other vegetables', 'whole milk'], ['yogurt', 'soda', 'whole milk']]
#l=apriori(final_lst,dqq,4)
#print(l)

print(len(final_item_set_list)) #Frequent itemsets : 165
association_rules=[]

for ia in final_item_set_list:
  for ja in final_item_set_list:
    c1=0
    c2=0
    if sorted(ia)!=sorted(ja):
      ia=set(ia)
      ja=set(ja)
      a=ia.union(ja)
      
      for xa in final_lst:
        if all(elem in xa for elem in a):
          
          c1+=1
        if all(elem in xa for elem in ia):
          c2+=1

      conf=c1/c2
      #print(c1,c2)
      #print(conf)
      if conf>=0.06:
       ia=list(ia)
       ja=list(ja)
       for i in ia:
         tally=1
         if i in ja:
           tally*=0
           break
       if (tally==0):
           print("Conf(",ia,"------>",ja,") =",conf) #Looks like no association rules are present with confidence more than 0.3


