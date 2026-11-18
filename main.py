import asyncio
import aiohttp
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from ats_fetchers import poll_all_ats, poll_portals
from analyzer import (
    is_new_job, save_job, get_company_trend, 
    get_market_trends_report, build_xray_links, generate_ai_pitch
)

async def send_telegram(session, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    async with session.post(url, json=payload) as resp:
        return resp.status == 200

async def listen_mobile_commands(session):
    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    while True:
        try:
            async with session.get(url, params={"offset": offset, "timeout": 20}, timeout=25) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        msg = update.get("message", {})
                        text = msg.get("text", "").strip().lower()
                        chat_id = str(msg.get("chat", {}).get("id", ""))
                        
                        if chat_id == str(TELEGRAM_CHAT_ID):
                            if text == "/trends":
                                await send_telegram(session, get_market_trends_report())
                            elif text == "/status":
                                await send_telegram(session, "✅ <b>Radar Active:</b> Polling ATS every 60s & Naukri/LinkedIn every 30m.")
        except Exception:
            await asyncio.sleep(5)

async def scan_jobs_loop(session):
    cycle = 0
    await send_telegram(session, "🚀 <b>Oracle HCM Radar Started!</b>\nSend /trends anytime for hiring stats.")
    
    while True:
        try:
            jobs = await poll_all_ats()
            
            if cycle % 30 == 0:
                print(f"[Cycle {cycle}] Running Naukri/LinkedIn/Indeed sweep...")
                portal_jobs = await poll_portals()
                jobs.extend(portal_jobs)
                
            for job in jobs:
                if is_new_job(job["id"]):
                    save_job(job)
                    trend = get_company_trend(job["company"])
                    hr_link, mgr_link = build_xray_links(job["company"])
                    pitch = generate_ai_pitch(job["company"], job["title"])
                    
                    alert = (
                        f"🚨 <b>NEW ORACLE HCM OPENING</b>\n"
                        f"📡 <b>Source:</b> {job['source']}\n\n"
                        f"🏢 <b>Company:</b> {job['company']}\n"
                        f"💼 <b>Role:</b> {job['title']}\n"
                        f"📍 <b>Location:</b> {job['location'] or 'India / Remote'}\n"
                        f"📈 <b>Trend:</b> {trend}\n\n"
                        f"👉 <a href='{job['url']}'>Apply Directly</a>\n"
                        f"🎯 <a href='{hr_link}'>Find HR / Recruiter</a> | "
                        f"👔 <a href='{mgr_link}'>Find Practice Lead</a>\n\n"
                        f"💬 <b>AI Outreach Pitch:</b>\n<code>{pitch}</code>"
                    )
                    await send_telegram(session, alert)
                    await asyncio.sleep(1)
                    
            cycle += 1
        except Exception as e:
            print(f"Scan cycle error: {e}")
            
        await asyncio.sleep(60)

async def main():
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            scan_jobs_loop(session),
            listen_mobile_commands(session)
        )

if __name__ == "__main__":
    asyncio.run(main())