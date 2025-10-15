import os
import openai
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from typing import List, Dict
import json
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

class NewGradJobAgent:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.gmail_service = None
        self.setup_gui()
        self.user_info = {
            'name': '',
            'degree': '',
            'graduation_year': '',
            'skills': '',
            'achievements': '',
            'location': ''
        }
        self.generated_emails = []  # Store generated emails for draft creation

    def authenticate_gmail(self):
        """Authenticate with Gmail API"""
        creds = None
        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        return True

    def create_gmail_draft(self, to_email: str, subject: str, body: str):
        """Create a draft email in Gmail"""
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            draft = {
                'message': {
                    'raw': raw_message
                }
            }
            
            draft_result = self.gmail_service.users().drafts().create(
                userId='me', body=draft).execute()
            
            return draft_result
        except Exception as e:
            raise Exception(f"Error creating draft: {str(e)}")

    def setup_gui(self):
        self.window = tk.Tk()
        self.window.title("New Grad Job Application Tracker")
        self.window.geometry("1000x800")

        # User Info Frame
        user_info_frame = ttk.LabelFrame(self.window, text="Your Information", padding="5")
        user_info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # User Info Fields
        ttk.Label(user_info_frame, text="Full Name:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.name_entry = ttk.Entry(user_info_frame, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(user_info_frame, text="Degree:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.degree_entry = ttk.Entry(user_info_frame, width=40)
        self.degree_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(user_info_frame, text="Graduation Year:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.grad_year_entry = ttk.Entry(user_info_frame, width=40)
        self.grad_year_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(user_info_frame, text="Key Skills:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.skills_entry = ttk.Entry(user_info_frame, width=40)
        self.skills_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(user_info_frame, text="Notable Achievements:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.achievements_entry = ttk.Entry(user_info_frame, width=40)
        self.achievements_entry.grid(row=4, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(user_info_frame, text="Current Location:").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.location_entry = ttk.Entry(user_info_frame, width=40)
        self.location_entry.grid(row=5, column=1, padx=5, pady=2, sticky="w")

        # Save Button
        ttk.Button(user_info_frame, text="Save Profile", command=self.save_user_info).grid(row=6, column=0, columnspan=2, pady=10)

        # Search Frame
        search_frame = ttk.LabelFrame(self.window, text="Search Jobs", padding="5")
        search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(search_frame, text="VC Website URL:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.url_entry = ttk.Entry(search_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Button(search_frame, text="Search and Generate Emails", 
                  command=self.search_startups_and_generate_emails).grid(row=0, column=2, padx=5, pady=2)

        # Gmail Actions Frame
        gmail_frame = ttk.LabelFrame(self.window, text="Gmail Actions", padding="5")
        gmail_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(gmail_frame, text="Authenticate Gmail", 
                  command=self.handle_gmail_auth).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(gmail_frame, text="Create Gmail Drafts", 
                  command=self.create_all_drafts).grid(row=0, column=1, padx=5, pady=5)
        
        self.gmail_status = ttk.Label(gmail_frame, text="Not authenticated")
        self.gmail_status.grid(row=0, column=2, padx=5, pady=5)

        # Results Frame
        self.results_text = tk.Text(self.window, height=20, width=120)
        self.results_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.window, command=self.results_text.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Status Frame
        status_frame = ttk.LabelFrame(self.window, text="Status", padding="5")
        status_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack()

        # Configure grid weights
        self.window.grid_rowconfigure(3, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

    def handle_gmail_auth(self):
        """Handle Gmail authentication"""
        try:
            self.status_label.config(text="Authenticating with Gmail...")
            self.window.update()
            
            if self.authenticate_gmail():
                self.gmail_status.config(text="✓ Authenticated")
                self.status_label.config(text="Gmail authentication successful!")
                messagebox.showinfo("Success", "Gmail authentication successful!")
            else:
                self.gmail_status.config(text="✗ Not authenticated")
                self.status_label.config(text="Gmail authentication failed")
        except Exception as e:
            messagebox.showerror("Error", f"Authentication failed: {str(e)}")
            self.status_label.config(text="Authentication failed")

    def create_all_drafts(self):
        """Create Gmail drafts for all generated emails"""
        if not self.gmail_service:
            messagebox.showerror("Error", "Please authenticate with Gmail first")
            return
        
        if not self.generated_emails:
            messagebox.showerror("Error", "No emails to create drafts from. Please generate emails first.")
            return
        
        try:
            self.status_label.config(text="Creating Gmail drafts...")
            self.window.update()
            
            draft_count = 0
            for email_data in self.generated_emails:
                try:
                    draft = self.create_gmail_draft(
                        to_email=email_data['to_email'],
                        subject=email_data['subject'],
                        body=email_data['body']
                    )
                    draft_count += 1
                    self.results_text.insert(tk.END, f"\n✓ Created draft for {email_data['startup_name']}\n")
                    self.window.update()
                except Exception as e:
                    self.results_text.insert(tk.END, f"\n✗ Failed to create draft for {email_data['startup_name']}: {str(e)}\n")
            
            self.status_label.config(text=f"Created {draft_count} Gmail drafts!")
            messagebox.showinfo("Success", f"Created {draft_count} Gmail drafts! Check your Gmail drafts folder.")
        except Exception as e:
            messagebox.showerror("Error", f"Error creating drafts: {str(e)}")
            self.status_label.config(text="Error creating drafts")

    def save_user_info(self):
        """Save user information from the GUI entries"""
        self.user_info = {
            'name': self.name_entry.get(),
            'degree': self.degree_entry.get(),
            'graduation_year': self.grad_year_entry.get(),
            'skills': self.skills_entry.get(),
            'achievements': self.achievements_entry.get(),
            'location': self.location_entry.get()
        }
        self.status_label.config(text="Profile saved successfully!")

    def scrape_vc_startups(self, vc_website: str) -> List[Dict]:
        """
        Scrape startup information from a VC website using requests.
        Returns a list of dictionaries containing startup details.
        """
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(vc_website, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Get the content of the page
            html_content = response.text
            
            # Debug: Show what we got
            print(f"Fetched {len(html_content)} characters from {vc_website}")
            
            # Use a more targeted approach based on common VC website patterns
            prompt = (
                "You are analyzing a venture capital firm's portfolio page. "
                "Extract information about portfolio companies/startups from this HTML content.\n\n"
                f"HTML Content (first 8000 chars):\n{html_content[:8000]}\n\n"
                "CRITICAL: Look for company/startup names, URLs, and any descriptive information. "
                "Even if limited information is available, extract what you can find.\n\n"
                "Instructions:\n"
                "1. Find at least 5-10 portfolio companies/startups\n"
                "2. Extract their names and website URLs (this is REQUIRED)\n"
                "3. Try to infer or extract: industry, stage, location\n"
                "4. For contact info: Use 'careers@[company-domain]' as email, leave contact_name as 'Hiring Manager'\n"
                "5. Return ONLY valid JSON - no explanations, no markdown, just the JSON array\n\n"
                "Required JSON format (return array of 5-10 companies):\n"
                "[\n"
                "  {\n"
                "    \"name\": \"Company Name\",\n"
                "    \"website\": \"https://company.com\",\n"
                "    \"industry\": \"Software/AI/Fintech/etc\",\n"
                "    \"stage\": \"Series A\",\n"
                "    \"location\": \"San Francisco, CA\",\n"
                "    \"contact_name\": \"Hiring Manager\",\n"
                "    \"contact_email\": \"careers@company.com\",\n"
                "    \"contact_linkedin\": \"\"\n"
                "  }\n"
                "]\n\n"
                "IMPORTANT: Return valid JSON only. Start with [ and end with ]."
            )
            
            response = openai.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better extraction
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Return only valid JSON arrays with no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            print(f"OpenAI Response: {content[:500]}...")  # Debug print
            
            # More aggressive cleaning of the response
            cleaned_content = content.strip()
            
            # Remove markdown code blocks if present
            if '```json' in cleaned_content:
                cleaned_content = cleaned_content.split('```json')[1].split('```')[0].strip()
            elif '```' in cleaned_content:
                cleaned_content = cleaned_content.split('```')[1].split('```')[0].strip()
            
            # Find the JSON array
            start_idx = cleaned_content.find('[')
            end_idx = cleaned_content.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                print("Could not find JSON array markers")
                # Try to create a manual fallback
                return self.create_fallback_startups(vc_website)
            
            json_str = cleaned_content[start_idx:end_idx+1]
            
            try:
                startups = json.loads(json_str)
                if not startups:
                    print("Empty startups array returned")
                    return self.create_fallback_startups(vc_website)
                print(f"Successfully parsed {len(startups)} startups")
                return startups
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Attempted to parse: {json_str[:200]}...")
                return self.create_fallback_startups(vc_website)
            
        except Exception as e:
            print(f"Error scraping VC website: {str(e)}")
            return []

    def create_fallback_startups(self, vc_website: str) -> List[Dict]:
        """
        Create fallback startup data when scraping fails.
        Uses known startups from major VC firms.
        """
        # Determine which VC firm based on URL
        vc_website_lower = vc_website.lower()
        
        fallback_data = []
        
        if 'sequoia' in vc_website_lower:
            fallback_data = [
                {"name": "Stripe", "website": "https://stripe.com", "industry": "Fintech", "stage": "Late Stage", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@stripe.com", "contact_linkedin": ""},
                {"name": "DoorDash", "website": "https://doordash.com", "industry": "Food Delivery", "stage": "Public", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@doordash.com", "contact_linkedin": ""},
                {"name": "Instacart", "website": "https://instacart.com", "industry": "Grocery Delivery", "stage": "Late Stage", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@instacart.com", "contact_linkedin": ""},
                {"name": "Databricks", "website": "https://databricks.com", "industry": "Data Analytics", "stage": "Late Stage", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@databricks.com", "contact_linkedin": ""},
                {"name": "Navan", "website": "https://navan.com", "industry": "Travel Tech", "stage": "Series G", "location": "Palo Alto, CA", "contact_name": "Hiring Manager", "contact_email": "careers@navan.com", "contact_linkedin": ""},
            ]
        elif 'ycombinator' in vc_website_lower or 'yc' in vc_website_lower:
            fallback_data = [
                {"name": "Airbnb", "website": "https://airbnb.com", "industry": "Hospitality", "stage": "Public", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@airbnb.com", "contact_linkedin": ""},
                {"name": "Coinbase", "website": "https://coinbase.com", "industry": "Cryptocurrency", "stage": "Public", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@coinbase.com", "contact_linkedin": ""},
                {"name": "Reddit", "website": "https://reddit.com", "industry": "Social Media", "stage": "Public", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@reddit.com", "contact_linkedin": ""},
                {"name": "Instacart", "website": "https://instacart.com", "industry": "Grocery Delivery", "stage": "Late Stage", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@instacart.com", "contact_linkedin": ""},
                {"name": "Brex", "website": "https://brex.com", "industry": "Fintech", "stage": "Series D", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@brex.com", "contact_linkedin": ""},
            ]
        elif 'a16z' in vc_website_lower or 'andreessen' in vc_website_lower:
            fallback_data = [
                {"name": "GitHub", "website": "https://github.com", "industry": "Developer Tools", "stage": "Acquired", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@github.com", "contact_linkedin": ""},
                {"name": "Coinbase", "website": "https://coinbase.com", "industry": "Cryptocurrency", "stage": "Public", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@coinbase.com", "contact_linkedin": ""},
                {"name": "Roblox", "website": "https://roblox.com", "industry": "Gaming", "stage": "Public", "location": "San Mateo, CA", "contact_name": "Hiring Manager", "contact_email": "careers@roblox.com", "contact_linkedin": ""},
                {"name": "Instacart", "website": "https://instacart.com", "industry": "Grocery Delivery", "stage": "Late Stage", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@instacart.com", "contact_linkedin": ""},
                {"name": "Dialpad", "website": "https://dialpad.com", "industry": "Communication", "stage": "Series E", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@dialpad.com", "contact_linkedin": ""},
            ]
        else:
            # Generic tech startups
            fallback_data = [
                {"name": "Sample Startup 1", "website": "https://example1.com", "industry": "Software", "stage": "Series A", "location": "San Francisco, CA", "contact_name": "Hiring Manager", "contact_email": "careers@example1.com", "contact_linkedin": ""},
                {"name": "Sample Startup 2", "website": "https://example2.com", "industry": "AI/ML", "stage": "Seed", "location": "New York, NY", "contact_name": "Hiring Manager", "contact_email": "careers@example2.com", "contact_linkedin": ""},
                {"name": "Sample Startup 3", "website": "https://example3.com", "industry": "Fintech", "stage": "Series B", "location": "Austin, TX", "contact_name": "Hiring Manager", "contact_email": "careers@example3.com", "contact_linkedin": ""},
            ]
        
        print(f"Using fallback data with {len(fallback_data)} startups")
        return fallback_data

    def generate_cold_email(self, startup_info: Dict) -> str:
        """
        Generate a personalized cold email for a new grad position using user information.
        """
        if not all(self.user_info.values()):
            raise ValueError("Please fill in all your profile information first")

        contact_name = startup_info.get('contact_name', 'Hiring Manager')
        contact_email = startup_info.get('contact_email', '')
        contact_linkedin = startup_info.get('contact_linkedin', '')

        if contact_name.lower() != 'hiring manager':
            salutation = f"Dear {contact_name},"
        else:
            salutation = "Dear Hiring Team,"

        prompt = (
            "Write a professional cold email for a new grad entry-level position. Include these details:\n"
            f"Startup: {startup_info['name']}\n"
            f"Industry: {startup_info.get('industry', 'Tech')}\n"
            f"Location: {startup_info.get('location', 'Remote')}\n"
            f"Contact Person: {contact_name}\n"
            f"Contact Email: {contact_email}\n"
            "\n"
            "The email should be personalized and include:\n"
            "1. A brief introduction as a recent graduate\n"
            "2. Why you're interested in the startup\n"
            "3. Relevant skills and experience from your degree\n"
            "4. How you can contribute to their early-stage company\n"
            "5. A professional closing\n"
            "\n"
            "Use this information about the candidate:\n"
            f"Name: {self.user_info['name']}\n"
            f"Degree: {self.user_info['degree']}\n"
            f"Graduation Year: {self.user_info['graduation_year']}\n"
            f"Skills: {self.user_info['skills']}\n"
            f"Achievements: {self.user_info['achievements']}\n"
            f"Location: {self.user_info['location']}\n"
            "\n"
            "Make it concise but impactful (3-4 paragraphs)."
        )

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        email_content = response.choices[0].message.content
        
        email_footer = f"\n\nContact Information:\n"\
                     f"Startup: {startup_info['name']}\n"\
                     f"Website: {startup_info['website']}\n"\
                     f"Contact Person: {contact_name}\n"\
                     f"Contact Email: {contact_email}\n"\
                     f"LinkedIn: {contact_linkedin}"
        
        return salutation + "\n\n" + email_content + "\n\n" + email_footer

    def search_startups_and_generate_emails(self):
        """
        Main function to scrape startups and generate cold emails for new grad positions.
        """
        try:
            vc_website = self.url_entry.get()
            if not vc_website:
                messagebox.showerror("Error", "Please enter a VC website URL")
                return

            self.status_label.config(text="Searching startups...")
            self.window.update()

            startups = self.scrape_vc_startups(vc_website)
            if not startups:
                messagebox.showerror("Error", "No startups found. Please check the VC website URL.")
                return

            self.status_label.config(text="Generating emails...")
            self.window.update()

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Found {len(startups)} startups. Generating emails...\n\n")

            self.generated_emails = []  # Clear previous emails

            for startup in startups:
                try:
                    email = self.generate_cold_email(startup)
                    
                    # Store email data for draft creation
                    contact_email = startup.get('contact_email', '')
                    if not contact_email:
                        contact_email = f"careers@{startup.get('website', 'example.com').replace('https://', '').replace('http://', '').split('/')[0]}"
                    
                    subject = f"New Graduate Interested in {startup['name']} - {self.user_info['degree']}"
                    
                    self.generated_emails.append({
                        'startup_name': startup['name'],
                        'to_email': contact_email,
                        'subject': subject,
                        'body': email
                    })
                    
                    self.results_text.insert(tk.END, f"\nEmail for {startup['name']}:\n")
                    self.results_text.insert(tk.END, f"To: {contact_email}\n")
                    self.results_text.insert(tk.END, f"Subject: {subject}\n")
                    self.results_text.insert(tk.END, "-" * 80 + "\n")
                    self.results_text.insert(tk.END, email + "\n")
                    self.results_text.insert(tk.END, "-" * 80 + "\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"Error generating email for {startup['name']}: {str(e)}\n")

            self.status_label.config(text="Email generation complete! Now authenticate Gmail to create drafts.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Error occurred")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    agent = NewGradJobAgent()
    agent.run()