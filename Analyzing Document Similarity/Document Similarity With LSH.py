from datasketch import MinHash
from datasketch import MinHashLSH
file= open("Projects/Project2/similarity","r") 
a=file.read()

b=a.split('\n\n')

item_to_remove =  ''
b = [item for item in b if item != item_to_remove]


num_perm = 128
num_bands = 16
threshold = 0.8
num_rows = num_perm // num_bands
def union(lsta,lstb):
    fin=lsta
    for i in lstb:
        if i not in lsta:
            fin.append(i)
    return fin

def inter(l1,l2):
    
    fin1=[]
    for i in l1:
        if i in l2:
            
            fin1.append(i)
    return fin1
            
#print(inter([1,2,3],[2,4,1]))


def jaccard(a,b):
    
    w=inter(a,b)
    q=union(a,b)
    if (len(q)!=0):
        return len(w)/len(q)
    else:
        return 0
def shingle(text,num):
    lst=[]
    for i in range(len(text)-num+1):
        if text[i:i+num] not in lst:
            lst+=[text[i:i+num]]
    return lst

# Function to create MinHash for a given document
def mh(paragraph, num_perm):
    m = MinHash(num_perm=num_perm)
    shingles = shingle(paragraph, 7)
    for s in shingles:
        m.update(s.encode('utf8'))
    return m

# Create MinHash objects for all documents
minhashes = [mh(para, num_perm) for para in b]

# Create LSH
lsh = MinHashLSH(num_perm=num_perm, threshold= threshold,params=(num_rows,num_bands)) #Banding technique

# Insert MinHashes into LSH
for i, minhash in enumerate(minhashes):
    lsh.insert(i, minhash)


candidate_pairs = []

for i in range(len(minhashes)):
    
    results = lsh.query(minhashes[i])
    
    #print(results)
    if len(results) > 1:
           if results not in candidate_pairs:
            candidate_pairs.append(results)

#print(candidate_pairs)
# Calculate Jaccard similarity for candidate pairs


similar_pairs = []
for pair in candidate_pairs:
         
         
         for i in range(len(pair)):
       
           for j in range(i + 1, len(pair)):
        
             # Compute the Jaccard similarity using MinHash signatures
             jaccard_similarity = jaccard(shingle(b[pair[i]],7),shingle(b[pair[j]],7))
            
             if jaccard_similarity >= 0.8: #Sometimes the looping might repeat over similar elements, which we won't need as their jaccard similarities are already present!
                 if ((pair[i], pair[j], jaccard_similarity)) not in similar_pairs:
                     if ((pair[j], pair[i], jaccard_similarity)) not in similar_pairs:
                        similar_pairs.append((pair[i], pair[j], jaccard_similarity))
                 
                 
        
            

if similar_pairs:
      for pair1 in similar_pairs:
          
        print(f"Similar Pair: Documents {pair1[0]} and {pair1[1]}, Jaccard Similarity: {pair1[2]}") # Index of the documents and the jaccard similarity between the documents are printed
else:
       print("No similar pairs found.")


# 3. I represented my textual data through shingles. Each paragraph was represented as a list fo shingles
# My shingle size was 7, as this size particularly compared the global information in the paragraphs 
#rather than the local text. Small shingle sizes may result in a higher jaccard similarity for a not so similar paragraphs,
#Hence, I picked a decently sized shingle size.

#4.Computing Minhash Signature matrices for each document and comparing them, would take a lot of memory and a higher time 
#complexity because of its dimensions. While the banding technique only checks the similarity between the candidate pairs,
# which is only the partion of the matrix, which reduces the complexity.

# This complexity is further reduced by LSH, by hashing the candidate pairs. This way similar pairs, end up in the 
#same bucket, which results in just comparing the Jaccard similarity of the candidate pairs.


#5.


#There are a lot of pairs very similar to each other. I am picking 5 pairs out of them which are 100% similar.
#Most Similar Pairs (Some of them)
pair1=(b[960],b[922])
pair2=(b[961],b[940])
pair3=(b[962],b[924])
pair4=(b[925],b[942])
pair5=(b[677],b[693])

print("")
print(pair1)
print("")
print(pair2)
print("")
print(pair3)
print("")
print(pair4)
print("")
print(pair5)
#Pairs. Paragraphs in pairs are separated by a comma
('    Deep in the heart of the Amazon rainforest, the dense canopy created a world of perpetual twilight. Exotic creatures, from brilliantly colored macaws to elusive jaguars, moved in the shadows of towering trees. The symphony of insects and the calls of howler monkeys provided a constant soundtrack to this verdant wilderness.', '    Deep in the heart of the Amazon rainforest, the dense canopy created a world of perpetual twilight. Exotic creatures, from brilliantly colored macaws to elusive jaguars, moved in the shadows of towering trees. The symphony of insects and the calls of howler monkeys provided a constant soundtrack to this verdant wilderness.')
('    On a remote island in the Pacific, a small fishing village was nestled against the shoreline. The turquoise waters stretched out to meet the horizon, and fishermen set sail each morning, returning with bountiful catches that sustained the close-knit community.', '    On a remote island in the Pacific, a small fishing village was nestled against the shoreline. The turquoise waters stretched out to meet the horizon, and fishermen set sail each morning, returning with bountiful catches that sustained the close-knit community.')
('    Within the walls of an ancient temple complex in Angkor Wat, intricately carved stone reliefs depicted scenes from myth and history. The imposing spires of the temple seemed to touch the sky, and the air was thick with a sense of spiritual reverence.', '    Within the walls of an ancient temple complex in Angkor Wat, intricately carved stone reliefs depicted scenes from myth and history. The imposing spires of the temple seemed to touch the sky, and the air was thick with a sense of spiritual reverence.')
('    In a bustling Moroccan bazaar, the narrow lanes were a labyrinth of colors and sounds. Merchants hawked their wares, from vibrant textiles to fragrant spices, while the aroma of street food filled the air. Bargaining was an art form, and every purchase was a dance of haggling and camaraderie.', '    In a bustling Moroccan bazaar, the narrow lanes were a labyrinth of colors and sounds. Merchants hawked their wares, from vibrant textiles to fragrant spices, while the aroma of street food filled the air. Bargaining was an art form, and every purchase was a dance of haggling and camaraderie.')
('    In the coral reefs of the ocean, a clownfish found refuge among the stinging tentacles of an anemone. This symbiotic relationship provided the clownfish with protection from predators while offering the anemone the benefit of food scraps and increased water circulation.', '    In the coral reefs of the ocean, a clownfish found refuge among the stinging tentacles of an anemone. This symbiotic relationship provided the clownfish with protection from predators while offering the anemone the benefit of food scraps and increased water circulation.')

#They are very much identical to each other. By very much, I mean literally the same.


