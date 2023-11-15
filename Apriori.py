from itertools import combinations
import time
start = time.time()

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



item_dict=dict()
for i1 in final_lst:
  for j1 in i1:
    if j1 in item_dict:
      item_dict[j1]+=1
    else:
      item_dict[j1]=1


freq_dict=dict()
freq1_lst=[]
for element in item_dict:
   if item_dict[element]>=18:
     freq_dict[(element,)]=item_dict[element]
     freq1_lst.append(element)


def frequent2(basketlst,freqitemset,k):
  itsets=list(combinations(freqitemset, k))
  b=dict()
  for is1 in itsets:#(Milk,eggs) 
    
     count=0
     for z in basketlst: 
      
      if all(elem in z for elem in is1):
          count+=1
      
     
     if count>=18:
       b[tuple(sorted(is1))]=count
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

di.update(freq_dict)
def thres_check(basketlst,lst):
    ret_list=[]
    for is1 in lst: 
     
     
     count=0
     for z in basketlst:
       
       if all(elem in z for elem in is1):
         count+=1
     
     if count>=18:
       ret_list.append(sorted(is1))
       di[tuple(sorted(is1))]=count
    
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


print(final_item_set_list) #Frequent Itemsets




pair_p=[]
for l in final_item_set_list:
  if len(l)>=2:
    pair_p.append(l)

from itertools import chain, combinations



def generate_subsets(itemset):
    return chain.from_iterable(combinations(itemset, r) for r in range(1, len(itemset)))


def generate_association_rules(frequent_itemsets):
    rules = []
    
    for itemset in frequent_itemsets:
       
        subsets = generate_subsets(itemset)
        
        for subset in subsets:
            a= set(subset)
            b = set(itemset) - a
            x=a.union(b)
            x1=tuple(sorted(tuple(x)))
            a1=tuple(sorted(tuple(a)))
            c1=di[x1]
            c2=di[a1]
            conf=c1/c2
            if conf>=0.06:
             rules.append((a,b,conf))
    
    return rules



association_rules=generate_association_rules(pair_p)

for rule in association_rules:
     antecedent_str = ', '.join(rule[0])
     consequent_str = ', '.join(rule[1])
     conf=rule[2]
     print(f"Conf({antecedent_str} -> {consequent_str}) : {conf} ")

'''Code below can be uncommented and can be printed to look at confidence between frequent
itemsets. I have printed above the confidence within every frequent itemset as I asked the Professor '''


'''
The only reason I have commented is because it takes a lot of time to run, almost 20-25 mins as it goes through atleast 20000 
possible combinations'''

# for ia in final_item_set_list:
#   for ja in final_item_set_list:
#     c1=0
#     c2=0
#     if sorted(ia)!=sorted(ja):
#       ia=set(ia)
#       ja=set(ja)
#       a=ia.union(ja)
      
#       for xa in final_lst:
#         if all(elem in xa for elem in a):
          
#           c1+=1
#         if all(elem in xa for elem in ia):
#           c2+=1

#       conf=c1/c2
#       #print(c1,c2)
#       #print(conf)
#       if conf>=0.06:
#        ia=list(ia)
#        ja=list(ja)
#        for i in ia:
#          tally=1
#          if i in ja:
#            tally*=0
#            break
#        if (tally==0):
#            print("Conf(",ia,"------>",ja,") =",conf)      


#Reasoning       

#1.

# Support quantifies the frequency of itemset occurrences, indicating how commonly items appear together. 
# Higher support values reveal more prevalent itemsets, guiding analysts to identify common patterns.
# 
# Support is calculated by (Number of baskets with item being occured)/(Total Baskets)

# Confidence measures the strength of associations between items, 
# reflecting the likelihood that one item is purchased when another is. 
# Elevated confidence values signify relationships, aiding in the discovery of reliable associations 
# for decision-making .

#Confidence of (I --> J) is calculated by Support(I U J)/Support(I)


#Lift, on the other hand, gauges the significance of an association by comparing the likelihood of items being purchased together against random chance. 
# Lift values greater than 1 indicate a positive association, suggesting that items are more likely to be bought together, while values less than 1 signify a less interesting or negative association. 
# Together, these metrics help analysts filter and prioritize association rules, ensuring that the identified patterns are not only statistically significant but also practically meaningful in 
# various domains such as market basket analysis. (Support of (A U B)/Support(A)*Support(B))

#2.
#In association rule mining, support, confidence, and lift are key metrics that provide insights 
# into the patterns and relationships within a dataset. 
# Support measures the frequency of occurrence of an itemset in the dataset, indicating how common or popular it is. 
# A high support value suggests that the itemset 
# is frequently found in transactions. 
# 
# Confidence, on the other hand, calculates the strength of associations between 
# items in an itemset. It represents the likelihood that the presence of one item implies the presence of another. 
# High confidence signifies strong relationships between items within an association rule.


# The Apriori algorithm employs these metrics to mine frequent itemsets. 
# It begins by identifying frequent singletons and iteratively generates candidate itemsets. 
# Apriori uses support to prune infrequent candidates. 
# Confidence is then applied to filter association rules, ensuring reliability. 
# So like associative rules are measured with the help of confidence here and only the ones above the confidence threshold, are displayed

# In market basket analysis, high-support itemsets reveal popular product combinations, guiding inventory decisions. This way, we could
# know the most bought items and indeed get popular produces
# High-confidence rules aid in targeted marketing and cross-selling as buying one product might increase 
# the purchasing probability of other products

#Lift assesses the significance of associations, 
# influencing strategic decisions on product bundling and placement.  
# These metrics collectively optimize product assortments and enhance overall sales strategies.
# Lift is particularly helpful in market-based analysis as it provides a measure of how much more likely a set of items are to be 
# purchased together compared to what would be expected by chance. In the context of association rule mining, lift helps 
# identify significant relationships between items and assesses the impact of these relationships on purchasing behavior.
