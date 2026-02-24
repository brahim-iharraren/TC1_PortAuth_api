TC1 Port Authority API Integration

Python-based service to retrieve Berth Plan (BP) data from the Maersk API and query necessary data from sparcsN4 database, generate structured SOAP XML messages for ETC and BP systems, and securely transmit them to the TC1 Port Authority.

The project is built with asynchronous processing, automated OAuth token management, and structured logging to ensure reliability and performance in production environments.

🚀 Overview
  - This service:
  - Authenticates with the Maersk API using OAuth 2.0
  - Fetches Berth Plan data asynchronously
  - Generates custom SOAP XML messages for:
  - ETC (Estimated Time of Completion)
  - BP (Berth Plan)
  - Securely transmits XML payloads to TC1 Port Authority
  - Automatically handles token expiration and renewal
  - Logs operations for monitoring and troubleshooting
  - Uses environment-based configuration for security
    
✨ Key Features
  ✅ OAuth 2.0 token lifecycle management
  ✅ Async API requests for high performance
  ✅ Custom SOAP XML generation
  ✅ Secure HTTP XML transmission
  ✅ Metrics calculation support
  ✅ Centralized logging
  ✅ Environment-based configuration (.env)

🛠️ Installation
  1. Clone the repository:
   ```
    git clone https://github.com/brahim-iharraren/TC1_PortAuth_api.git
    cd TC1_PortAuth_api
   ```
  
  2 Create and activate a virtual environment:
    ```
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows
    pip install -r requirements.txt
    ```

Project Structure
  .
  ├── main.py                # Entry point
  ├── bp_handler_api.py      # BerthPlanHandler class with async API & XML handling
  ├── etc_db.py              # ETC database connection handler
  ├── xml_builder.py         # XML file generation logic
  ├── metrics.py             # Metrics calculation
  ├── requirements.txt       # Python dependencies
  └── .env                   # Credentials (not committed)
