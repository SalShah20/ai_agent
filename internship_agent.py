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
            response = requests.get(vc_website, timeout=10)
            response.raise_for_status()
            
            # Get the content of the page
            html_content = response.text
            
            # Use OpenAI to extract startup information
            prompt = (
                "Analyze this VC website content and extract startup information:\n\n"
                f"{html_content[:5000]}...\n\n"
                "Extract startups that might be interested in entry-level positions for new graduates. "
                "Focus on startups that are actively hiring and have a strong engineering or technical focus. "
                "For each startup, return a JSON object with:\n"
                "- name: Startup name\n"
                "- website: Startup's website URL\n"
                "- industry: Startup's industry focus\n"
                "- stage: Startup's current stage (e.g., seed, series A, etc.)\n"
                "- location: Startup's location\n"
                "- contact_name: Name of the Head of Engineering/CTO/CEO\n"
                "- contact_email: Email address if available\n"
                "- contact_linkedin: LinkedIn profile URL if available\n"
                "Return as a JSON array of these objects. Format the response exactly like this:\n"
                "[\n"
                "    {\n"
                "        \"name\": \"Startup Name\",\n"
                "        \"website\": \"https://startup.com\",\n"
                "        \"industry\": \"Tech\",\n"
                "        \"stage\": \"seed\",\n"
                "        \"location\": \"San Francisco\",\n"
                "        \"contact_name\": \"John Doe\",\n"
                "        \"contact_email\": \"john.doe@startup.com\",\n"
                "        \"contact_linkedin\": \"https://linkedin.com/in/johndoe\"\n"
                "    }\n"
                "]\n"
            )
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            print(f"Received response: {content}")
            
            # Clean the response by removing any extra text
            cleaned_content = content.strip()
            if not cleaned_content.startswith('['):
                cleaned_content = '[' + cleaned_content
            if not cleaned_content.endswith(']'):
                cleaned_content = cleaned_content + ']'
            
            try:
                startups = json.loads(cleaned_content)
                print(f"Successfully parsed {len(startups)} startups")
                return startups
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {str(e)}")
                print("Trying to clean the response...")
                
                start_idx = cleaned_content.find('[')
                end_idx = cleaned_content.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    json_array = cleaned_content[start_idx:end_idx+1]
                    try:
                        startups = json.loads(json_array)
                        print(f"Successfully parsed {len(startups)} startups after cleaning")
                        return startups
                    except json.JSONDecodeError as e:
                        print(f"Second JSON parsing attempt failed: {str(e)}")
                        return []
                else:
                    print("Could not find JSON array in response")
                    return []
            
        except Exception as e:
            print(f"Error scraping VC website: {str(e)}")
            return []

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