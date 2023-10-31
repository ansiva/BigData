
import warnings
import numpy as np
import pandas as pd
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
movie_ids_titles = pd.read_csv('Homeworks/movies.csv') #reading movies file -- Pandas library


movie_ids_ratings = pd.read_csv('Homeworks/ratings.csv') # reading ratings file




movie_ids_titles.drop("genres", inplace = True, axis = 1)  # Removing the genres column from the data 


movie_ids_ratings.drop("timestamp", inplace = True, axis =1) # Removing the column timestamp
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    merged_movie_df = pd.merge(movie_ids_ratings, movie_ids_titles,on='movieId') # Specifies in what level to do the merging
    movie_rating_mean_count = pd.DataFrame(columns=['rating_mean', 'rating_count'])

    movie_rating_mean_count["rating_mean"] = merged_movie_df.groupby('title')['rating'].mean() 
    movie_rating_mean_count["rating_count"] = merged_movie_df.groupby('title')['rating'].count()
#movie_rating_mean_count.dropna(inplace = True)

    user_movie_rating_matrix = merged_movie_df.pivot_table(index='userId', columns='title', values='rating')

#user_movie_rating_matrix.dropna(inplace=True)
    pulp_fiction_ratings = user_movie_rating_matrix["Jumanji (1995)"] 

    pulp_fiction_correlations = pd.DataFrame(user_movie_rating_matrix.corrwith(pulp_fiction_ratings), columns =["pf_corr"])
    pulp_fiction_correlations = pulp_fiction_correlations.join(movie_rating_mean_count["rating_count"])

    pulp_fiction_correlations_50 = pulp_fiction_correlations[pulp_fiction_correlations['rating_count'] > 50]




    print(pulp_fiction_correlations_50.sort_values('pf_corr',ascending=False).head())



#Movies reccomended for a viewer who saw Jumanji (with correlation):
# Jumanji (1995)              1.000000           110
# Notting Hill (1999)         0.798372            56
# Million Dollar Baby (2004)  0.716712            52
# Others, The (2001)          0.698576            55
# Donnie Brasco (1997)        0.687060            52
