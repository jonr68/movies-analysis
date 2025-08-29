import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
from datetime import datetime


# def get_movie_rankings():
#     """
#     Scrapes the Rotten Tomatoes website for a list of new movies and their Tomatometer scores.
#
#     Returns:
#         A list of tuples, where each tuple contains (movie_title, tomatometer_score).
#     """
#     url = "https://editorial.rottentomatoes.com/guide/best-new-movies/"
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
#
#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()  # This will raise an exception for HTTP errors
#
#         soup = BeautifulSoup(response.content, 'html.parser')
#         # print(soup)
#
#         movies = []
#         # The movies are listed in div elements with the class 'row countdown-item'
#         movie_containers = soup.find_all('div', class_='row countdown-item')
#
#         for container in movie_containers:
#             # Extract the movie title
#             title_tag = container.select('div.col-sm-20.col-full-xs > div > h2 > a')
#             title = title_tag[0].text.strip()
#
#             # Extract the Tomatometer score
#             score_tag = container.find('div', class_='countdown-item-content').find('span', class_='tMeterScore')
#             score = score_tag.text.strip() if score_tag else None
#
#             if title and score:
#                 movies.append((title, score))
#         print(movies)
#         return movies
#
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching the URL: {e}")
#         return None


# def save_rankings_to_sqlite(data, db_file="movies.sql"):
#     if not data:
#         print("No data to save. The list of rankings is empty.")
#         return
#
#     pulled_at = datetime.now().date().isoformat()
#     data_with_time = [(title, score, pulled_at) for (title, score) in data]
#
#     conn = sqlite3.connect(db_file)
#     cursor = conn.cursor()
#     cursor.execute('''
#                    CREATE TABLE IF NOT EXISTS rankings
#                    (
#                        id                INTEGER PRIMARY KEY AUTOINCREMENT,
#                        title             TEXT,
#                        tomatometer_score TEXT,
#                        pulled_at         TEXT
#                    )
#                    ''')
#     cursor.executemany('''
#                        INSERT INTO rankings (title, tomatometer_score, pulled_at)
#                        VALUES (?, ?, ?)
#                        ''', data_with_time)
#     conn.commit()
#     conn.close()
#     print(f"Successfully saved {len(data)} rankings to {db_file}")


def get_movie_box_office():
    """
    Scrapes the Box Office Mojo website for a list of movies and their gross box office earnings.

    Returns:
        A list of tuples, where each tuple contains (movie_title, gross_earnings).
    """
    url = 'https://www.boxofficemojo.com/year/2025/?grossesOption=totalGrosses'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        movies = []

        # Find all rows in the table
        rows = soup.select('tr')

        if rows:
            # Skip the header row
            for row in rows[1:]:
                # Find all td elements in the row
                cells = row.find_all('td')
                if len(cells) >= 8:  # Make sure we have enough cells
                    # Title is in column 2, Gross is in column 8 (Total Gross)
                    title = cells[1].get_text(strip=True)
                    gross = cells[5].get_text(strip=True)
                    release_date = cells[10].get_text(strip=True)
                    distributor = cells[12].get_text(strip=True)
                    if title and gross:
                        movies.append((title, gross, release_date, distributor))

        return movies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None


def save_box_office_to_sqlite(data, db_file="movies.sql"):
    if not data:
        print("No data to save. The list of box office movies is empty.")
        return

    pulled_at = datetime.now().date().isoformat()
    data_with_time = [(title, gross, release_date, distributor, pulled_at) for (title, gross, release_date, distributor)
                      in data]

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS box_office
                   (
                       id           INTEGER PRIMARY KEY AUTOINCREMENT,
                       title        TEXT,
                       total_gross  TEXT,
                       release_date TEXT,
                       distributor  TEXT,
                       pulled_at    TEXT
                   )
                   ''')
    cursor.executemany('''
                       INSERT INTO box_office (title, total_gross, release_date, distributor, pulled_at)
                       VALUES (?, ?, ?, ?, ?)
                       ''', data_with_time)
    conn.commit()
    conn.close()
    print(f"Successfully saved {len(data)} box office movies to {db_file}")


import sqlite3
import csv


def export_table_to_csv(table_name, csv_filename, db_file="movies.sql"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    # Get column names
    column_names = [description[0] for description in cursor.description]
    conn.close()

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
        writer.writerows(rows)
    print(f"Exported {len(rows)} rows from {table_name} to {csv_filename}")


if __name__ == "__main__":
    rankings = get_movie_rankings()
    if rankings:
        save_rankings_to_sqlite(rankings)
        export_table_to_csv('rankings', 'rankings.csv')

    box_office = get_movie_box_office()
    if box_office:
        save_box_office_to_sqlite(box_office)
        export_table_to_csv('box_office', 'box_office.csv')

    # save_movies_to_csv(movie_list)
