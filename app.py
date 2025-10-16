import streamlit as st
import pickle
import pandas as pd
import requests
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import os


# Mobile-Friendly UI (uncomment if needed)
# st.set_page_config(layout="wide")

# ------------------------------
# Functions
# ------------------------------

@st.cache_data
def fetch_movie_details(movie_id):
    """
    Fetch movie details from TMDb API.
    Returns a dictionary with:
      - poster: URL for the movie poster image
      - vote_average: Movie rating (formatted to 1 decimal)
      - release_year: Year extracted from release_date
      - genres: Comma-separated genre names
      - homepage: URL of the movie's homepage
    """
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=7715a12395bcf543f2e73cf956eb4a57&language=en-US'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        poster_url = "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get(
            'poster_path') else "https://via.placeholder.com/500"
        vote_average = f"{data.get('vote_average', 0.0):.1f}"
        release_date = data.get("release_date", "")
        release_year = release_date[:4] if release_date else "N/A"
        genres_list = data.get("genres", [])
        genres = ", ".join([genre["name"] for genre in genres_list]) if genres_list else "N/A"
        homepage = data.get("homepage", "#")

        return {
            "poster": poster_url,
            "vote_average": vote_average,
            "release_year": release_year,
            "genres": genres,
            "homepage": homepage
        }
    except requests.exceptions.RequestException:
        return {
            "poster": "https://via.placeholder.com/500",
            "vote_average": "N/A",
            "release_year": "N/A",
            "genres": "N/A",
            "homepage": "#"
        }


def recommend_content(movie):
    """
    Content-Based Recommendation:
    Uses the precomputed content similarity matrix.
    """
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = []
    recommended_details = []

    # Skip the movie itself and get next 8 recommendations
    for i in distances[1:9]:
        movie_id = movies.iloc[i[0]].movie_id
        movie_title = movies.iloc[i[0]].title
        details = fetch_movie_details(movie_id)
        recommended_movies.append(movie_title)
        recommended_details.append(details)
    return recommended_movies, recommended_details


def recommend_collaborative(movie):
    try:
        # find the row index of the selected movie in movies_collab
        movie_id = movies_collab.loc[movies_collab['title'] == movie, 'movieId'].values[0]
        idx = pivot_df.index.get_loc(movie_id)  # Make sure you load this pivot_df

        # get 6 neighbors (1 self + 5 recs)
        distances, indices = knn_model.kneighbors(csr_data[idx], n_neighbors=6)
        recommended_titles = []
        for idx in indices.flatten()[1:]:
            recommended_movie_id = pivot_df.index[idx]
            title = movies_collab.loc[movies_collab['movieId'] == recommended_movie_id, 'title']
            if not title.empty:
                title_row = title.values[0]
                recommended_titles.append(title_row)
            else:
                st.warning(f"Movie ID {recommended_movie_id} not found.")
    except IndexError:
        st.error("❌ The selected movie does not exist in the collaborative dataset.")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return []

    return recommended_titles




# ------------------------------
# Data Loading
# ------------------------------

movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))
movies_dict_collab=pickle.load(open('movie_dict_collab.pkl','rb'))
movies_collab=pd.DataFrame(movies_dict_collab)
knn_model = pickle.load(open('knn_model.pkl', 'rb'))
csr_data   = pickle.load(open('csr_data_clb.pkl'  , 'rb'))
pivot_df = pickle.load(open('similarity_collab.pkl', 'rb'))





# ------------------------------
# App Layout
# ------------------------------

st.title('🎬 Movie Recommender System')

# Sidebar: Filter options and Recommendation method
sample_genres = ["Action", "Adventure", "Family", "Fantasy", "Science Fiction", "Drama", "Comedy", "Romance"]
selected_genres = st.sidebar.multiselect("🎭 Filter by Genre", sample_genres)
sort_option = st.sidebar.selectbox("🔽 Sort recommended movies by:",
                                   ["Default", "Rating (High to Low)", "Year (Newest First)"])
method = st.sidebar.radio("Select Recommendation Method", ["Content-Based Filtering", "Collaborative Filtering"])

if method == "Content-Based Filtering":
    # Main movie selection dropdown
    selected_movie_name = st.selectbox('Movies which might give you same vibes as...!', movies['title'].values)
