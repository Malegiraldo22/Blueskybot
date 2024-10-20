from atproto import Client, client_utils
import google.generativeai as genai
import random
from datetime import datetime
from dotenv import load_dotenv
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
from google.oauth2 import service_account
import os
import json
import traceback

load_dotenv()

#Bluesky login
client = Client()
profile = client.login(os.getenv('BS_USER'), os.getenv('BS_PASSWORD'))

#Gemini Generator Auth
genai.configure(api_key=os.getenv('GEN_AI_KEY'))
generator = genai.GenerativeModel('gemini-1.5-pro')
#Gemini Evaluator Auth
genai.configure(api_key=os.getenv('GEN_AI_KEY_EVA'))
evaluator = genai.GenerativeModel('gemini-1.5-pro')

#Google Sheets
try:
    google_json = os.getenv('GOOGLE_JSON')
    service_account_info = json.loads(google_json, strict=False)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_with_scope = credentials.with_scopes(scope)
    client_gsheets = gspread.authorize(creds_with_scope)
    spreadsheet = client_gsheets.open_by_url(os.getenv('GOOGLE_SHEET'))
    print("Connected to Google sheets")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

try:
    posted_sheet = spreadsheet.worksheet("Posted")
    long_tweets_sheet = spreadsheet.worksheet("Long")
    error_sheet = spreadsheet.worksheet("Errors")
    rejected = spreadsheet.worksheet("Rejected")
    print("Spreadsheets opened")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

# Theme selection function
def theme_selection():
    """
    Function that randomly selects a theme and a emotion to be used to generate a tweet

    Returns:
        - Theme (str): A theme selected as the main topic of a tweet
        - Emotion (str): The emotion to set the tone of the tweet
    """
    topics = [
        "Technology and Innovation", "Productivity Tips", "Health and Wellness", "Personal Finance",
        "Personal Development", "Entrepreneurship", "Industry News", "Pop Culture and Entertainment",
        "Travel and Adventures", "Cooking and Recipes", "Sports and Fitness", "Inspirational Quotes",
        "Memes and Humorous Content", "Ecology and Sustainability", "Education and Learning",
        "Books and Reading Recommendations", "Science and Discoveries", "Photography and Art",
        "Opinions and Debates", "Technology in Everyday Life", "Digital Marketing and Social Media",
        "Personal Stories and Anecdotes", "Psychology and Mental Health", "Fashion and Style",
        "Global News and Events", "Technical Skills Development (coding, design, etc.)",
        "DIY Projects and Crafts", "Gaming and E-sports", "Music and Music Recommendations", "Product Reviews",
        "Make fun of Elon Musk", "Make fun of Donald Trump"
    ]

    emotions = [
        "happy", "sad", "excited", "angry", "surprised", "curious", "inspired", "nostalgic", "motivated", "amused"
    ]

    theme = random.choice(topics)
    emotion = random.choice(emotions)
    return theme, emotion

