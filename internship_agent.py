import os
import openai
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from typing import List, Dict

class InternshipAgent:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.tracking_file = 'internship_applications.xlsx'
        self.initialize_tracking_file()
        self.setup_gui()

    def initialize_tracking_file(self):
        if not os.path.exists(self.tracking_file):
            df = pd.DataFrame(columns=['Company', 'Position', 'Location', 'Application Date', 'Status', 'Link'])
            df.to_excel(self.tracking_file, index=False)

    def search_internships(self, query: str) -> List[Dict]:
        try:
            print(f"Searching for internships with query: {query}")
            prompt = f"""Find internships matching this query: {query}
            Return a JSON array of internship opportunities with these fields:
            company, position, location, application deadline, and job posting URL.
            Only include positions that are currently accepting applications.
            Format the response as a JSON array with proper escaping.
            Example: [{"company": "Example Corp", "position": "Software Engineer Intern", "location": "New York", "deadline": "2025-07-31", "url": "https://example.com/internship"}]"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response and extract internship opportunities
            content = response.choices[0].message.content
            print(f"Received response: {content}")
            
            # Try to parse JSON directly
            try:
                opportunities = eval(content)
                print(f"Successfully parsed {len(opportunities)} opportunities")
                return opportunities
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                print("Attempting to clean response...")
                
                # Clean the response by removing any extra text
                clean_content = content.strip()
                if clean_content.startswith('[') and clean_content.endswith(']'):
                    try:
                        opportunities = eval(clean_content)
                        print(f"Successfully parsed {len(opportunities)} opportunities after cleaning")
                        return opportunities
                    except Exception as e:
                        print(f"Error parsing cleaned response: {str(e)}")
                        print(f"Raw response: {content}")
                        return []
                else:
                    print("Response does not appear to be valid JSON")
                    print(f"Raw response: {content}")
                    return []
        except Exception as e:
            print(f"Error searching internships: {str(e)}")
            return []

    def add_to_tracking(self, internship: Dict):
        df = pd.read_excel(self.tracking_file)
        new_row = {
            'Company': internship['company'],
            'Position': internship['position'],
            'Location': internship['location'],
            'Application Date': datetime.now().strftime('%Y-%m-%d'),
            'Status': 'Not Applied',
            'Link': internship['url']
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(self.tracking_file, index=False)

    def setup_gui(self):
        self.window = tk.Tk()
        self.window.title("Internship Application Tracker")
        self.window.geometry("800x600")

        # Search Frame
        search_frame = ttk.LabelFrame(self.window, text="Search Internships")
        search_frame.pack(padx=10, pady=10, fill="x")

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(padx=5, pady=5, fill="x")

        search_btn = ttk.Button(search_frame, text="Search", command=self.search_and_display)
        search_btn.pack(pady=5)

        # Results Frame
        self.results_frame = ttk.Frame(self.window)
        self.results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Treeview for displaying results
        columns = ('Company', 'Position', 'Location', 'Deadline', 'URL')
        self.tree = ttk.Treeview(self.results_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)

        # Add to Tracking Button
        self.add_btn = ttk.Button(self.window, text="Add Selected to Tracking", command=self.add_selected_to_tracking)
        self.add_btn.pack(pady=5)

        # View Tracking Button
        view_tracking_btn = ttk.Button(self.window, text="View Tracking Spreadsheet", command=self.view_tracking)
        view_tracking_btn.pack(pady=5)

    def search_and_display(self):
        query = self.search_entry.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return

        self.tree.delete(*self.tree.get_children())
        opportunities = self.search_internships(query)
        
        for opp in opportunities:
            self.tree.insert('', 'end', values=(
                opp['company'],
                opp['position'],
                opp['location'],
                opp.get('deadline', 'N/A'),
                opp['url']
            ))

    def add_selected_to_tracking(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an internship to add")
            return

        item = self.tree.item(selected_item)
        values = item['values']
        internship = {
            'company': values[0],
            'position': values[1],
            'location': values[2],
            'url': values[4]
        }
        self.add_to_tracking(internship)
        messagebox.showinfo("Success", "Internship added to tracking spreadsheet")

    def view_tracking(self):
        try:
            os.startfile(self.tracking_file)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open tracking file: {str(e)}")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    agent = InternshipAgent()
    agent.run()
