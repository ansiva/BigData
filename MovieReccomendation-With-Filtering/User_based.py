import numpy as np

import random
from collections import defaultdict
random.seed(350)
# I. Data Loading and Exploration
# Load the u.data file
data_path = "Projects/Project4/u.data"
# data = np.genfromtxt(data_path, delimiter='\t')
# print(data)
user_ids = dict()
movie_ids = []
ratings = []
timestamps = []
with open(data_path, 'r') as file:
    for line in file:
        
        parts = line.split()
        
        
        user_id = int(parts[0])
        
        movie_id = int(parts[1])
        rating = int(parts[2])
        timestamp = int(parts[3])
        
        if user_id in user_ids:
            
            user_ids[user_id]+=[(movie_id,rating)]
        else:
            
            user_ids[user_id]=[(movie_id,rating)]
        

users = list(user_ids.keys())
random.shuffle(users)

train_size = int(0.8 * len(users))
train_users = users[:train_size]
test_users = users[train_size:]

train_data = {user: user_ids[user] for user in train_users}
test_data = {user: user_ids[user] for user in test_users}


#print(len(train_data))
#print((test_data))

hidden_data=dict()
for i in test_data:
    n = len(test_data[i])
    n = int(0.8*n)
    l=(test_data[i])
    random.shuffle(l)
    b=l[n:]
    test_data[i]=l[:n]
    
    hidden_data[i]=b
    
train_data.update(test_data)
#print(len(train_data))

def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    if norm_vector1 == 0 or norm_vector2 == 0:
        return 0

    similarity = dot_product / (norm_vector1 * norm_vector2)
    return similarity

def normalize_ratings(data):
    # Normalize ratings to have zero mean for each user
    normalized_data = {}
    for user, ratings in data.items():
        mean_rating = np.mean([rating for _, rating in ratings])
        normalized_ratings = [(movie, rating - mean_rating) for movie, rating in ratings]
        normalized_data[user] = normalized_ratings
    return normalized_data



def predict_ratings(train_data, test_data, k=5):
    b=dict()
    predictions = defaultdict(list)
    
    for test_user in test_data:
        test_movies, test_ratings = zip(*test_data[test_user])
        
        for train_user in train_data:
            if train_user != test_user:
                train_movies, train_ratings = zip(*train_data[train_user])

                # Create vectors for each list with ratings for all movies
                x=train_data[train_user]
                y=train_data[test_user]
                dict1=dict(x)
                dict2=dict(y)
              
                all_keys = set(dict1.keys()).union(dict2.keys())


                vectora = [0] * len(all_keys)
                vectorb = [0] * len(all_keys)

                for i, key in enumerate(all_keys):
                    if key in dict1:
                        vectora[i] = dict1[key]
                    if key in dict2:
                        vectorb[i] = dict2[key]
                       
                norm_vectora = np.linalg.norm(vectora)
                norm_vectorb = np.linalg.norm(vectorb)

                if norm_vectora != 0:
                        vectora = [val / norm_vectora for val in vectora]

                if norm_vectorb != 0:
                        vectorb = [val / norm_vectorb for val in vectorb]

               # Calculate cosine similarity

                # if ((train_user==377 or train_user==858) and (test_user==377 or test_user==858 )):
                #            print(y1)
                #            print(x1)
                #            print(111111111)
                #            print(test_user)
                #            print(train_user)
                #            print(vectora)
                #            print(vectorb)
                #            print(cosine_similarity(vectora, vectorb))
                #            break
                similarity = cosine_similarity(vectora, vectorb)



                predictions[test_user].append((train_user, similarity))

        # Sort the neighbors based on similarity
        predictions[test_user] = sorted(predictions[test_user], key=lambda x: x[1], reverse=True)
        # if test_user==377:
        #     top_k_neighbors = predictions[test_user][:k]
        #     print(top_k_neighbors[0])
        #     break
            
        # Select the top k neighbors
        top_k_neighbors = predictions[test_user][:k]
        # print(test_user)
        # print((top_k_neighbors))
        # break
        # print("232222222222")
        # print(test_movies)
        # print(train_movies)
        
        # Predict the rating for each movie in the test set
        for movie in test_movies:
            numerator = 0
            denominator = 0

            for neighbor, similarity in top_k_neighbors:
                if movie in dict(train_data[neighbor]):
                    # print(dict(train_data[neighbor]))
                    #print(movie)
                    neighbor_rating = dict(train_data[neighbor])[movie]
                    #print(neighbor_rating)
                    numerator += similarity * neighbor_rating
                    denominator += abs(similarity)

            if denominator != 0:
                predicted_rating = numerator / denominator
                #print(predicted_rating,neighbor_rating)
                
                if test_user not in b:
                    b[test_user]=[(movie,predicted_rating)]
                else:
                    b[test_user]+=[(movie,predicted_rating)]
                
    
    return b

# Function to evaluate the model using RMSE
def evaluate_model(predictions, hid_data):
    
    squared_errors = []

    for test_user in hid_data:
        true_ratings = dict(hid_data[test_user])
        #print(predictions[test_user])
        #break
        predicted_ratings = dict(predictions[test_user])

        for movie in true_ratings:
            
            if movie in predicted_ratings:
                

                error = (true_ratings[movie] - predicted_ratings[movie]) ** 2
                squared_errors.append(error)

    mse = np.mean(squared_errors)
    rmse = sqrt(mse)
    
    return rmse




predictions = predict_ratings(train_data, hidden_data, k=450)
print(evaluate_model(predictions,hidden_data))
train_data=normalize_ratings(train_data)
hidden_data=normalize_ratings(hidden_data)
predictions = predict_ratings(train_data, hidden_data, k=450)
print(evaluate_model(predictions,hidden_data))

for j in predictions:
    user=j
    for k in predictions[j]:
        movie=k[0]
        rating=k[1]

        print("Predicted Rating - User: ",user, ", Movie: ", movie, "Rating: ", rating)
