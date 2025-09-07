import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
import time
import datetime
import json





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

    pulled_at = datetime.datetime.now().date().isoformat()
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





def fetch_tomatometer_score(title):
    """Search Rotten Tomatoes for the movie title and return the Tomatometer score."""
    print(f"Searching for: {title}")
    search_url = f"https://www.rottentomatoes.com/search?search={requests.utils.quote(title)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        print("Fetching search results page...")
        resp = requests.get(search_url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        print("Parsing search results...")
        movie_link = soup.select_one('search-page-media-row a')
        if not movie_link:
            print("No movie link found.")
            return None
        movie_href = movie_link['href']
        if movie_href.startswith('http'):
            movie_url = movie_href
        else:
            movie_url = "https://www.rottentomatoes.com" + movie_href
        print(f"Fetching movie page: {movie_url}")
        movie_resp = requests.get(movie_url, headers=headers)
        movie_resp.raise_for_status()
        movie_soup = BeautifulSoup(movie_resp.content, 'html.parser')
        score_script = movie_soup.find('script', {'id': 'media-scorecard-json', 'type': 'application/json'})
        if score_script:
            data = json.loads(score_script.string)
            score = data.get('criticsScore', {}).get('scorePercent')
            if score:
                print(f"Found score: {score}")
                return score
        print("No score found on movie page.")
        return None
    except Exception as e:
        print(f"Error fetching score for '{title}': {e}")
        return None

def update_rankings_from_box_office(db_file="movies.sql"):
    """Fetches movie titles from box_office, gets Tomatometer scores, and saves only today's results to rankings."""
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM box_office")
    titles = [row[0] for row in cursor.fetchall()]
    print(len(titles), "titles found in box_office table.")
    conn.close()

    results = []
    for title in titles:
        score = fetch_tomatometer_score(title)
        if score:
            results.append((title, score, today))
        time.sleep(1)  # Be polite to Rotten Tomatoes

    # Only save records for today
    if results:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS rankings
                       (
                           id                INTEGER PRIMARY KEY AUTOINCREMENT,
                           title             TEXT,
                           tomatometer_score TEXT,
                           pulled_at         TEXT
                       )
                       ''')
        # Delete any previous records for today to avoid duplicates
        cursor.execute('DELETE FROM rankings WHERE pulled_at = ?', (today,))
        cursor.executemany('''
            INSERT INTO rankings (title, tomatometer_score, pulled_at)
            VALUES (?, ?, ?)
        ''', results)
        conn.commit()
        conn.close()
        print(f"Saved {len(results)} scores to rankings table for {today}.")
    else:
        print("No scores found for today.")

if __name__ == "__main__":
    box_office = get_movie_box_office()
    if box_office:
        save_box_office_to_sqlite(box_office)
        export_table_to_csv('box_office', 'box_office.csv')
        update_rankings_from_box_office()
        export_table_to_csv('rankings', 'rankings.csv')