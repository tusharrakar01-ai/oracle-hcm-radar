# 1. Telegram Keys
TELEGRAM_TOKEN = "9111685080:AAGhi5nM0ZLKfLb_dJm3dz6gyLA-B1KcJhw"
TELEGRAM_CHAT_ID = "8711850891"

# 2. Google AI Studio Key
GEMINI_API_KEY = "AQ.Ab8RN6Ir5aivJjBcoJapq-ELxoyfORUcARPsAGmyxnzA7SLapw"

# 3. Oracle HCM Keywords (Tailored for 1.8 Yrs Exp)
TARGET_KEYWORDS = [
    "oracle hcm", "fusion hcm", "core hr", "absence management",
    "hdl", "hcm data loader", "hris", "oracle functional", "oracle support"
]

# Filter out senior roles requiring 5+ years
EXCLUDE_KEYWORDS = [
    "lead", "architect", "manager", "director", "principal", "vp", "5+", "6+", "7+", "8+"
]

TARGET_LOCATIONS = ["pune", "bengaluru", "bangalore", "hyderabad", "mumbai", "remote", "india"]

# 4A. Greenhouse Career Portals (Polled every 1 Minute)
GREENHOUSE_BOARDS = [
    "jadeglobal", "mastek", "huronconsulting", "birlasoft", 
    "yashtechnologies", "zensar", "hexaware", "xoriant", "persistentsystems",
    "ltimindtree", "coforge", "happiestminds", "talentica", "pubmatic"
]

# 4B. Lever Career Portals (Polled every 1 Minute)
LEVER_BOARDS = ["cred", "zeta", "meesho"]

# 4C. SmartRecruiters Career Portals (Polled every 1 Minute)
SMARTRECRUITERS_BOARDS = [
    "BoschGroup", "Visa", "Equifax", "Square", "Sutherland", "WNSGlobalServices"
]

# 4D. Workday Direct Career Portals (Big 4, Consulting & Global GCCs)
# Format: {"name": "Company", "host": "tenant.wdX.myworkdayjobs.com", "tenant": "tenant", "site": "SiteID"}
WORKDAY_BOARDS = [
    {"name": "ACCENTURE", "host": "accenture.wd3.myworkdayjobs.com", "tenant": "accenture", "site": "AccentureCareers"},
    {"name": "PWC", "host": "pwc.wd3.myworkdayjobs.com", "tenant": "pwc", "site": "Global_Experienced_Careers"},
    {"name": "DELOITTE", "host": "deloitte.wd1.myworkdayjobs.com", "tenant": "deloitte", "site": "DeloitteCareers"},
    {"name": "MASTERCARD", "host": "mastercard.wd1.myworkdayjobs.com", "tenant": "mastercard", "site": "CorporateCareers"},
    {"name": "BARCLAYS", "host": "barclays.wd3.myworkdayjobs.com", "tenant": "barclays", "site": "External_Career_Site"},
    {"name": "NVIDIA", "host": "nvidia.wd5.myworkdayjobs.com", "tenant": "nvidia", "site": "NVIDIAExternalCareerSite"},
    {"name": "JOHN DEERE", "host": "johndeere.wd1.myworkdayjobs.com", "tenant": "johndeere", "site": "External"},
    {"name": "EATON", "host": "eaton.wd5.myworkdayjobs.com", "tenant": "eaton", "site": "EatonCareers"},
    {"name": "CITI", "host": "citi.wd5.myworkdayjobs.com", "tenant": "citi", "site": "2"}
]

# 4E. Oracle Recruiting Cloud (ORC) Direct Career Portals
ORC_BOARDS = [
    {"name": "ORACLE", "host": "eeho.fa.us2.oraclecloud.com", "site": "CX_1"}
]