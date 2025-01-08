# Bluesky Tweet Generator

This project is a Python-based tweet generator that uses the Gemini AI model to create engaging and authentic tweets. It leverages the Bluesky API to publish these tweets, and integrates with Google Sheets for logging and control.

## Features

-   **AI-Powered Tweet Generation:** Uses the Gemini AI model to generate tweets based on random themes and voices.
-   **Tweet Review:** Evaluates generated tweets for quality, authenticity, and structure before posting.
-   **Automatic Posting:** Publishes tweets directly to Bluesky using the API.
-   **Google Sheets Integration:** Logs successful posts, rejected tweets, long tweets, and errors to Google Sheets for monitoring and control.
-   **Scheduled Posting:** Uses `apscheduler` to schedule tweets to be posted at regular intervals.
-   **Error Handling & Retries:** Implements robust error handling with retry mechanisms to ensure consistent tweet publishing.

## Requirements

Before running the application, you must have the following:

1.  **Python 3.6+** installed.
2.  **Bluesky Account**: You'll need a Bluesky username and password.
3.  **Google Cloud Project**: Create a Google Cloud Project and enable the Google Sheets API.
4.  **Service Account Key**: Download the service account key in JSON format to authorize the application for Google Sheets.
5.  **Google Gemini API Keys:** Obtain API keys for the current Gemini version for content generation and evaluation.
6.  **.env File**: Create a `.env` file in the root directory and add the required environment variables.
    
## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Malegiraldo22/Blueskybot.git
    cd Blueskybot
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file** in the root directory and add the following variables:

    ```env
    BS_USER=your_bluesky_username
    BS_PASSWORD=your_bluesky_password
    GEN_AI_KEY=your_gemini_api_key_for_generation
    GEN_AI_KEY_EVA=your_gemini_api_key_for_evaluation
    GOOGLE_JSON='{"type": "service_account", "project_id": "your_project_id", "private_key_id": "your_private_key_id", "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n", "client_email": "your_client_email", "client_id": "your_client_id", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "your_client_x509_cert_url"}'
    GOOGLE_SHEET=your_google_sheet_url
    ```

    Replace the placeholders with your actual data.

## Usage

To run the tweet generator:

```bash
python bot.py
```

This will start the scheduler, which posts a tweet every hour based on a random theme and voice, logging all actions into the configured Google Sheets.

## Configuration

* Themes and Voices: The `theme_selection` function defines the list of themes and voices used to generate the tweets. You can modify these lists to fit your needs.
* Scheduling: The `tweet_schedule` function is set to post a tweet every hour, but it can be adjusted as desired
* Google Sheets: The program uses the Google Sheets API to store information, it requires the creation of a google sheet with the following sheets: "Posted", "Long", "Errors" and "Rejected".

## Logging

The script logs the following events to Google Sheets:

* **Posted**: Log of all successful tweets posted
* **Long**: Log of tweets that are too long
* **Errors**: Log of any errors encountered during the process
* **Rejected**: Log of tweets that were rejected by the review process

## Error Handling

* The script includes a retry mechanism in case there is any error during the process of tweet generation or posting
* All errors are logged to the Error Sheet in your Google Sheet
* After reaching the maximum number of retries, the script will wait 10 minutes before trying again

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License. See `LICENSE` for more information.