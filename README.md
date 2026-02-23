# TC1_PortAuth_api

Python scripts to fetch **Berth Plan** data via API, generate custom SOAP XML messages for **ETC** and **BP**, and securely send them to the **TC1 Port Authority**. Supports automated token management, logging, and XML transmission.

---

## Features

- Fetch berth plan data from Maersk API using OAuth 2.0 token authentication.  
- Build custom XML messages compatible with ETC and BP systems.  
- Send XML files over HTTP securely to TC1 Port Authority.  
- Automatic token expiry handling and logging.  
- Async operations for fast API calls and XML transmissions.  
- Configurable via `.env` to keep all credentials secure.

---

## Installation

1. Clone the repository:


git clone https://github.com/Iharraren-dev/TC1_PortAuth_api.git
cd TC1_PortAuth_api
Create and activate a virtual environment:

2. python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

Folder Structure
.
├── main.py                # Entry point
├── bp_handler_api.py      # BerthPlanHandler class with async API & XML handling
├── etc_db.py              # ETC database connection handler
├── xml_builder.py         # XML file generation logic
├── metrics.py             # Metrics calculation
├── requirements.txt       # Python dependencies
└── .env                   # Credentials (not committed)
