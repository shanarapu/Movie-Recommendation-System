# 🎬 Movie Recommendation System

A smart **Movie Recommendation Web App** built with **Python** and **Streamlit**, powered by both **Content-Based Filtering** and **Collaborative Filtering** techniques.  
It suggests movies similar to a selected title and provides rich movie details fetched live from the **TMDb API**.

---

## 🚀 Features

- 🔍 **Two Recommendation Methods**
  - **Content-Based Filtering** — recommends movies similar in content/features.
  - **Collaborative Filtering** — recommends movies based on user–movie interactions using KNN.
- 🎭 **Genre Filtering** — filter recommendations by your preferred genres.
- ⭐ **Sorting Options** — sort movies by rating or release year.
- 🖼️ **Dynamic Movie Posters** — fetched directly from TMDb.
- 🔥 **Trending Movies Section** — shows currently popular movies.
- 🆕 **New Releases Section** — displays movies currently in theaters.

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **Backend** | Python |
| **Data Processing** | Pandas, NumPy, SciPy |
| **Machine Learning** | scikit-learn (KNN model) |
| **API** | TMDb (The Movie Database API) |
| **Model Serialization** | Pickle |

---

## 📁 Project Structure

├── app.py # Streamlit web app
├── movie-recommender-system.ipynb # Jupyter notebook for model development
└── README.md # Project documentation