elif method=="Collaborative Filtering":
    selected_movie_name = st.selectbox('Movies which might give you same vibes as...!', movies_collab['title'].values)

# ------------------------------
# Recommendation Trigger
# ------------------------------

if st.button('Recommend'):
    with st.spinner("Fetching recommendations..."):
        # Choose recommendation method based on sidebar selection
        if method == "Content-Based Filtering":
            names, details_list = recommend_content(selected_movie_name)
            # Apply Genre Filter if any are selected
            if selected_genres:
                filtered_names = []
                filtered_details = []
                for name, details in zip(names, details_list):
                    if any(genre.lower() in details["genres"].lower() for genre in selected_genres):
                        filtered_names.append(name)
                        filtered_details.append(details)
                names, details_list = filtered_names, filtered_details

            # Apply Sorting
            if sort_option == "Rating (High to Low)":
                names, details_list = zip(*sorted(zip(names, details_list),
                                                  key=lambda x: float(
                                                      x[1]['vote_average'] if x[1]['vote_average'] != "N/A" else 0),
                                                  reverse=True))
            elif sort_option == "Year (Newest First)":
                names, details_list = zip(*sorted(zip(names, details_list),
                                                  key=lambda x: int(x[1]['release_year']) if x[1][
                                                                                                 'release_year'] != "N/A" else 0,
                                                  reverse=True))

            # Display Recommendations (in 4 columns per row)
            for i in range(0, len(names), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i + j < len(names):
                        with cols[j]:
                            st.text(names[i + j])
                            st.image(details_list[i + j]["poster"])
                            st.caption(f"⭐ {details_list[i + j]['vote_average']}")
                            st.caption(f"📅 {details_list[i + j]['release_year']}")
                            st.caption(f"🎭 {details_list[i + j]['genres']}")
                            # Homepage Link Button:
                            st.markdown(f'<a href="{details_list[i + j]["homepage"]}" target="_blank">Homepage</a>',
                                        unsafe_allow_html=True)
                            # st.markdown(f'<a href="{details_list[i + j]["homepage"]}" target="_blank">Homepage</a>',unsafe_allow_html=True)
        elif method == "Collaborative Filtering":
            names = recommend_collaborative(selected_movie_name)
            for name in names:
                st.write(f"• {name}")

# ------------------------------
# Top Trending Section
# ------------------------------

st.markdown("---")
st.subheader("🔥 Top Trending Movies (Based on Popularity)")

if 'popularity' in movies.columns and 'title' in movies.columns:
    top_movies = movies.sort_values(by='popularity', ascending=False).head(6)
    cols = st.columns(5)
    for i in range(5):
        movie_id = top_movies.iloc[i].movie_id
        movie_title = top_movies.iloc[i].title
        details = fetch_movie_details(movie_id)
        with cols[i % 5]:
            st.text(movie_title)
            st.image(details["poster"])
            st.caption(f"⭐ {details['vote_average']}")
            st.caption(f"📅 {details['release_year']}")
            st.caption(f"🎭 {details['genres']}")
            st.markdown(f'<a href="{details["homepage"]}" target="_blank">Homepage</a>', unsafe_allow_html=True)
else:
    st.warning("Trending data not available in the dataset.")

# ---- NEW RELEASES SECTION ----
st.markdown("---")
st.subheader("🆕 New Releases (In Theaters Now)")

try:
    now_playing_url = f"https://api.themoviedb.org/3/movie/now_playing?api_key=7715a12395bcf543f2e73cf956eb4a57&language=en-US&page=1"
    response = requests.get(now_playing_url)
    response.raise_for_status()
    now_playing_data = response.json()
    new_movies = now_playing_data.get('results', [])[:5]  # Get top 6 new releases

    cols = st.columns(5)
    for i, movie in enumerate(new_movies):
        movie_id = movie.get('id')
        movie_title = movie.get('title', 'Untitled')
        details = fetch_movie_details(movie_id)

        with cols[i % 5]:
            st.text(movie_title)
            st.image(details["poster"])
            st.caption(f"⭐ {details['vote_average']}")
            st.caption(f"📅 {details['release_year']}")
            st.caption(f"🎭 {details['genres']}")
            st.markdown(f'<a href="{details["homepage"]}" target="_blank">Homepage</a>', unsafe_allow_html=True)
except requests.exceptions.RequestException as e:
    st.warning("Failed to fetch new releases. Please try again later.")




