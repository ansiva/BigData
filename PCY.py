from itertools import combinations
from collections import defaultdict
import time
start=time.time()

conf_dict=dict()




def support(baskets,item):
    c=0
    if type(item)!=tuple:
        item=(item,)
        
        
        
    for q1 in baskets:   
           if all(elem in q1 for elem in item ):
                c+=1
    
   
    
                
   
    
    return c


def generate_pairs(basket):
    pairs = []
    for pair in combinations(basket, 2):
        pairs.append(tuple(sorted(pair)))
    return pairs

def generate_triplets(basket):
    triplets = []
    for triplet in combinations(basket, 3):
        triplets.append(tuple(sorted(triplet)))
    return triplets

def combine_hashes(hash1, hash2, max_value):
    # Combine two hash values to generate a new hash value
    combined_hash = (hash1 + hash2) % max_value
    return combined_hash

def pcy_algorithm(baskets, support_threshold):
   
    item_counts = defaultdict(int)
    pair_counts = defaultdict(int)
    triplet_counts = defaultdict(int)

    for basket in baskets:
        for item in basket:
            item_counts[item] += 1
      
        pairs = generate_pairs(basket)
        for pair in pairs:
            pair_counts[pair] += 1

        triplets = generate_triplets(basket)
        for triplet in triplets:
            triplet_counts[triplet] += 1
    
    # Create bitmap for frequent items
    frequent_items = list(item for item, count in item_counts.items() if count >= support_threshold)
    bitmap = {item: 1 for item in frequent_items}

    # Second pass to count candidate pairs and triplets using the bitmap
    candidate_pairs = defaultdict(int)
    candidate_triplets = defaultdict(int)

    for basket in baskets:
        pairs = generate_pairs(basket)
        triplets = generate_triplets(basket)

        for pair in pairs:
            if pair[0] in frequent_items and pair[1] in frequent_items:
                # Use two hash functions to create a combined hash value
                hashed_value = combine_hashes(hash(pair[0]), hash(pair[1]), len(bitmap))
                if bitmap[pair[0]] == 1 and bitmap[pair[1]] == 1:
                    if pair[0] != pair[1]:
                            
                        
                            candidate_pairs[pair] += 1

        
        for triplet in triplets:
            if all(item in frequent_items for item in triplet):
                # Use two hash functions to create a combined hash value
                hashed_value = combine_hashes(combine_hashes(hash(triplet[0]), hash(triplet[1]), len(bitmap)),
                                              hash(triplet[2]), len(bitmap))
                if bitmap[triplet[0]] == 1 and bitmap[triplet[1]] == 1 and bitmap[triplet[2]] == 1:
                    #if support(baskets,triplet)==18:
                      
                      candidate_triplets[triplet] += 1
        
    # Filter out pairs and triplets below the support threshold
    x1pairs=[]
    x2triplets=[]
    x3items=[]
    
    frequent_pairs = [pair for pair, count in candidate_pairs.items() if count >= support_threshold]
    for a in frequent_pairs:
        
        s=support(baskets,a)
        if s >=18:
            x1pairs.append(a)
            
            conf_dict[tuple(sorted(a))]=s
    
    frequent_triplets = [triplet for triplet, count in candidate_triplets.items() if count >= support_threshold]
    for b in frequent_triplets:
        s=support(baskets,b)
        if s>=18:
            x2triplets.append(b)
            conf_dict[tuple(sorted(b))]=s
    
    for c in frequent_items:
        
        s=support(baskets,c)
        
        if s>=18:
            x3items.append((c,))
            
            conf_dict[(c,)]=item_counts[(c)]


    return x3items+x1pairs+x2triplets



file= open("Projects/Project3/Groceries_dataset.csv","r") 

file1=file.readline()
list_pur=[]

file2=file.read()
file2=file2.split('\n')[:-1]
lst=[]
for i in file2:
  i=i.split(',')
  lst.append(i)


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
baskets=final_lst


support_threshold = 18
result = pcy_algorithm(baskets, support_threshold)

print(result) #Frequent itemsets
itemsets_list=[]
for d in result:
    if len(d)>=2:
        itemsets_list.append(d)


from itertools import chain, combinations

# ... (your existing code)

# Function to generate all non-empty subsets of a given set
def generate_subsets(itemset):
    return chain.from_iterable(combinations(itemset, r) for r in range(1, len(itemset)))

# Function to generate association rules from frequent itemsets
def generate_association_rules(frequent_itemsets):
    rules = []
    #print(frequent_itemsets)
    for itemset in frequent_itemsets:
       
        subsets = generate_subsets(itemset)
        
        for subset in subsets:
            a= set(subset)
            b = set(itemset) - a
            x=a.union(b)
            x1=tuple(sorted(tuple(x)))
            a1=tuple(sorted(tuple(a)))
            c1=conf_dict[x1]
            c2=conf_dict[a1]
            conf=c1/c2
            if conf>=0.06:
             rules.append((a,b,conf))
    
    return rules



association_rules=generate_association_rules(itemsets_list)

for rule in association_rules:
     antecedent_str = ', '.join(rule[0])
     consequent_str = ', '.join(rule[1])
     conf=(rule[2])
     print(f"Conf({antecedent_str} -> {consequent_str}) : {conf} ")

''' 
Below Uncommented code is again for confidence between various frequent itemsets
'''
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


# My PCY algorithm produced the same output as the Apriori algorithm, but the thing is it was faster than the apriori algorithm. It computed
# the correct algorithm in less than 10 seconds, while my Apriori algorithm took a lot of time to compute the frequent itemsets and much more time 
# to get the confidence of each association rule.

#This hash-based methods helps PCY scale better to large datasets and improves its runtime efficiency in comparison to Apriori, 
# particularly when dealing with sparse datasets where most itemsets are infrequent. 
