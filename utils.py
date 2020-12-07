#Libraries to extract music data
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

#Libraries to deal with special data types and automatization process
import time
from IPython.core.display import clear_output
from collections import defaultdict

#Libraries to deal with text from wikipedia and extract music genre words
import wikipedia
import string
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from collections import Counter


#Function to validate credentials from spotify api
def credentials():
    
    CLIENT_ID = 'your_client_id'
    CLIENT_SECRET = 'your_client_secret'
    USERNAME = 'your_username_id'
    REDIRECT_URI = 'your_redirect_url' # I usually use http://localhost:8888/callback/

    #Scopes for authorization to Spotify API  more information on this link: https://developer.spotify.com/documentation/general/guides/scopes/
    SCOPE_USER = 'user-library-read'
    SCOPE_PLAYLIST = 'playlist-modify-public'

    #Credentials to access the Spotify Music Data
    manager = SpotifyClientCredentials(CLIENT_ID,CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=manager)

    #Credentials to access to  the Spotify User's Playlist, Favorite Songs, etc. 
    auth_manager = SpotifyOAuth(scope=SCOPE_USER,client_id=CLIENT_ID,client_secret=CLIENT_SECRET,username=USERNAME, redirect_uri=REDIRECT_URI)
    spt = spotipy.Spotify(auth_manager=auth_manager)

    auth_playlist = SpotifyOAuth(scope=SCOPE_PLAYLIST,client_id=CLIENT_ID,client_secret=CLIENT_SECRET,username=USERNAME, redirect_uri=REDIRECT_URI)
    spp = spotipy.Spotify(auth_manager=auth_playlist)
    
    return sp, spt ,spp



#function that returns the ids of the current user saved music
def get_saved_song_ids(spt,sp,playlist_id=None,is_playlist=False):

    track_ids = list()

    if is_playlist:

        playlist = sp.playlist_tracks(playlist_id)
        total_songs = playlist['total']

        for i in range(0,total_songs,100):
            tracks = sp.playlist_tracks(playlist_id,limit=100,offset=i)
            for track in tracks['items']:
                track_ids.append(track['track']['id'])

    else:

        user = spt.current_user_saved_tracks()
        total_songs = user['total']

        for i in range(0,total_songs,20):
            tracks = spt.current_user_saved_tracks(limit=20,offset=i)
            for track in tracks['items']:
                track_ids.append(track['track']['id'])

    return track_ids

#Function that gets the main features of each song
def get_features_saved_songs(tracks_ids,sp):

    dict_features = defaultdict(list)

    dict_features['id'] = tracks_ids

    for track_id in tracks_ids:

        meta = sp.track(track_id)
        dict_features['name'].append(meta['name'])
        dict_features['album'].append(meta['album']['name'])
        dict_features['artist'].append(meta['album']['artists'][0]['name'])

    return dict_features



#Function to join single words in bigrams
def words_to_ngrams(words, n, sep=" "):
       return [sep.join(words[i:i+n]) for i in range(len(words)-n+1)]

# Function to Search  music genre information from wikipedia 
def search_genres_on_wikipedia(query):

    english_stopwords = stopwords.words('english') 
    with open('musicgenresdata.txt',encoding='utf-8') as file:
        genres = file.read()
        genres = genres.lower().split("\n")
    
    page = wikipedia.page(query)
    page = page.content.lower()

    #Tokenization process and remove the punctuation and stopwords (Natural Language Processing Tools)
    text  = "".join(word for word in page if word not in string.punctuation)
    text_rm = [word for word in text.split() if (word not in english_stopwords)]
    bigrams = words_to_ngrams(text_rm,2,sep=" ")
    match_genres = [words for words in bigrams if words in genres]

    return match_genres

#Functions that uses the functions above to automate the process of searching music genres from dataframe information
def find_music_genre_on_wikipedia(df):

    print("Finding Music Genres From Wikipedia....")
    #List where the music genre will save
    track_genre = list()

    #Iterate through each row and define the query to search on wikipedia
    for i in df.index:
        try:
            query = df.name.iloc[i] + " " + df.artist.iloc[i]
            genre = search_genres_on_wikipedia(query.lower())
        except:
            try:
                query = df.album.iloc[i] + " " + df.artist.iloc[i]
                genre = search_genres_on_wikipedia(query.lower())
            except:
                try:
                    query =  df.artist.iloc[i]
                    genre = search_genres_on_wikipedia(query.lower())
                except:
                    genre = 'nan'
                    
        #Count frecuency of words realted with music genres
        count_genre = Counter(genre)
        sorted_genre = sorted(count_genre,key=count_genre.get,reverse=True)
        track_genre.append(sorted_genre)

    #Save the result on a new dataframe column
    df['genre'] = track_genre


    #Convert the results of list to a string
    for n in df.index:
        df.genre.iloc[n] = ", ".join(word for word in df.genre.iloc[n])
    #Replace null genre values with no information 
    for n in df.index:
        if len(df.genre.iloc[n]) <=0:
            df.genre.iloc[n] = 'no information'

        
    clear_output(wait=True)

    print("Process Finished!")

    return df

#Functions that uses spotify database to automate the process of searching music genres from dataframe information
def finding_music_genre_on_spotify(df,sp):

    print("Finding Music Genres From Spotify....")
    track_ids = df.id.tolist()
    #List where the music genre will save
    track_genre = list()

    #Iterate through each row and define the song id to search on spotify
    for ids in track_ids:

        track = sp.track(ids)
        albums_id = track['album']['id']
        artist_id = track['artists'][0]['id']

        album = sp.album(albums_id)
        artist = sp.artist(artist_id)

        if len(album['genres']) <=0:
            track_genre.append(artist['genres'])
        else:
            track_genre.append(album['genres'])

    #Save the result on a new dataframe column
    df['genre'] = track_genre

    #Convert the results of list to a string
    for n in df.index:
        df.genre.iloc[n] = ", ".join(word for word in df.genre.iloc[n])
        
    #Replace null genre values with no information
    for n in df.index:
        if len(df.genre.iloc[n]) <=0:
     
            df.genre.iloc[n] = 'no information'
    clear_output(wait=True)
    print("Process Finished!")

    return df