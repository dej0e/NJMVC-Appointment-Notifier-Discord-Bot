from bs4 import BeautifulSoup
import urllib.request

APPOINTMNET_URL_PREFIX = "https://telegov.njportal.com"
APPOINTMENT_TEMPLATE_URL = "https://telegov.njportal.com/njmvc/AppointmentWizard/{type_code}/{location_code}"

TYPE_CODES = {
    "INITIAL PERMIT (NOT FOR KNOWLEDGE TEST)": 15,
    "CDL PERMIT OR ENDORSEMENT - (NOT FOR KNOWLEDGE TEST)": 14,
    "REAL ID": 12,
    "NON-DRIVER ID": 16,
    "KNOWLEDGE TESTING (NOT CDL)": 19,
    "RENEWAL: LICENSE OR NON-DRIVER ID": 11,
    "RENEWAL: CDL": 6,
    "TRANSFER FROM OUT OF STATE": 7,
    "NEW TITLE OR REGISTRATION": 8,
    "SENIOR NEW TITLE OR REGISTRATION (65+)": 9,
    "REGISTRATION RENEWAL": 10,
    "TITLE DUPLICATE/REPLACEMENT": 13,
}

MVC_LOCATION_CODES = {
    "KNOWLEDGE TESTING (NOT CDL)": {
        "BAYONNE": 268, "NEWARK": 281, "NORTH BERGEN": 282, "ELIZABETH": 290,
        "EDISON": 275, "WAYNE": 283, "PATERSON": 285, "LODI": 279,
    },
    "TRANSFER FROM OUT OF STATE": {
        "ELIZABETH": 263, "OAKLAND": 58, "PATERSON": 59, "LODI": 55,
        "WAYNE": 67, "RANDOLPH": 61, "NORTH BERGEN": 57, "NEWARK": 56,
        "BAYONNE": 47, "RAHWAY": 60, "SOUTH PLAINFIELD": 63, "EDISON": 52,
        "FLEMINGTON": 53, "BAKERS BASIN": 46, "FREEHOLD": 54, "EATONTOWN": 51,
        "TOMS RIVER": 65, "DELANCO": 50, "CAMDEN": 49, "WEST DEPTFORD": 68,
        "SALEM": 64, "VINELAND": 66, "CARDIFF": 48, "RIO GRANDE": 62,
    },
    "REAL ID": {
        "OAKLAND": 141, "PATERSON": 142, "LODI": 136, "WAYNE": 140, "RANDOLPH": 145,
        "NORTH BERGEN": 139, "NEWARK": 138, "BAYONNE": 125, "RAHWAY": 144,
        "SOUTH PLAINFIELD": 131, "EDISON": 132, "FLEMINGTON": 133, "BAKERS BASIN": 124,
        "FREEHOLD": 135, "EATONTOWN": 130, "TOMS RIVER": 134, "DELANCO": 129,
        "CAMDEN": 127, "WEST DEPTFORD": 143, "SALEM": 128, "VINELAND": 137,
        "CARDIFF": 146, "RIO GRANDE": 126,
    },
    "INITIAL PERMIT (NOT FOR KNOWLEDGE TEST)": {
        "OAKLAND": 203, "PATERSON": 204, "LODI": 198, "WAYNE": 202, "RANDOLPH": 207,
        "NORTH BERGEN": 201, "NEWARK": 200, "BAYONNE": 187, "RAHWAY": 206,
        "SOUTH PLAINFIELD": 193, "EDISON": 194, "FLEMINGTON": 195, "BAKERS BASIN": 186,
        "FREEHOLD": 197, "EATONTOWN": 192, "TOMS RIVER": 196, "DELANCO": 191,
        "CAMDEN": 189, "WEST DEPTFORD": 205, "SALEM": 190, "VINELAND": 199,
        "CARDIFF": 208, "RIO GRANDE": 188,
    }
}

def get_new_appointments(config_info, seen_urls):
    new_appointments = {}

    for (appt_type, type_code), locations in config_info.items():
        for loc_name, loc_code in locations:
            url = APPOINTMENT_TEMPLATE_URL.format(type_code=type_code, location_code=loc_code)
            try:
                with urllib.request.urlopen(url) as response:
                    html = response.read().decode()
                    soup = BeautifulSoup(html, "html.parser")
                    container = soup.find(id="timeslots")
                    if container:
                        slots = container.find_all("a", href=True)
                        for slot in slots:
                            full_url = APPOINTMNET_URL_PREFIX + slot['href']
                            if full_url not in seen_urls:
                                time_str = full_url.split("/")[-1]
                                time_fmt = (
                                    "0" + time_str[0] + ":" + time_str[1:] + "AM" if len(time_str) == 3
                                    else time_str[:2] + ":" + time_str[2:] + ("PM" if int(time_str[:2]) >= 12 else "AM")
                                )
                                new_appointments[full_url] = {
                                    "type": appt_type,
                                    "location": loc_name,
                                    "url": full_url,
                                    "date": full_url.split("/")[-2],
                                    "time": time_fmt,
                                }
            except Exception as e:
                print(f"❌ Failed to fetch from {url} — {e}")

    return new_appointments