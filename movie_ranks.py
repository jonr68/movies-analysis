import requests
from bs4 import BeautifulSoup
import csv


def get_movie_rankings():
    """
    Scrapes the Rotten Tomatoes website for a list of new movies and their Tomatometer scores.

    Returns:
        A list of tuples, where each tuple contains (movie_title, tomatometer_score).
    """
    url = "https://editorial.rottentomatoes.com/guide/best-new-movies/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP errors

        soup = BeautifulSoup(response.content, 'html.parser')
        # print(soup)

        movies = []
        # The movies are listed in div elements with the class 'row countdown-item'
        movie_containers = soup.find_all('div', class_='row countdown-item')


        for container in movie_containers:
            # Extract the movie title
            title_tag = container.select('div.col-sm-20.col-full-xs > div > h2 > a')
            title = title_tag[0].text.strip()


            # Extract the Tomatometer score
            score_tag = container.find('div', class_='countdown-item-content').find('span', class_='tMeterScore')
            score = score_tag.text.strip() if score_tag else None

            if title and score:
                movies.append((title, score))
        print(movies)
        return movies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

get_movie_rankings()
def save_to_csv(data, filename="best_new_movies.csv"):
    """
    Saves a list of movie data to a CSV file.

    Args:
        data: A list of tuples, where each tuple is (movie_title, tomatometer_score).
        filename: The name of the CSV file to save.
    """
    if not data:
        print("No data to save. The list of movies is empty.")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write the header row
        writer.writerow(['Movie Title', 'Tomatometer Score'])

        # Write the data rows
        writer.writerows(data)

    print(f"Successfully saved {len(data)} movies to {filename}")


if __name__ == "__main__":
    movie_list = get_movie_rankings()
    if movie_list:
        save_to_csv(movie_list)