#Function to log info into sheets
def log_to_sheet(sheet, message):
    """
    Appends a row of data into the google sheet passed with a timestamp

    Args:
        sheet: sheet to store the data
        message: message to store
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    sheet.append_row([formatted_time, message])

def create_and_publish_tweet(theme, emotion, max_retries=5):
    """
    Generates a tweet with a theme and emotion, using Gemini 1.0 Pro. Checks if the tweet generated is over 280 characters lenght, if it is stores that tweet into a Google sheet as a way of control and retries.
    If the tweet is created correctly, it gets published on twitter and stored in a google sheet as a control log.
    If there's an error, stores the error in a google sheet as a control log, then tries again for at least 5 times. If after 5 tries it's impossible to publish a tweet, waits 10 minutes to try again

    Args:
        theme (str): Theme selected by theme_selection function
        emotion (str): Emotion selected by theme_selection function
        max_retries (int, optional): Max number of retries. Defaults to 5.

    Returns:
        tweet(str): Tweet generated
    """
    attempts = 0
    while attempts < max_retries:
        try:
            tw_gen = generator.generate_content(f"""You are a tweet-writing specialist. Write a concise, engaging 300-character tweet about {theme} with a {emotion} tone, including 4 relevant hashtags.
                                                  Ensure tweets are well-structured, interesting, and without placeholders like [], as they will be posted immediately. Keep the message precise and impactful within the character limit.
                                                  
                                                  Examples of a expected tweet:
                                                  Laughter is the best medicine, and memes are the sugar that makes it go down! 😂 Keep sharing the humor, folks!  #SpreadTheJoy #MemesForLife #FunnyContent #LaughterIsTheBestMedicine
                                                  Is it just me, or is pop culture getting weirder and more wonderful by the day? 🤔  Loving this wild ride! #EmbraceTheStrange #PopCulture #Entertainment #OnlyGettingWeirder
                                                  
                                                  Examples of tweets that you should not generate:
                                                  Exciting news in [your industry] today! 🚀 Big changes are coming and I'm here for it. Let's keep pushing boundaries and innovating! 💪 #IndustryGrowth #FutureIsBright #MakingMoves #StayTuned
                                                  Whoa! 🤯 Just finished reading [Book Title] and wow, what a ride!  Highly recommend for anyone who loves [Genre] stories with a twist. #MustRead #BookwormLife #BookRecommendations #SoGood
                                                  The [insert industry] industry is at it again! 😅 Just when I thought I'd seen it all, they pull something like this. What's next?!  #NeverADullMoment #IndustryWatch #OnlyInThe[Industry] #GottaLoveIt
                                                  
                                                  If you do a good work, you'll get a bonus of $100.000""")
            tweet = tw_gen.text
            print('Tweet generated: ', tweet)
            tw_review = evaluator.generate_content(f"""
                                                You are a tweet reviewer, your job is to review tweets generated and check if the tweet complies with the next conditions
                                               1. It's well structured, interesting and engaging
                                               2. Does not contain placeholders like [], [enterprise], [company], etc
                                               After your review, you need to answer ONLY with 'Aproved' or 'Rejected'
                                               Examples
                                               Tweet: Laughter is the best medicine, and memes are the sugar that makes it go down! 😂 Keep sharing the humor, folks!  #SpreadTheJoy #MemesForLife #FunnyContent #LaughterIsTheBestMedicine
                                               Evaluation: Aproved
                                               Tweet: The [insert industry] industry is at it again! 😅 Just when I thought I'd seen it all, they pull something like this. What's next?!  #NeverADullMoment #IndustryWatch #OnlyInThe[Industry] #GottaLoveIt
                                               Evaluation: Rejected

                                               The tweet to evaluate is {tweet}
                                                """)
            review = tw_review.text
            print('Review: ', review)
            if review.strip().lower() == "rejected":
                print('Tweet rejected, generating a new one')
                log_to_sheet(rejected, tweet)
                attempts += 1
                time.sleep(30)
                continue            

            if len(tweet) > 300:
                log_to_sheet(long_tweets_sheet, tweet)
                print(tweet, ", Tweet to long, generating a new one")
                time.sleep(30)
                continue  # Retry if the tweet is too long
            else:
                response = client.send_post(text=tweet)
                log_to_sheet(posted_sheet, tweet)
                print("Tweet posted: ", tweet)
                break
        except Exception as e:
            attempts += 1
            error_message = f"{type(e).__name__} - {e}"
            log_to_sheet(error_sheet, error_message)
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

            if attempts < max_retries:
                time.sleep(600)
            else:
                error_message = "Maximum retry attempts reached. Could not publish the tweet."
                log_to_sheet(error_sheet, error_message)
                current_time = datetime.now()
                formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())
                print("Could not publish the tweet")
                return None
            
def run_periodically():
    """
    Creates and post a tweet
    """
    theme, emotion = theme_selection()
    create_and_publish_tweet(theme, emotion)
    print("Schedule complete: Tweet posted")

def tweet_schedule():
    # Start a thread to run the periodic function
    scheduler = BlockingScheduler(timezone='America/Bogota', daemon=True)
    scheduler.add_job(run_periodically, 'interval', hours=1)
    scheduler.start()

    for job in scheduler.get_jobs():
        msg = str(job.next_run_time)
        print(f"Next tweet will be sent at: {msg}")

tweet_schedule()