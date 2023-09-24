file= open("/Users/aniruthansivakumar/BigData/Projects/fradulent_emails.txt","r", errors="ignore") 

start=0





def map_1(filename,file1): #file fradulent emails.txt
        l=[]
        for word in file1.split():
                
            
                l+=[(word,1)]
        return l

a=file.read()

                 
        
map_op=(map_1("Fradulent emails", a)) #[(word,1),(word,1),(hello,1)]

print("Example of the output of the map function")
print(map_op[:10])
       

big_group=sorted(map_op)               
# print((big_group))


i1=0


def grouping(list_):
        
        eqlist=[]
        final_list=[]
        for i in list_:
                if len(eqlist)==0:
                        eqlist.append(i)
                elif (i==eqlist[0]):
                        eqlist.append(i)
                else:
                        final_list+=[eqlist]
                        eqlist=[i]

        if len(eqlist)!=0:
                 final_list+=[eqlist] #[[('Abdio', 1)], [('Hello', 1), ('Hello', 1)], [('Joke', 1)], [('Jokes', 1)], [('Mega', 1)], [('Tho', 1)], [('Wonderful', 1)], [('in', 1)]]

        new_grp_list=[]
        for a in final_list:
                if len(a)==1:
                        val=[a[0][1]]
                        new_grp_list+=[(a[0][0],val)]
                else:
                        val_1=[]
                        
                        for a1 in a:
                                
                                
                                val_1.append(a1[1])
                        new_grp_list+=[(a1[0],val_1)]
                                
        return  new_grp_list

                        


grouped =grouping(big_group)
print("Example of the output of the grouping function")

#print(grouped)
def reduce(key,values):
        sum_val=sum(values)
        return key,sum_val


word_count=[]
for q in grouped:
        
                k_1=q[0]
                val_1=q[1]
                
                word_count+=[(reduce(k_1,val_1))]

#print("Example of the output of the reduce function")
#print(word_count)

def most_used_words(list_,number):
        dup_list=list_
        most_words=[]
        for h in range(number):
          max=0
          for i in dup_list:
                 
                 if i[1]>max:
                         max=i[1]
                         key_=i[0]
       
          dup_list.remove((key_,max))
          most_words+=[(key_,max)]
        
        return most_words

print(most_used_words(word_count,40))
# [('the', 73641), ('to', 61308), ('of', 52996), ('and', 41009), ('I', 38663), ('in', 33475), ('you', 29527), 
# ('this', 26616), ('a', 25180), ('for', 23119), ('your', 22427), ('my', 21608), ('that', 19074), 
# ('will', 18801)  , ('as', 17535), ('is', 16419), ('be', 14207), ('with', 13866), ('me', 11972), ('have', 10990)]


#4 They are normal words in use. We can't decide if it is a spam email with these 
# words, as it is also likely for these words to be present in a non-spam email, as
#it is hard to build a sentence structure in an email without these words.

# However if we take the next 20 words after that, we are able to get some unique keywords that can be related with a spam email 
#For example: money, account, etc. But then that is also not conclusive.

#My algorithm also calculates some codes with some special characters, which are quite irrelevant to the word counting
#problem. So, if I am able to filter the file into file of just emails with words, the time complexity of my program could decrease .
#The algorithm can also be improved by having more than one map function too.
          

