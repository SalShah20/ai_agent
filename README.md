# New Grad Job Application Agent

This tool helps you find and apply for entry-level positions at startups by generating personalized cold emails.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Download ChromeDriver:
   - Go to https://sites.google.com/a/chromium.org/chromedriver/downloads
   - Download the version that matches your Chrome browser
   - Extract `chromedriver.exe` and place it in the same directory as your Python script

3. Create a `.env` file in the project directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Using the Email Generation Feature

1. **Fill in Your Profile Information**
   - Click on the "Your Information" section at the top
   - Enter your:
     - Full Name
     - Degree (e.g., "Computer Science", "Business Administration")
     - Graduation Year
     - Key Skills (comma-separated list)
     - Notable Achievements (e.g., "Won hackathon award", "Published research paper")
     - Current Location
   - Click "Save Profile" to store your information

2. **Find Startups to Apply To**
   - Find a VC (Venture Capital) firm's portfolio website
   - Common examples include:
     - Y Combinator: https://www.ycombinator.com/companies/
     - Sequoia Capital: https://www.sequoiacap.com/portfolio/
     - Andreessen Horowitz: https://a16z.com/portfolio/

3. **Generate Cold Emails**
   - Copy the VC website URL
   - Paste it in the "VC Website URL" field
   - Click "Search and Generate Emails"
   - The tool will:
     1. Scrape startups from the VC website
     2. Generate personalized cold emails using your profile information
     3. Display the emails in the results area

4. **Using the Generated Emails**
   - Each email is personalized for a specific startup
   - The emails will include:
     - Your name and degree information
     - Your relevant skills
     - Your achievements
     - How you can contribute to the startup
   - You can copy any email directly from the results area
   - Review and customize the email before sending

## Tips for Successful Applications

1. Customize Further
   - Review the startup's website and recent news
   - Add specific details about their products or mission
   - Tailor the email to match their company culture

2. Follow Up
   - Send a follow-up email if you don't hear back
   - Connect on LinkedIn
   - Share relevant projects or achievements

3. Track Your Applications
   - The tool will save your applications in `new_grad_jobs.xlsx`
   - Keep notes about your interactions
   - Follow up on deadlines

## Troubleshooting

- If you get an error about the API key, check your `.env` file
- If no startups are found, try a different VC website
- If emails aren't generating, make sure you've saved your profile information

## Requirements

- Python 3.8+
- OpenAI API key
- Selenium
- ChromeDriver
- Internet connection
- Excel (for tracking applications)
