from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import os
import time
from datetime import datetime
from tqdm import tqdm

# Initialize WebDriver
driver = webdriver.Chrome()

# Open Twitter and navigate to the account page
account_username = "CNN"
driver.get(f"https://twitter.com/{account_username}")

# Wait for manual login
input("Log in manually in the opened browser window and press Enter here...")

# Number of tweets you want to fetch
# Twitter now has a 500 read limit for newly created accounts
# 1k for old accounts and 10k for the verfied accounts
NUM_TWEETS_TO_FETCH = 500

tweets_data = []
already_seen = set()  # Keep track of tweets we've already processed
total_skipped = 0  # Total number of skipped tweets
total_fetched = 0  # Initialize total fetched counter

def scroll_and_fetch_tweets():
    global total_skipped, already_seen, total_fetched
    stagnant_count = 0
    previous_count = 0  # Ensure previous_count is initialized outside the loop

    while len(tweets_data) < NUM_TWEETS_TO_FETCH:
        error_count = 0
        fetched_this_scroll = 0

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        tweets_elements = driver.find_elements(By.CSS_SELECTOR, 'article')

        for tweet in tweets_elements:
            tweet_id = hash(tweet.text)
            if tweet_id not in already_seen:
                already_seen.add(tweet_id)
                tweet_data = {}
                try:
                    content_spans = tweet.find_elements(By.CSS_SELECTOR, 'div > div > div > div > span')
                    tweet_data['Content'] = ' '.join([span.text for span in content_spans])
                    tweet_data['Likes'], tweet_data['Retweets'], tweet_data['Comments'] = (
                        element.text if (element := tweet.find_element(By.CSS_SELECTOR, f'div[data-testid="{type_}"]'))
                        else '0' for type_ in ('like', 'retweet', 'reply'))
                    tweet_data['Time'] = (
                        time_element.get_attribute('datetime') if (time_element := tweet.find_element(By.CSS_SELECTOR, 'time'))
                        else 'N/A')

                    fetched_this_scroll += 1

                except Exception:
                    error_count += 1
                    total_skipped += 1
                    continue

                tweets_data.append(tweet_data)

        total_fetched += fetched_this_scroll
        print("===============")
        print(f"\rSkipped this scroll: {error_count}", end='')
        print(f"\nTotal skipped: {total_skipped}", end='')
        print(f"\nFetched this scroll: {fetched_this_scroll}", end='')
        print(f"\nTotal fetched: {total_fetched}\n", end='')

        current_count = len(tweets_data)
        if current_count == previous_count:
            stagnant_count += 1
        else:
            stagnant_count = 0
            previous_count = current_count

        if stagnant_count >= 3:
            print("\nNo new tweets found for three consecutive attempts. Ending data collection...")
            break

        time.sleep(1)

scroll_and_fetch_tweets()

# Ensure the DataFrame is created even if no data was fetched
if tweets_data:
    tweets_df = pd.DataFrame(tweets_data)
else:
    print("No data was fetched. Exiting...")
    driver.quit()
    exit()

# Create the outputs directory if it doesn't exist
output_dir = "outputs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Construct the file path and confirm it
timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
filename = f"{output_dir}/{account_username}_tweets_{timestamp_str}.xlsx"
print(f"Saving data to {filename}...")

# Implement tqdm for the progress bar
with tqdm(total=100, desc="Saving data", leave=False) as pbar:
    for i in range(100):
        time.sleep(0.01)  # Simulating save progress
        pbar.update(1)

# Saving the DataFrame to Excel and verifying
tweets_df.to_excel(filename, index=False)
print(f"Data successfully saved to {filename}")

# Cleanup
driver.quit()
