# Player Visualization Tool/API

This project fetches player data from the [wank.wavu.wiki](https://wank.wavu.wiki) website and provides visualizations for rating gains, win rates against different characters, and opponent character usage.

## Features

- Fetch player data from the specified URL.
- Visualize daily rating gains.
- Visualize win rates against different opponent characters.
- Visualize the distribution of opponent characters.

## Prerequisites

- Python 3.6+
- `requests` library
- `beautifulsoup4` library
- `flask` library
- `waitress` library
- `matplotlib` library
- `pandas` library

## How to Run

1. Clone this repository:
2. Start the server:
   The server will start on `http://0.0.0.0:8000`.

## Fetch Data as JSON

Fetches player data, including match history, character win rates, and current ratings.

### Endpoint

`GET /fetch_data_json`

### Request Parameters

- **player_url** (required): The URL of the player's profile. This is used to identify the player.
- **start_date** (optional): The start date for fetching match history. Format: YYYY-MM-DD. Defaults to one month prior to the current date if not provided.
- **end_date** (optional): The end date for fetching match history. Format: YYYY-MM-DD. Defaults to the current date if not provided.

### Example Requests

#### Example 1: Fetching Data for a Player

GET /fetch_data_json?player_url=https://wank.wavu.wiki/player/3BgbnRiDAaMa&start_date=2024-06-30&end_date=2024-07-30

### Response

```json
{
  "player_id": "3BgbnRiDAaMa",
  "start_date": "2024-06-30",
  "end_date": "2024-07-30",
  "characters": {
    "Azucena": {
      "win_rate": 0.75,
      "current_rating": 1939
    },
    "Claudio": {
      "win_rate": 0.60,
      "current_rating": 1925
    }
  },
  "matches": [
    {
      "whenDateTime": "2024-06-30 14:00",
      "character": "Azucena",
      "score": "2-1",
      "isWin": true,
      "rating": 1900,
      "ratingChange": 39,
      "newRating": 1939,
      "opponentName": "Opponent1",
      "opponentChar": "Nina",
      "opponentRating": 1800,
      "opponentRatingChange": -20,
      "newOpponentRating": 1780
    },
    {
      "whenDateTime": "2024-07-01 16:30",
      "character": "Claudio",
      "score": "1-2",
      "isWin": false,
      "rating": 1925,
      "ratingChange": 0,
      "newRating": 1925,
      "opponentName": "Opponent2",
      "opponentChar": "Kazuya",
      "opponentRating": 1950,
      "opponentRatingChange": 10,
      "newOpponentRating": 1960
    }
  ]
}
```

### Response Format

- **player_id**: The unique identifier for the player.
- **start_date**: The start date of the data range.
- **end_date**: The end date of the data range.
- **characters**: An object containing information about each character played by the player.
  - **character_name**: The name of the character.
  - **win_rate**: The win rate for this character.
  - **current_rating**: The current rating for this character.
- **matches**: A list of match records containing detailed information about each match.
  - **whenDateTime**: The date and time of the match.
  - **character**: The character played by the player.
  - **score**: The score of the match.
  - **isWin**: Whether the match was won by the player.
  - **rating**: The rating before the match.
  - **ratingChange**: The change in rating after the match.
  - **newRating**: The new rating after the match.
  - **opponentName**: The name of the opponent.
  - **opponentChar**: The character played by the opponent.
  - **opponentRating**: The opponent's rating before the match.
  - **opponentRatingChange**: The change in the opponent's rating after the match.
  - **newOpponentRating**: The new rating of the opponent after the match.
 
# POST Endpoint: /fetch_data

This endpoint fetches player data, including match history, character win rates, and current ratings, for a specified player.

### Request

- **URL**: `/fetch_data`
- **Method**: `POST`

#### Request Parameters

- **player_url** (required): The URL of the player's profile.
- **start_date** (optional): The start date for fetching match history. Defaults to one month prior to the current date if not provided. Format: `YYYY-MM-DD`.
- **end_date** (optional): The end date for fetching match history. Defaults to the current date if not provided. Format: `YYYY-MM-DD`.

#### Response

- **Success**: Redirects to the visualization options page with player ID, start date, and end date as query parameters.
- **Error**: Returns a JSON response with an error message and a status code of 400.

#### Example Usage

To fetch data for a player, you need to send a POST request to `/fetch_data` with the `player_url`, and optionally `start_date` and `end_date`. The server processes the request as follows:

1. Retrieves the `player_url` from the form data. If not provided, returns an error message.
2. Retrieves the `start_date` and `end_date` from the form data. If not provided, sets `start_date` to one month prior and `end_date` to the current date.
3. Extracts the `player_id` from the URL.
4. Fetches player data and calculates win rates and current ratings for each character played by the player.
5. Stores the data in the session and redirects to the visualization options page.

# Endpoint: /visualize_options

This endpoint provides an interface for selecting visualization options based on the player's data.

### Request

- **URL**: `/visualize_options`
- **Method**: `GET`

#### Parameters

- **player_id** (required): The unique identifier for the player.
- **start_date** (optional): The start date of the data range.
- **end_date** (optional): The end date of the data range.

#### Description

The `/visualize_options` endpoint retrieves player data and displays a web page where users can view character ratings and win rates. It also allows users to select a character and choose a graph type for visualization, including daily gains, win rates, or opponent distribution.

#### Example Response

The response includes a table displaying each character's rating and win rate, with a form for selecting visualization options.

---

# Endpoint: /visualize

This endpoint generates visualizations for a specified character and graph type.

#### Request

- **URL**: `/visualize`
- **Method**: `GET`

#### Request Parameters

- **player_id** (required): The unique identifier for the player.
- **character** (required): The character to visualize data for.
- **graph** (required): The type of graph to generate (`daily_gains`, `win_rates`, or `distribution`).
- **start_date** (optional): The start date for the data range.
- **end_date** (optional): The end date for the data range. Defaults to the current date if not provided.

#### Response

- **Success**: Returns a plot image based on the selected character and graph type.
- **Error**: Returns a JSON response with an error message and a status code of 400 if any required parameters are missing or invalid.

#### Example Usage

To visualize data for a player, send a GET request to `/visualize` with the `player_id`, `character`, and `graph` parameters. The server processes the request as follows:

1. Validates that all required parameters are provided.
2. Retrieves the player data from the session.
3. Generates the requested graph based on the character and date range.
4. Returns the plot as an image.

  <h2>Example graphs:</h2>
  
  ![image](https://github.com/Zigdiz/tekken-visualizer/assets/35729336/98aea1db-43f5-441f-ae64-ed15ce399874)
  ![image](https://github.com/Zigdiz/tekken-visualizer/assets/35729336/b2445a3e-6df1-42b1-b257-7ade0e2b7842)
  ![image](https://github.com/Zigdiz/tekken-visualizer/assets/35729336/3be07029-0b04-4352-90ab-049799eaa113)
