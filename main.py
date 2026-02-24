from datetime import datetime, timedelta
import os
import traceback, sys
import asyncio

import xml.etree.ElementTree as ET
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | Line:%(lineno)d | %(message)s'
)
local_logger = logging.getLogger(__name__)


local_logger.debug(f"Starting EtcHandler, BerthPlanHandler.")
# Suppress httpx and httpcore debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from etc_handler_api import EtcHandler
from bp_handler_api import BerthPlanHandler

        
etc_handler = EtcHandler()
bp_handler = BerthPlanHandler()

async def delete_old_xml_files(directory, days=31):
    try:
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        for filename in os.listdir(directory):
            if filename.lower().endswith(".xml"):
                file_path = os.path.join(directory, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff:
                    os.remove(file_path)
                    local_logger.info(f"Deleted old XML file: {file_path}")

    except Exception as e:
        local_logger.error(f"Error deleting old XML files: {str(traceback.format_exc())}")


async def main():
    try:
        # Fetch XML data from etc_handler
        etc_content = await etc_handler.get_etc_xml()
        etc_soap_data =f'''
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:tmsa="http://ADEVEAI/TMSA_BERTHPLAN.pub">
            <soapenv:Header/>
            <soapenv:Body>
                <tmsa:processETC>
                    <ETC>
                        {etc_content}
                    </ETC>
                </tmsa:processETC>
            </soapenv:Body>
        </soapenv:Envelope>
        '''
        
        # send etc xml file
        await etc_handler.send_xml(etc_soap_data)

        xml_directory = f"{os.getcwd()}/SOAP_Archive"
        os.makedirs(xml_directory, exist_ok=True)

        # Save XML locally
        timestamp = datetime.now().strftime("%Y%m%d_%H:%M:%S")
        filename = f"{xml_directory}/APMT_ETC_{timestamp}.xml"
        with open(filename, mode='w') as xml_file:
            xml_file.write(etc_soap_data)

        local_logger.info(f"ETC XML saved locally as {filename}")

        # Delete XML files older than one month (31 days)
        await delete_old_xml_files(xml_directory, days=30)
        final_bp_xml = await bp_handler.metrics_handler()
        await bp_handler.send_xml(final_bp_xml)
    except Exception as e:
        local_logger.error(f"Error saving XML data: {str(traceback.format_exc())}")
        


if __name__ == '__main__':

    asyncio.run(main())
