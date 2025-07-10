import os
import openai
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from typing import List, Dict
import json

class NewGradJobAgent:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.setup_gui()
        self.user_info = {
            'name': '',
            'degree': '',
            'graduation_year': '',
            'skills': '',
            'achievements': '',
            'location': ''
        }

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

        # Results Frame
        self.results_text = tk.Text(self.window, height=20, width=120)
        self.results_text.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.window, command=self.results_text.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Status Frame
        status_frame = ttk.LabelFrame(self.window, text="Status", padding="5")
        status_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack()

        # Configure grid weights
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

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
                "Return as a JSON array of these objects. Format the response exactly like this:\n"
                "[\n"
                "    {\n"
                "        \"name\": \"Startup Name\",\n"
                "        \"website\": \"https://startup.com\",\n"
                "        \"industry\": \"Tech\",\n"
                "        \"stage\": \"seed\",\n"
                "        \"location\": \"San Francisco\"\n"
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
            print(f"Received response: {content}")  # Debug print
            
            # Clean the response by removing any extra text
            cleaned_content = content.strip()
            if not cleaned_content.startswith('['):
                cleaned_content = '[' + cleaned_content
            if not cleaned_content.endswith(']'):
                cleaned_content = cleaned_content + ']'
            
            try:
                # Try to parse as JSON
                startups = json.loads(cleaned_content)
                print(f"Successfully parsed {len(startups)} startups")  # Debug print
                return startups
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {str(e)}")
                print("Trying to clean the response...")
                
                # Try to find the JSON array in the response
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

        prompt = (
            "Write a professional cold email for a new grad entry-level position. Include these details:\n"
            f"Startup: {startup_info['name']}\n"
            f"Industry: {startup_info.get('industry', 'Tech')}\n"
            f"Location: {startup_info.get('location', 'Remote')}\n"
            "\n"
            "The email should be personalized and include:\n"
            "1. A brief introduction as a recent graduate\n"
            "2. Why you're interested in the startup\n"
            "3. Relevant skills and experience from your degree\n"
            "4. How you can contribute to their early-stage company\n"
            "5. A professional closing\n"
            "\n"
            f"Use this information about the candidate:\n"
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
        
        return response.choices[0].message.content

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

            for startup in startups:
                try:
                    email = self.generate_cold_email(startup)
                    self.results_text.insert(tk.END, f"\nEmail for {startup['name']}:\n")
                    self.results_text.insert(tk.END, "-" * 80 + "\n")
                    self.results_text.insert(tk.END, email + "\n")
                    self.results_text.insert(tk.END, "-" * 80 + "\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"Error generating email for {startup['name']}: {str(e)}\n")

            self.status_label.config(text="Email generation complete!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Error occurred")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    agent = NewGradJobAgent()
    agent.run()
