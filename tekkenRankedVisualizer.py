import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting

from waitress import serve
from flask import Flask, request, jsonify, send_file, render_template_string, redirect, url_for, session
from flask_session import Session
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import pandas as pd
import io
import json
from io import StringIO
from dateutil.relativedelta import relativedelta

# Import the plotting functions from plotting.py
from plotting import plot_daily_gains, plot_win_rates, plot_opponent_distribution

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Configure server-side session storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

def fetch_player_data(player_id, start_date=None, end_date=None):
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

    # Filter by date range if provided
    if start_date and end_date:
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    elif start_date or end_date:
        raise ValueError("Both start_date and end_date must be provided.")

    # Sort the DataFrame by 'whenDateTime'
    df = df.sort_values(by='whenDateTime')

    return df

@app.route('/')
def home():
    # Get today's date
    today = datetime.today()

    # Subtract one month
    one_month_ago = today - relativedelta(months=1)

    # Format the dates as 'YYYY-MM-DD'
    end_date = today.strftime('%Y-%m-%d')
    start_date = one_month_ago.strftime('%Y-%m-%d')

    return render_template_string('''
    <html>
    <head>
        <title>Player Visualization Tool</title>
    </head>
    <body>
        <h1>Player Visualization Tool</h1>
        <p>Welcome to the <a href="https://wank.wavu.wiki" target="_blank">wank.wavu.wiki</a> player data Visualization tool. This tool allows you to visualize player data from the wank.wavu.wiki website.</p>
        <h2>How It Works</h2>
        <p>Enter the URL of a player's profile from <a href="https://wank.wavu.wiki" target="_blank">wank.wavu.wiki</a> in the textbox below. For example: <a href="https://wank.wavu.wiki/player/3BgbnRiDAaMa" target="_blank">https://wank.wavu.wiki/player/3BgbnRiDAaMa</a>. The tool will fetch the player's data and allow you to generate three different types of graphs: rating gain, win rate percentage against each character, and opponent character usage percentage against you.</p>
        <h2>Enter your player URL:</h2>
        <form action="/fetch_data" method="post">
            <label for="player_url">Player URL:</label>
            <input type="text" id="player_url" name="player_url" style="width:400px;">
            <label for="start_date">Start Date:</label>
            <input type="date" id="start_date" name="start_date" value="{{ start_date  }}">
            <label for="end_date">End Date:</label>
            <input type="date" id="end_date" name="end_date" value="{{ end_date }}">
            <button type="submit">Fetch Data</button>
        </form>
        <div id="graphs" style="margin-top:20px;">
            {% if graphs %}
                <h2>Choose a graph type:</h2>
                <form action="/visualize" method="get">
                    <input type="hidden" name="player_id" value="{{ player_id }}">
                    <input type="hidden" name="start_date" value="{{ start_date }}">
                    <input type="hidden" name="end_date" value="{{ end_date }}">
                    <label for="character">Character:</label>
                    <select name="character" id="character">
                        {% for char in characters %}
                            <option value="{{ char }}">{{ char }}</option>
                        {% endfor %}
                    </select>
                    <br><br>
                    <button type="submit" name="graph" value="daily_gains">Daily Gains</button>
                    <button type="submit" name="graph" value="win_rates">Win Rates</button>
                    <button type="submit" name="graph" value="distribution">Opponent Distribution</button>
                </form>
            {% endif %}
        </div>
    </body>
    </html>
    ''', graphs=False, end_date=end_date, start_date=start_date)


@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    player_url = request.form.get('player_url')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not player_url:
        return jsonify({"error": "Player URL is required."}), 400

    # Calculate default start_date as one month prior to the current date if not provided
    if not start_date:
        start_date = (datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')

    # Convert date strings to datetime.date objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Extract the player ID from the URL
    player_id = player_url.split('/')[-1]

    try:
        df = fetch_player_data(player_id, start_date, end_date)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if df.empty:
        return jsonify({"error": "No data found for the given player URL."}), 400

    characters = df['character'].unique()
    if len(characters) == 0:
        return jsonify({"error": "No characters found for the given player URL."}), 400

    # Store the DataFrame in session as JSON
    session['player_data'] = df.to_json(orient='split')

    # Pass current date to the template
    current_date = datetime.today().strftime('%Y-%m-%d')

    return redirect(url_for('visualize_options', player_id=player_id, start_date=start_date, end_date=end_date))

@app.route('/visualize_options')
def visualize_options():
    player_id = request.args.get('player_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Retrieve the DataFrame from the session
    player_data = session.get('player_data')
    if not player_data:
        return jsonify({"error": "No player data found in session. Please fetch data again."}), 400

    df = pd.read_json(StringIO(player_data), orient='split')

    characters = df['character'].unique()
    
    return render_template_string('''
    <html>
    <head>
        <title>Player Visualization tool</title>
    </head>
    <body>
        <h1>Player Visualization tool</h1>
        <p>Data fetched successfully for player: {{ player_id }}</p>
        <h2>Choose a character and graph type:</h2>
        <form action="/visualize" method="get">
            <input type="hidden" name="player_id" value="{{ player_id }}">
            <input type="hidden" name="start_date" value="{{ start_date }}">
            <input type="hidden" name="end_date" value="{{ end_date }}">
            <label for="character">Character:</label>
            <select name="character" id="character">
                {% for char in characters %}
                    <option value="{{ char }}">{{ char }}</option>
                {% endfor %}
            </select>
            <br><br>
            <button type="submit" name="graph" value="daily_gains">Daily Gains</button>
            <button type="submit" name="graph" value="win_rates">Win Rates</button>
            <button type="submit" name="graph" value="distribution">Opponent Distribution</button>
        </form>
    </body>
    </html>
    ''', player_id=player_id, start_date=start_date, end_date=end_date, characters=characters)


@app.route('/visualize', methods=['GET'])
def visualize():
    player_id = request.args.get('player_id')
    char = request.args.get('character')
    graph = request.args.get('graph')
    start_date = request.args.get('start_date') 
    end_date = request.args.get('end_date') or datetime.today().strftime('%Y-%m-%d')

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

    # Retrieve the DataFrame from the session
    player_data = session.get('player_data')
    if not player_data:
        return jsonify({"error": "No player data found in session. Please fetch data again."}), 400

    df = pd.read_json(StringIO(player_data), orient='split')

    characters = df['character'].unique()
    
    if char not in characters:
        return jsonify({"error": "Invalid character."}), 400
    
    if graph == 'daily_gains':
        buf = plot_daily_gains(df, char, start_date, end_date)
    elif graph == 'win_rates':
        buf = plot_win_rates(df, char, start_date, end_date)
    elif graph == 'distribution':
        buf = plot_opponent_distribution(df, char, start_date, end_date)
    else:
        return jsonify({"error": "Invalid graph type. Use 'daily_gains', 'win_rates', or 'opponent_distribution'."}), 400
    
    if buf is None:
        return jsonify({"error": f"No data found for character '{char}'."}), 400
    
    # Return the plots as a response
    return send_file(buf, mimetype='image/png')


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)

    
