import json
import sys
import pyodbc
import traceback
import asyncio
import os
from datetime import datetime
# import requests
import httpx
from dotenv import load_dotenv
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | Line:%(lineno)d | %(message)s'
)
local_logger = logging.getLogger(__name__)

load_dotenv()

class EtcHandler:
    def __init__(self):
        required_vars = [
            "DB_DATA_SOURCE",
            "DB_INITIAL_CATALOG",
            "DB_USER_ID",
            "DB_PASSWORD",
            "ETC_URI",
            "ETC_AUTH_USER",
            "ETC_AUTH_PASSWORD"
        ]

        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Missing required environment variable: {var}")
            
        self.ETC_URI = os.getenv("ETC_URI")
        self.ETC_AUTH_USER = os.getenv("ETC_AUTH_USER")
        self.ETC_AUTH_PASSWORD = os.getenv("ETC_AUTH_PASSWORD")
        self.Data_Source = os.getenv("DB_DATA_SOURCE")
        self.Initial_Catalog = os.getenv("DB_INITIAL_CATALOG")
        self.User_ID = os.getenv("DB_USER_ID")
        self.Password = os.getenv("DB_PASSWORD")
        self.port = int(os.getenv("DB_PORT", 1433))
        self.MultipleActiveResultSets = os.getenv("DB_MARS", "True").lower() == "true"

        self.cnxn = None
        self.cursor = None

    async def sqlConnection(self):
        try:
            connection_string = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.Data_Source};'
                f'DATABASE={self.Initial_Catalog};'
                f'UID={self.User_ID};'
                f'PWD={self.Password}'
            )
            self.cnxn = pyodbc.connect(connection_string)
            self.cursor = self.cnxn.cursor()
            return 1
        except Exception as e:
            local_logger.error(f"Error during connection: {str(traceback.format_exc())}")
            return 0

    async def closeSqlConnection(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.cnxn:
                self.cnxn.close()
            return 1
        except Exception as e:
            local_logger.error(f"Error closing connection: {str(traceback.format_exc())}")
            return 0

    async def read_data(self):
        try:
            if await self.sqlConnection():
                sql_query = """
                WITH cte AS (
                    SELECT a.est_move_time, b.id, lloyds_id, name
                    FROM Sparcsn4.dbo.inv_wi a
                    INNER JOIN Sparcsn4.dbo.argo_carrier_visit b ON a.carrier_locid = b.id
                    LEFT OUTER JOIN argo_visit_details c ON c.gkey = b.cvcvd_gkey
                    LEFT OUTER JOIN vsl_vessel_visit_details d ON d.vvd_gkey = c.gkey
                    LEFT OUTER JOIN vsl_vessels e ON e.gkey = d.vessel_gkey
                    WHERE a.move_kind IN ('LOAD', 'DSCH')
                    AND a.move_stage NOT LIKE '%COMPLETE%'
                    AND b.phase = '40WORKING'
                )
                SELECT (
                    SELECT '1.0' AS msgVersion,
                        CONVERT(varchar, GETDATE(), 126) + DATENAME(tz, SYSDATETIMEOFFSET()) AS GenerationTime,
                        'APMT' AS sender,
                        'TerminalComercialOperationETC' AS msgFunction
                    FOR XML PATH('header'), TYPE
                ), (
                    SELECT RIGHT(id, LEN(id) - 3) AS voyageNumber,
                        name AS vesselName,
                        LEFT(id, 3) AS vesselCode,
                        lloyds_id AS IMO,
                        MAX(CONVERT(varchar, est_move_time, 126) + '.000' + DATENAME(tz, SYSDATETIMEOFFSET())) AS ETC
                    FROM cte
                    GROUP BY id, lloyds_id, name
                    FOR XML PATH('comercialOperation'), TYPE, ELEMENTS
                ) AS 'body/comercialOperations'
                FOR XML PATH(''), ROOT('TerminalComercialOperation');
                """

                self.cursor.execute(sql_query)
                result = self.cursor.fetchone()
                return result[0] if result else None
            else:
                local_logger.error("Failed to establish database connection")
                return None
        except Exception as e:
            local_logger.error(f"Error during data fetch: {str(traceback.format_exc())}")
            return None
        finally:
            await self.closeSqlConnection()

    async def get_etc_xml(self):
        try:
            xml_data = await self.read_data()

            if not xml_data:
                local_logger.warning("No XML data to save.")
                return None
            return xml_data
        except Exception as e:
            local_logger.error(f"Error generating XML data: {str(traceback.format_exc())}")
            return None

    async def send_xml(self, xml_str: str):
        if xml_str is None:
            raise ValueError("send_xml() error: 'xml_str' cannot be None. Please provide valid XML data before sending.")
        ETC_auth = (self.ETC_AUTH_USER, self.ETC_AUTH_PASSWORD)
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    self.ETC_URI, 
                    content=xml_str, 
                    auth=ETC_auth, 
                    headers={'Content-Type': 'text/xml'}
                )
                response.raise_for_status()
                msg = {
                    "message": f"ETC XML data successfully sent to {self.ETC_URI}",
                    "response_status": f"{response.status_code} OK"
                }
                local_logger.info(f"\n{json.dumps(msg, indent=4)}")
                local_logger.info(f"ETC XML file successfully sent to {self.ETC_URI}. Response status code: {response.status_code}")

        except httpx.HTTPStatusError as e:
            local_logger.error(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            local_logger.error(f"An error occurred while requesting: {e}")
        except IOError as e:
            local_logger.error(f"An error occurred while saving the file: {e}")
        except Exception as e:
            local_logger.error(f"An unexpected error occurred: {e}")

        return False

if __name__ == '__main__':
    db_obj = EtcHandler()
    try:
        xml_file = asyncio.run(db_obj.get_etc_xml())
        print(xml_file)
    except Exception as e:
        print(str(traceback.format_exc()))