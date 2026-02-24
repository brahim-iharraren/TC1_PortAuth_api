import os
import sys
import json
import asyncio
import traceback
from datetime import datetime, timedelta
import logging
import httpx
from dotenv import load_dotenv

from metrics import BerthMetricCalculator
from xml_builder import xml_file_builder
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | Line:%(lineno)d | %(message)s'
)
local_logger = logging.getLogger(__name__)
load_dotenv()


class BerthPlanHandler:
    def __init__(self):
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.SCOPE = os.getenv("SCOPE")
        self.CONSUMER_KEY = os.getenv("CONSUMER_KEY")
        self.BP_XML_USER = os.getenv("BP_XML_USER")
        self.BP_XML_PASSWORD = os.getenv("BP_XML_PASSWORD")
        self.TOKEN_URL = os.getenv("TOKEN_URL")
        self.BP_TOKEN_EXP_DATA = os.getenv("BP_TOKEN_EXP_DATA")
        self.BP_URL = os.getenv("BP_URL")
        self.BP_XML_SEND_URL = os.getenv("BP_XML_SEND_URL")

        required_vars = {
            "CLIENT_ID": self.CLIENT_ID,
            "CLIENT_SECRET": self.CLIENT_SECRET,
            "SCOPE": self.SCOPE,
            "CONSUMER_KEY": self.CONSUMER_KEY,
            "BP_XML_USER": self.BP_XML_USER,
            "BP_XML_PASSWORD": self.BP_XML_PASSWORD,
            "TOKEN_URL": self.TOKEN_URL,
            "BP_TOKEN_EXP_DATA": self.BP_TOKEN_EXP_DATA,
            "BP_URL": self.BP_URL,
            "BP_XML_SEND_URL": self.BP_XML_SEND_URL
        }

        for key, value in required_vars.items():
            if value is None:
                raise ValueError(f"Missing required environment variable: {key}")

        self.current_date = datetime.now()
        self.expiration_date = datetime.strptime(self.BP_TOKEN_EXP_DATA, "%Y-%m-%d")
        self.TOKEN_REMAINING_DAYS = (self.expiration_date - self.current_date).days
        self.TOKEN_MSG = f"Time Left Until Expiry: {self.TOKEN_REMAINING_DAYS} days"

        self.start_date = (self.current_date - timedelta(days=8)).strftime("%Y-%m-%d")
        self.end_date = (self.current_date + timedelta(days=40)).strftime("%Y-%m-%d")
        self.params = {'terminal': 'MAPTMTM', 'fromDate': self.start_date, 'toDate': self.end_date}

        self.BP_DATA = []
        self.metrics = BerthMetricCalculator()


    async def berthPlan_api_proxy(self):
        local_logger.info(f"Berth Plan api params: {self.params}")
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'scope': self.SCOPE
        }

        self.BP_DATA = []

        try:
            async with httpx.AsyncClient(verify=False) as client:
                # -----------check token---------------------
                token_response = await client.post(self.TOKEN_URL, data=data)
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    token = token_data.get('access_token')

                    # -----------getting berth data---------------------
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Consumer-Key": self.CONSUMER_KEY
                    }

                    async with httpx.AsyncClient(verify=False) as client:
                        data_response = await client.get(self.BP_URL, params=self.params, headers=headers)

                        if data_response.status_code == 200:
                            self.BP_DATA = data_response.json()

                            with open("BerthPlan_data.json", "w") as file:
                                json.dump(self.BP_DATA, file, indent=4)

                            res_msg = {
                                "status": "success",
                                "status_code": data_response.status_code,
                                "message": "OK",
                                "token_left_time": self.TOKEN_MSG
                            }
                            local_logger.info(f"Response info: {json.dumps(res_msg, indent=4)}")
                            return res_msg
                        else:
                            res_msg = {
                                "status": "failed",
                                "status_code": data_response.status_code,
                                "message": f"token_response:\n{token_response.text} \ndata_response:\n{data_response.text}",
                                "token_left_time": self.TOKEN_MSG
                            }
                            local_logger.critical(f"Request failed with status code: {data_response.status_code}")
                            local_logger.debug(f"Response content: {json.dumps(res_msg, indent=4)}")
                            return res_msg

                else:
                    res_msg = {
                        "status": "error",
                        "status_code": token_response.status_code,
                        "message": f"token_response:\n{token_response.text}",
                        "token_left_time": self.TOKEN_MSG
                    }
                    local_logger.error(f'Request failed:{json.dumps(res_msg, indent=4)}')
                    return res_msg

        except Exception as e:
            err = traceback.format_exc()
            res_msg = {"status": "error", "status_code": 500, "message": str(err), "token_left_time": self.TOKEN_MSG}
            local_logger.error(json.dumps(res_msg, indent=4))
            return res_msg

    async def send_xml(self, xml_str: str) -> bool:
        if xml_str is None:
            raise ValueError("send_xml() error: 'xml_str' cannot be None. Please provide valid XML data before sending.")
        auth = (self.BP_XML_USER, self.BP_XML_PASSWORD)
        headers = {'Content-Type': 'text/xml'}

        try:
            date_format = "%Y-%m-%d"
            start = datetime.strptime(self.start_date, date_format)
            end = datetime.strptime(self.end_date, date_format)
            diff_days = (end - start).days

            local_logger.debug(f"Preparing to send BerthPlan XML data for {diff_days} day(s): {self.start_date} → {self.end_date}")

            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.post(
                    self.BP_XML_SEND_URL,
                    content=xml_str,
                    auth=auth,
                    headers=headers
                )

                response.raise_for_status()

                msg = {
                    "message": f"BerthPlan XML data successfully sent to {self.BP_XML_SEND_URL}",
                    "info": f"Sent BerthPlan data for {diff_days} day(s), from {self.start_date} to {self.end_date}",
                    "date_range": f"{self.start_date} to {self.end_date}",
                    "response_status": f"{response.status_code} OK"
                }
                local_logger.info(f"\n{json.dumps(msg, indent=4)}")
                return True

        except httpx.HTTPStatusError as e:
            local_logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException as e:
            local_logger.error(f"Request timed out after 10 seconds: {e}")
        except httpx.RequestError as e:
            local_logger.error(f"Request error: {e}")
        except IOError as e:
            local_logger.error(f"I/O error while handling file or response: {e}")
        except Exception as e:
            local_logger.exception(f"Unexpected error occurred: {e}")

        return False

    async def metrics_handler(self):
        try:
            await self.berthPlan_api_proxy()

            final_xml = await xml_file_builder(self.metrics, self.BP_DATA, self.start_date, self.end_date, local_logger)

            with open("xml_file.xml", "w") as f:
                f.write(final_xml)
            return final_xml
        except Exception as e:
            local_logger.error(f"Error generating XML data: {str(traceback.format_exc())}")
            return None


if __name__ == "__main__":
    handler = BerthPlanHandler()
    asyncio.run(handler.metrics_handler())