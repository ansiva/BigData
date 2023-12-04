import numpy as np
from math import sqrt
import random
from collections import defaultdict
random.seed(50)
# I. Data Loading and Exploration
# Load the u.data file
data_path = "Projects/Project4/u.data"
# data = np.genfromtxt(data_path, delimiter='\t')
# print(data)
movie_ids = dict()
user_ids = []
ratings = []
timestamps = []
with open(data_path, 'r') as file:
    for line in file:
        
        parts = line.split()
        
        
        user_id = int(parts[0])
        
        movie_id = int(parts[1])
        rating = int(parts[2])
        timestamp = int(parts[3])
        
        if movie_id in movie_ids:
            
            movie_ids[movie_id]+=[(user_id,rating)]
        else:
            
            movie_ids[movie_id]=[(user_id,rating)]
        

movies = list(movie_ids.keys())
random.shuffle(movies)

train_size = int(0.81 * len(movies))
train_movies = movies[:train_size]
test_movies = movies[train_size:]

train_data = {movie: movie_ids[movie] for movie in train_movies}
test_data = {movie: movie_ids[movie] for movie in test_movies}





hidden_data=dict()
for i in test_data:
    n = len(test_data[i])
    if n>1:
        n = int(0.81*n)
        l=(test_data[i])
        random.shuffle(l)
        b=l[n:]
        test_data[i]=l[:n]
    
        hidden_data[i]=b
    
train_data.update(test_data)


def cosine_similarity(vector1, vector2):
    
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    if norm_vector1 == 0 or norm_vector2 == 0:
        return 0 

    similarity = dot_product / (norm_vector1 * norm_vector2)
    
    return similarity

def calculate_cosine_similarity(list1, list2):
    # Extract movie names and ratings from tuples
    users1, ratings1 = zip(*list1)
    users2, ratings2 = zip(*list2)

    # Create a set of all unique movie names
    all_users = set(users1 + users2)

    # Create vectors for each list with ratings for all movies
    vector1 = [ratings1[users1.index(user)] if user in users1 else 0 for user in all_users]
    vector2 = [ratings2[users2.index(user)] if user in users2 else 0 for user in all_users]

    # Convert the vectors to numpy arrays
    vector1 = np.array(vector1)
    vector2 = np.array(vector2)

    # Calculate cosine similarity
    similarity = cosine_similarity(vector1, vector2)

    return similarity

def predict_ratings(train_data, test_data, k=5):
    b=dict()
    predictions = defaultdict(list)
    
    for test_movie in test_data:
        test_users, test_ratings = zip(*test_data[test_movie])
        
        for train_movie in train_data:
            if train_movie != test_movie:
                train_users, train_ratings = zip(*train_data[train_movie])

                # Create vectors for each list with ratings for all movies
                vector_test = [test_ratings[test_users.index(user)] if user in test_users else 0 for user in train_users]
                vector_train = [train_ratings[train_users.index(user)] if user in train_users else 0 for user in train_users]

                # Calculate cosine similarity
                similarity = cosine_similarity(vector_test, vector_train)

                predictions[test_movie].append((train_movie, similarity))

        # Sort the neighbors based on similarity
        predictions[test_movie] = sorted(predictions[test_movie], key=lambda x: x[1], reverse=True)
        #
        # Select the top k neighbors
        top_k_neighbors = predictions[test_movie][:k]
        # print((top_k_neighbors))
        # print("232222222222")
        # print(test_movies)
        # print(train_movies)
        
        # Predict the rating for each movie in the test set
        for user in test_users:
            numerator = 0
            denominator = 0

            for neighbor, similarity in top_k_neighbors:
                if user in dict(train_data[neighbor]):
                    # print(dict(train_data[neighbor]))
                    # print(movie)
                    neighbor_rating = dict(train_data[neighbor])[user]
                    numerator += similarity * neighbor_rating
                    denominator += abs(similarity)

            if denominator != 0:
                predicted_rating = numerator / denominator
                
                if test_movie not in b:
                    b[test_movie]=[(user,predicted_rating)]
                else:
                    b[test_movie]+=[(user,predicted_rating)]
                
    
    return b

# Function to evaluate the model using RMSE
def evaluate_model(predictions, test_data):
    count=0
    count1=0
    squared_errors = []

    for test_movie in test_data:
        true_ratings = dict(test_data[test_movie])
        #print(predictions[test_user])
        #break
        predicted_ratings = dict(predictions[test_movie])

        for user in true_ratings:
            
            if user in predicted_ratings:
                

                error = (true_ratings[user] - predicted_ratings[user]) ** 2
                squared_errors.append(error)

    mse = np.mean(squared_errors)
    #rmse = sqrt(mse)
    
    return mse


predictions = predict_ratings(train_data, hidden_data, k=425)
#print(len(predictions))
#print(test_data)
print(evaluate_model(predictions,hidden_data)) #Mean squared error

for j in predictions:
    movie=j
    for k in predictions[j]:
        user=k[0]
        rating=k[1]

        print("Predicted Rating - Movie: ",movie, ", User: ", user, "Rating: ", rating)


# The Item-based filtering has a slight increase in the mean squared error when compared to the user based filtering model
#  but not a significant one at all. This could be because of some movies being rated by very few users, which was not the case with
# the user based filtering model as every user had a minimum movies rated count of 20 while the number of items wasn't given that guarantee.
# This type of filtering predicts the rating given by the user on a particular movie by looking at the similarity between movies and predicting the rating with those similar movies.

#But overall, user-based has a lower squared error, but can't say it is a better model because of the insignificant difference.
