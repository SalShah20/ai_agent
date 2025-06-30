import logging
import asyncio
import json
import csv
from datetime import datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

llm = ChatOpenAI(model="gpt-4")

EMAIL_TEMPLATE = """
Hi [First Name or Title + Last Name],

I'm a first-year Computer Engineering student at the University of Minnesota with a strong interest in working at innovative startups like [Company Name]. I recently came across your work through [VC Firm Name or Portfolio Page], and I'm impressed by [one-sentence personalized remark about their product/team/mission].

With hands-on experience building systems across compilers, neural networks, and IoT devices—as well as contributing to robotics teams and AR app development—I’m eager to contribute and learn from a team that’s shaping the future of tech. A few of my recent projects include:

- A Java-based PASCAL to MIPS compiler
- A hand gesture recognition system using a multi-layer neural network
- A smart temperature monitor built with Particle Photon and real-time web integration

I’ve also led student outreach programs and built a productivity AR app that won a $1K grant.

If you’re open to summer internship roles or exploratory conversations, I’d love to send along my resume and share how I might contribute. Thank you for your time, and I hope to hear from you.

Best regards,  
[Your Full Name]  
[LinkedIn or GitHub link]  
[Email address]
"""

VC_WEBSITES = [
    "https://a16z.com/portfolio/",
    "https://www.sequoiacap.com/companies/",
    "https://www.benchmark.com/portfolio/",
    "https://www.ycombinator.com/companies",
    "https://www.techstars.com/portfolio"
]

async def extract_ycombinator(page):
    await page.goto("https://www.ycombinator.com/companies")
    await page.wait_for_load_state("networkidle")
    for _ in range(3):
        await page.mouse.wheel(0, 5000)
        await asyncio.sleep(2)
    cards = await page.query_selector_all("div[class*='CompanyPreview'] a")
    results = []
    for c in cards[:3]:
        name = await c.inner_text()
        href = await c.get_attribute("href")
        results.append({
            "company_name": name.strip(),
            "company_link": f"https://www.ycombinator.com{href}",
            "vc_firm": "Y Combinator"
        })
    logging.info(f"✅ Extracted {len(results)} companies from Y Combinator")
    return results

async def extract_techstars(page):
    await page.goto("https://www.techstars.com/portfolio")
    await page.wait_for_selector(".css-1fpn9ur")
    cards = await page.query_selector_all(".css-1fpn9ur")
    results = []
    for c in cards[:3]:
        name = await c.inner_text()
        link = await c.get_attribute("href")
        if name and link:
            results.append({
                "company_name": name.strip(),
                "company_link": link,
                "vc_firm": "Techstars"
            })
    logging.info(f"✅ Extracted {len(results)} companies from Techstars")
    return results

async def extract_sequoia(page):
    await page.goto("https://www.sequoiacap.com/companies/")
    await page.wait_for_selector("a[href*='/company/']")
    cards = await page.query_selector_all("a[href*='/company/']")
    results = []
    for c in cards[:3]:
        name = await c.inner_text()
        href = await c.get_attribute("href")
        results.append({
            "company_name": name.strip(),
            "company_link": f"https://www.sequoiacap.com{href}",
            "vc_firm": "Sequoia Capital"
        })
    logging.info(f"✅ Extracted {len(results)} companies from Sequoia Capital")
    return results

async def extract_a16z(page):
    await page.goto("https://a16z.com/portfolio/")
    await page.wait_for_selector("div.portfolio-company a")
    cards = await page.query_selector_all("div.portfolio-company a")
    results = []
    for c in cards[:3]:
        name = await c.inner_text()
        href = await c.get_attribute("href")
        results.append({
            "company_name": name.strip(),
            "company_link": href,
            "vc_firm": "a16z"
        })
    logging.info(f"✅ Extracted {len(results)} companies from a16z")
    return results

async def extract_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            if "ycombinator.com" in url:
                return await extract_ycombinator(page)
            elif "techstars.com" in url:
                return await extract_techstars(page)
            elif "sequoiacap.com" in url:
                return await extract_sequoia(page)
            elif "a16z.com" in url:
                return await extract_a16z(page)
            else:
                await page.goto(url)
                title = await page.title()
                logging.info(f"Visited {url} | Title: {title}")
                return [{"vc_firm": url, "page_title": title}]
        finally:
            await browser.close()

async def run_all_scrapes():
    results = []
    for url in VC_WEBSITES:
        try:
            logging.info(f"🔍 Scraping: {url}")
            result = await asyncio.wait_for(extract_with_playwright(url), timeout=90)
            logging.info(f"✅ Done scraping {url}")
            results.extend(result)
        except asyncio.TimeoutError:
            logging.warning(f"⏰ Timed out on {url}")
            results.append({"url": url, "error": "Timeout"})
    return results

async def save_results(data):
    if data:
        csv_path = f"startup_outreach_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logging.inf