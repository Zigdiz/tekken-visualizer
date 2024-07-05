# plotting.py

import matplotlib.pyplot as plt
import io
import pandas as pd  # Add this import

def plot_daily_gains(df, char, start_date, end_date):
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
    plt.title(f'Daily Gains in Rating for {char}\n({start_date} to {end_date})')
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

def plot_win_rates(df, char, start_date, end_date):
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

    plt.title(f'Win Rates by Opponent Character for {char}\n({start_date} to {end_date})')
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

def plot_opponent_distribution(df, char, start_date, end_date):
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
    plt.title(f'Opponent Character Distribution for {char}\n({start_date} to {end_date})')
    plt.tight_layout()

    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf
