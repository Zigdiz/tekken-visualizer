import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting

from waitress import serve

from flask import Flask, request, jsonify, send_file, render_template_string
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import io

app = Flask(__name__)

def fetch_player_data(player_id):
    # URL of the webpage
    url = f'https://wank.wavu.wiki/player/{player_id}'

    # Fetch the content of the webpage
    response = requests.get(url)
    web_content = response.content

    # Parse the webpage content
    soup = BeautifulSoup(web_content, 'html.parser')

    # Define a list to hold the parsed data
    data_list = []

    # Find the table in the webpage with <th>When</th>
    table = None
    for tbl in soup.find_all('table'):
        if tbl.find('th') and tbl.find('th').text.strip() == 'When':
            table = tbl
            break

    if table:
        tbody = table.find('tbody')
        if tbody:
            # Loop through each row in the table body
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                
                when_date_time = cells[0].text.strip() if cells[0] else ''
                character = cells[1].text.strip() if cells[1] else ''
                
                # Extract score and isWin
                score_lines = cells[2].text.strip().split()
                score = score_lines[0] if score_lines else ''
                is_win = score_lines[1] == "WIN" if len(score_lines) > 1 else False

                rating = int(cells[3].text.strip().split()[0]) if cells[3] else 0
                rating_change = int(cells[3].find('span').text.strip()) if cells[3].find('span') else 0
                new_rating = rating + rating_change
                opponent_name = cells[4].find('a').text.strip() if cells[4].find('a') else ''
                opponent_char = cells[5].text.strip() if cells[5] else ''
                opponent_rating = int(cells[6].text.strip().split()[0]) if cells[6] else 0
                opponent_rating_change = int(cells[6].find('span').text.strip()) if cells[6].find('span') else 0
                new_opponent_rating = opponent_rating + opponent_rating_change

                data = {
                    "whenDateTime": when_date_time,
                    "character": character,
                    "score": score,
                    "isWin": is_win,
                    "rating": rating,
                    "ratingChange": rating_change,
                    "newRating": new_rating,
                    "opponentName": opponent_name,
                    "opponentChar": opponent_char,
                    "opponentRating": opponent_rating,
                    "opponentRatingChange": opponent_rating_change,
                    "newOpponentRating": new_opponent_rating
                }
                
                data_list.append(data)

    # Convert the data_list to a DataFrame
    df = pd.DataFrame(data_list)

    # Convert 'whenDateTime' to datetime and extract date
    df['whenDateTime'] = pd.to_datetime(df['whenDateTime'], format='%d %b %Y %H:%M')
    df['date'] = df['whenDateTime'].dt.date

    # Sort the DataFrame by 'whenDateTime'
    df = df.sort_values(by='whenDateTime')

    return df

def plot_daily_gains(df, char):
    char_df = df[df['character'] == char]

    if char_df.empty:
        return None
    
    # Extract the last match of each day for the character
    last_matches = char_df.groupby('date').apply(lambda x: x.iloc[-1])
    
    # Calculate the daily rating gains
    last_matches['dailyGain'] = last_matches['newRating']

    # Plot the daily gains
    plt.figure(figsize=(10, 6))
    plt.plot(last_matches['date'], last_matches['dailyGain'], marker='o')
    plt.title(f'Daily Gains in Rating for {char}')
    plt.xlabel('Date')
    plt.ylabel('Rating')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def plot_win_rates(df, char):
    char_df = df[df['character'] == char]
    if char_df.empty:
        return None
    
    # Calculate win rates by opponent character
    win_rates = char_df.groupby('opponentChar')['isWin'].mean() * 100
    match_counts = char_df['opponentChar'].value_counts()

    # Create a DataFrame for visualization
    win_rate_df = pd.DataFrame({
        'opponentChar': win_rates.index,
        'winRate': win_rates.values,
        'matchCount': match_counts[win_rates.index].values
    })

    # Plot the win rates
    plt.figure(figsize=(12, 8))
    bars = plt.bar(win_rate_df['opponentChar'], win_rate_df['winRate'], color='skyblue')

    # Add annotations to the bars
    for bar, count in zip(bars, win_rate_df['matchCount']):
        plt.text(bar.get_x() + bar.get_width() / 2 - 0.2, bar.get_height() - 5,
                 f'{bar.get_height():.2f}%\n({count} matches)', ha='center', color='black')

    plt.title(f'Win Rates by Opponent Character for {char}')
    plt.xlabel('Opponent Character')
    plt.ylabel('Win Rate (%)')
    plt.xticks(rotation=45)
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def plot_opponent_distribution(df, char):
    char_df = df[df['character'] == char]
    
    if char_df.empty:
        return None  # Return None if no data for the character

    # Count the total number of matches against each opponent character
    opponent_counts = char_df['opponentChar'].value_counts()
    
    # Calculate the percentage of matches against each opponent character
    opponent_percentages = opponent_counts / opponent_counts.sum() * 100

    # Plot the distribution as a pie chart
    plt.figure(figsize=(10, 6))
    plt.pie(opponent_percentages, labels=opponent_percentages.index, autopct='%1.1f%%', startangle=140)
    plt.title(f'Opponent Character Distribution for {char}')
    plt.tight_layout()

    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

@app.route('/')
def home():
    return render_template_string('''
    <html>
    <head>
        <title>Player Visualization API</title>
    </head>
    <body>
        <h1>Player Visualization API</h1>
        <p>Welcome to the Player Visualization API. This API provides visualizations for player data.</p>
        <h2>Usage</h2>
        <p>To use this API, send a GET request to the <code>/visualize</code> endpoint with the following query parameters:</p>
        <ul>
            <li><code>player_id</code>: The ID of the player.</li>
            <li><code>character</code>: The character you want to visualize.</li>
            <li><code>graph</code>: The type of graph you want to generate. Valid options are <code>daily_gains</code>, <code>win_rates</code>, and <code>distribution</code>.</li>
        </ul>
        <h3>Example Requests</h3>
        <p>Daily Gains:</p>
        <code><a href="/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=daily_gains">/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=daily_gains</a></code>
        <p>Win Rates:</p>
        <code><a href="/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=win_rates">/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=win_rates</a></code>
        <p>Opponent Distribution:</p>
        <code><a href="/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=distribution">/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=distribution</a></code>
    </body>
    </html>
    ''')

@app.route('/visualize', methods=['GET'])
def visualize():
    player_id = request.args.get('player_id')
    char = request.args.get('character')
    graph = request.args.get('graph')
    
    missing_params = []
    if not player_id:
        missing_params.append('player_id')
    if not char:
        missing_params.append('character')
    if not graph:
        missing_params.append('graph')
    
    if missing_params:
        return jsonify({
            "error": f"Missing parameters: {', '.join(missing_params)}",
            "example_request": "/visualize?player_id=3BgbnRiDAaMa&character=Azucena&graph=daily_gains"
        }), 400
    
    df = fetch_player_data(player_id)
    if df.empty:
        return jsonify({"error": "No data found for the given player ID."}), 400
    
    characters = df['character'].unique()
    
    if char not in characters:
        return jsonify({"error": "Invalid character."}), 400
    
    if graph == 'daily_gains':
        buf = plot_daily_gains(df, char)
    elif graph == 'win_rates':
        buf = plot_win_rates(df, char)
    elif graph == 'distribution':
        buf = plot_opponent_distribution(df, char)
    else:
        return jsonify({"error": "Invalid graph type. Use 'daily_gains', 'win_rates', or 'opponent_distribution'."}), 400
    
    if buf is None:
        return jsonify({"error": f"No data found for character '{char}'."}), 400
    
    # Return the plots as a response
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)
