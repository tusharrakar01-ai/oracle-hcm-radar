import sqlite3
import urllib.parse
from datetime import datetime, timedelta
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

conn = sqlite3.connect("oracle_radar.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        company TEXT,
        title TEXT,
        location TEXT,
        url TEXT,
        source TEXT,
        first_seen TIMESTAMP
    )
""")
conn.commit()

def is_new_job(job_id: str) -> bool:
    cur.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
    return cur.fetchone() is None

def save_job(job):
    cur.execute(
        "INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job["id"], job["company"], job["title"], job["location"], job["url"], job["source"], datetime.now())
    )
    conn.commit()

def get_company_trend(company: str) -> str:
    seven_days_ago = datetime.now() - timedelta(days=7)
    cur.execute("SELECT COUNT(*) FROM jobs WHERE company = ? AND first_seen >= ?", (company, seven_days_ago))
    count = cur.fetchone()[0]
    if count >= 3:
        return f"🔥 HIRING SURGE ({count} roles in 7d)"
    return f"📊 Active ({count} roles in 7d)"

def get_market_trends_report() -> str:
    seven_days_ago = datetime.now() - timedelta(days=7)
    cur.execute("SELECT COUNT(DISTINCT company), COUNT(*) FROM jobs WHERE first_seen >= ?", (seven_days_ago,))
    total_companies, total_jobs = cur.fetchone()
    
    cur.execute("""
        SELECT company, COUNT(*) as cnt 
        FROM jobs WHERE first_seen >= ? 
        GROUP BY company ORDER BY cnt DESC LIMIT 5
    """, (seven_days_ago,))
    top_rows = cur.fetchall()
    
    if not top_rows:
        return "📊 <b>7-Day Market Trends:</b> No jobs logged yet. Keep the radar running!"
        
    leaderboard = "\n".join([f"• <b>{c}</b>: {n} openings" for c, n in top_rows])
    return (
        f"📈 <b>ORACLE HCM 7-DAY HIRING TRENDS</b>\n\n"
        f"🏢 <b>Active Hiring Companies:</b> {total_companies}\n"
        f"💼 <b>Total Matching Roles:</b> {total_jobs}\n\n"
        f"🏆 <b>Top Hiring Companies This Week:</b>\n{leaderboard}"
    )

def build_xray_links(company: str):
    hr_query = f'site:linkedin.com/in/ ("Talent Acquisition" OR "Recruiter" OR "HR") AND "{company}"'
    mgr_query = f'site:linkedin.com/in/ ("Oracle HCM" OR "Fusion HCM" OR "Practice" OR "Delivery Manager") AND "{company}"'
    return (
        f"https://www.google.com/search?q={urllib.parse.quote(hr_query)}",
        f"https://www.google.com/search?q={urllib.parse.quote(mgr_query)}"
    )

def generate_ai_pitch(company: str, title: str) -> str:
    prompt = (
        f"Write a crisp 3-line LinkedIn DM for a candidate with 1.8 years of hands-on Oracle Fusion HCM "
        f"(Core HR, Absence Management, HDL) configuration experience applying for '{title}' at '{company}'. "
        f"Confident, direct, zero fluff."
    )
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception:
        return f"Hi, I have 1.8 years of hands-on experience configuring Oracle Fusion HCM (Core HR & Absence). Would love to connect regarding the {title} role at {company}."