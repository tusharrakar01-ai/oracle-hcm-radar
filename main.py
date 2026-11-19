import os
import time
import asyncio
import threading
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from ats_fetchers import poll_all_ats, poll_portals, poll_linkedin_posts
from analyzer import (
    is_new_job, save_job, get_company_trend, 
    build_xray_links, generate_ai_pitch, get_market_trends_report
)
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# 1. Dummy HTTP Server to satisfy Render & UptimeRobot
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Oracle HCM Radar is active 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def send_telegram_message(session, text, reply_markup=None):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    async with session.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload) as resp:
        return await resp.json()

async def poll_telegram_commands(session):
    try:
        async with session.get(f"{TELEGRAM_API_URL}/getUpdates?offset=-1") as resp:
            data = await resp.json()
            if data.get("ok") and data.get("result"):
                updates = data["result"]
                if not updates:
                    return
                update = updates[0]
                msg = update.get("message", {})
                text = msg.get("text", "").strip()
                
                if text == "/trends":
                    report = get_market_trends_report()
                    await send_telegram_message(session, report)
                elif text == "/linkedin":
                    li_url = 'https://www.linkedin.com/search/results/content/?keywords=%22Oracle%20HCM%22%20AND%20(%22Hiring%22%20OR%20%22Opening%22)&datePosted=%22past-24h%22&sortBy=%22date_posted%22'
                    msg_text = (
                        "🔍 <b>Real-Time LinkedIn Feed Sweep (Last 24h)</b>\n\n"
                        "Tap below to open your LinkedIn app directly to fresh recruiter posts sorted newest-first:\n\n"
                        f"👉 <a href='{li_url}'>Open Latest Oracle HCM Feed Posts</a>"
                    )
                    await send_telegram_message(session, msg_text)
    except Exception:
        pass

async def job_hunter_loop():
    print("🚀 Oracle HCM Radar 24/7 Cloud Bot Started...")
    
    async with aiohttp.ClientSession() as session:
        await send_telegram_message(
            session, 
            "🟢 <b>Oracle HCM Radar Updated & Deployed!</b>\n\n"
            "Now scanning Workday, Greenhouse, Lever, SmartRecruiters, ORC, Portals & LinkedIn Recruiter Posts 24/7.\n"
            "Commands: /trends | /linkedin"
        )
        
        while True:
            try:
                await poll_telegram_commands(session)
                
                # Fetch live jobs from direct ATS, portals, and LinkedIn X-Ray
                ats_jobs = await poll_all_ats()
                portal_jobs = await poll_portals()
                li_posts = await poll_linkedin_posts()
                all_jobs = ats_jobs + portal_jobs + li_posts
                
                new_jobs = [j for j in all_jobs if is_new_job(j["id"])]
                
                for job in new_jobs:
                    save_job(job)
                    
                    company = job["company"]
                    title = job["title"]
                    location = job["location"]
                    url = job["url"]
                    source = job["source"]
                    
                    trend_tag = get_company_trend(company)
                    pitch = generate_ai_pitch(company, title)
                    hr_xray, mgr_xray = build_xray_links(company)
                    
                    message = (
                        f"🎯 <b>NEW ORACLE HCM OPENING!</b> {trend_tag}\n\n"
                        f"🏢 <b>Company:</b> {company}\n"
                        f"💼 <b>Role:</b> {title}\n"
                        f"📍 <b>Location:</b> {location}\n"
                        f"🔍 <b>Source:</b> {source}\n\n"
                        f"💡 <b>Tailored Outreach Pitch:</b>\n<i>\"{pitch}\"</i>\n\n"
                        f"🔗 <a href='{url}'>Apply / View Post Directly</a>"
                    )
                    
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "🔍 Find HR (X-Ray)", "url": hr_xray},
                                {"text": "🔍 Find Manager (X-Ray)", "url": mgr_xray}
                            ]
                        ]
                    }
                    
                    await send_telegram_message(session, message, reply_markup=keyboard)
                    await asyncio.sleep(1.5)
                    
            except Exception as e:
                print(f"Loop error: {e}")
                
            await asyncio.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    asyncio.run(job_hunter_loop())