import asyncio
import aiohttp
from jobspy import scrape_jobs
from config import (
    GREENHOUSE_BOARDS, LEVER_BOARDS, SMARTRECRUITERS_BOARDS,
    WORKDAY_BOARDS, ORC_BOARDS,
    TARGET_KEYWORDS, EXCLUDE_KEYWORDS, TARGET_LOCATIONS
)

def matches_criteria(title: str, location: str) -> bool:
    t, l = title.lower(), location.lower()
    has_keyword = any(k in t for k in TARGET_KEYWORDS)
    has_exclusion = any(ex in t for ex in EXCLUDE_KEYWORDS)
    has_location = any(loc in l for loc in TARGET_LOCATIONS) or not l
    return has_keyword and not has_exclusion and has_location

async def fetch_greenhouse(session):
    results = []
    for company in GREENHOUSE_BOARDS:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                for job in data.get("jobs", []):
                    title = job.get("title", "")
                    loc = job.get("location", {}).get("name", "")
                    if matches_criteria(title, loc):
                        results.append({
                            "id": f"gh_{company}_{job['id']}",
                            "company": company.upper(),
                            "title": title,
                            "location": loc,
                            "url": job.get("absolute_url", ""),
                            "source": "Greenhouse Career Portal (Direct)"
                        })
        except Exception:
            pass
    return results

async def fetch_lever(session):
    results = []
    for company in LEVER_BOARDS:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                for job in data:
                    title = job.get("text", "")
                    loc = job.get("categories", {}).get("location", "")
                    if matches_criteria(title, loc):
                        results.append({
                            "id": f"lever_{company}_{job.get('id')}",
                            "company": company.upper(),
                            "title": title,
                            "location": loc,
                            "url": job.get("hostedUrl", ""),
                            "source": "Lever Career Portal (Direct)"
                        })
        except Exception:
            pass
    return results

async def fetch_smartrecruiters(session):
    # Polls SmartRecruiters public career portal APIs directly
    results = []
    for company in SMARTRECRUITERS_BOARDS:
        url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings?q=Oracle"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                for job in data.get("content", []):
                    title = job.get("name", "")
                    city = job.get("location", {}).get("city", "")
                    country = job.get("location", {}).get("country", "")
                    loc = f"{city} {country}".strip()
                    job_id = job.get("id", "")
                    if matches_criteria(title, loc):
                        results.append({
                            "id": f"sr_{company}_{job_id}",
                            "company": company.upper(),
                            "title": title,
                            "location": loc,
                            "url": f"https://jobs.smartrecruiters.com/{company}/{job_id}",
                            "source": "SmartRecruiters Career Portal (Direct)"
                        })
        except Exception:
            pass
    return results

async def fetch_workday(session):
    # Polls Workday public CXS career endpoints directly (no browser needed)
    results = []
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "Oracle HCM"}
    
    for board in WORKDAY_BOARDS:
        url = f"https://{board['host']}/wday/cxs/{board['tenant']}/{board['site']}/jobs"
        try:
            async with session.post(url, json=payload, headers=headers, timeout=12) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                for job in data.get("jobPostings", []):
                    title = job.get("title", "")
                    loc = job.get("locationsText", "")
                    ext_path = job.get("externalPath", "")
                    if matches_criteria(title, loc) and ext_path:
                        job_url = f"https://{board['host']}/{board['site']}{ext_path}"
                        results.append({
                            "id": f"wd_{board['name']}_{abs(hash(ext_path))}",
                            "company": board["name"],
                            "title": title,
                            "location": loc,
                            "url": job_url,
                            "source": "Workday Career Portal (Direct)"
                        })
        except Exception:
            pass
    return results

async def fetch_orc(session):
    results = []
    for board in ORC_BOARDS:
        url = (
            f"https://{board['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
            f"?onlyData=true&expand=requisitionList.secondaryLocations"
            f"&finder=findReqs;siteNumber={board['site']},limit=25,offset=0,sortBy=POSTING_DATES_DESC"
        )
        try:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                items = data.get("items", [])
                if not items:
                    continue
                for job in items[0].get("requisitionList", []):
                    title = job.get("Title", "")
                    loc = f"{job.get('PrimaryLocation', '')} {job.get('PrimaryLocationCountry', '')}"
                    req_id = job.get("Id", "")
                    if matches_criteria(title, loc):
                        job_url = f"https://{board['host']}/hcmUI/CandidateExperience/en/sites/{board['site']}/job/{req_id}"
                        results.append({
                            "id": f"orc_{board['name']}_{req_id}",
                            "company": board["name"],
                            "title": title,
                            "location": loc.strip(),
                            "url": job_url,
                            "source": "Oracle Career Portal (Direct)"
                        })
        except Exception:
            pass
    return results

async def poll_all_ats():
    async with aiohttp.ClientSession() as session:
        gh, lev, sr, wd, orc = await asyncio.gather(
            fetch_greenhouse(session),
            fetch_lever(session),
            fetch_smartrecruiters(session),
            fetch_workday(session),
            fetch_orc(session)
        )
        return gh + lev + sr + wd + orc

def _scrape_portals_sync():
    # Sweeps Naukri, LinkedIn & Indeed across both Pune and All-India
    portal_results = []
    for search_loc in ["Pune", "India"]:
        try:
            df = scrape_jobs(
                site_name=["naukri", "linkedin", "indeed"],
                search_term="Oracle HCM Functional Consultant",
                location=search_loc,
                results_wanted=15,
                hours_old=24,
                country_indeed="India"
            )
            for _, row in df.iterrows():
                title = str(row.get("title", ""))
                loc = str(row.get("location", ""))
                company = str(row.get("company", "Unknown")).upper()
                job_url = str(row.get("job_url", ""))
                site = str(row.get("site", "Portal")).upper()
                
                if matches_criteria(title, loc) and job_url and job_url != "nan":
                    portal_results.append({
                        "id": f"portal_{site}_{abs(hash(job_url))}",
                        "company": company,
                        "title": title,
                        "location": loc,
                        "url": job_url,
                        "source": f"{site} Job Portal"
                    })
        except Exception as e:
            print(f"Portal sweep ({search_loc}) warning: {e}")
    return portal_results

async def poll_portals():
    return await asyncio.to_thread(_scrape_portals_sync)