null = ""

from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime

ET.register_namespace('soapenv', "http://schemas.xmlsoap.org/soap/envelope/")
ET.register_namespace('tmsa', "http://ADEVEAI/TMSA_BERTHPLAN.pub")

SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"
TMSA = "http://ADEVEAI/TMSA_BERTHPLAN.pub"

# added on 05-06-2025
agency = {
    "MSK": "NOATUM (Ex MARMEDSA)",
    "HCL": "ARKAS MAROC",
    "HAP": "ARKAS MAROC",
    "MSC": "TRANSPORTS MAROCAINS",
    "CGM": "CMA CGM MAROC",
    "XCL": "BOLLORE TRANSPORT ET LOGISTICS MAROC",
    "JOEL LALAURIE": "JOEL LALAURIE",
    "HAMAG": "HAMAG",
    "UNIVERSAL SHIPPING": "UNIVERSAL SHIPPING",
    "UNION MAIRITIME ET MINIERE": "UNION MAIRITIME ET MINIERE",
    "INTERCONA": "INTERCONA",
    "GLOBE MARINE": "GLOBE MARINE",
    "GRIMALDI AGENCIES MAROC": "GRIMALDI AGENCIES MAROC",
    "AGENCE MED": "AGENCE MED",
    "GLOBAL CONTAINER AGENCY MAROC SA": "GLOBAL CONTAINER AGENCY MAROC SA",
    "FRS MAROC": "FRS MAROC",
    "SOCONAV": "SOCONAV",
    "BABMARSA Babord Maroc sarl": "BABMARSA Babord Maroc sarl",
    "MARITIME SHIP SERVICES": "MARITIME SHIP SERVICES",
    "LASRY MAROC": "LASRY MAROC",
    "SAGET MAROC": "SAGET MAROC",
    "ASAPS": "ASAPS",
    "AGECOMAR": "AGECOMAR",
    "SEATRADE": "SEATRADE",
    "SHARAF SHIPPING AGENCY": "SHARAF SHIPPING AGENCY",
    "TRASMEDITERRANEA SHIPPING MAROC": "TRASMEDITERRANEA SHIPPING MAROC",
    "TB INTERNATIONAL": "TB INTERNATIONAL",
    "INTERSHIPPING": "INTERSHIPPING",
    "PEREZ & CIA": "PEREZ & CIA",
    "GRANDI NAVI VELOCI MAROC": "GRANDI NAVI VELOCI MAROC",
    "PLANET COM TRANS": "PLANET COM TRANS",
    "OCEAN NETWORK EXPRESS (ONE)": "OCEAN NETWORK EXPRESS (ONE)"
}

def ns(tag, namespace):
    return f"{{{namespace}}}{tag}"

def format_datetime(dt_string):
    if not dt_string:
        return ""
    try:
        if 'T' in dt_string:
            if '.' in dt_string:
                dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S.%f")
            else:
                dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        # If parsing fails, return the original string
        return dt_string
 
async def xml_file_builder(metrics, berth_data_list, start_date, end_date, logger):
    global agency
    try:
        logger.info("Starting BerthPlan XML file processing...")
        # Adding root structure
        envelope = ET.Element(ns("Envelope", SOAPENV))
        header = ET.SubElement(envelope, ns("Header", SOAPENV))
        body = ET.SubElement(envelope, ns("Body", SOAPENV))
        process = ET.SubElement(body, ns("processBerthPlan", TMSA))
        request = ET.SubElement(process, "berthPlanRequest")
        demande = ET.SubElement(request, "DemandeInitiale")

        # Adding nHeader
        header_elem = ET.SubElement(demande, "header")
        ET.SubElement(header_elem, "msgVersion").text = "3.0"
        ET.SubElement(header_elem, "GenerationTime").text = datetime.utcnow().isoformat() + "Z"
        ET.SubElement(header_elem, "sender").text = "APMT"

        # Adding Body
        body_elem = ET.SubElement(demande, "body")
        ET.SubElement(body_elem, "startDate").text = format_datetime(start_date)
        ET.SubElement(body_elem, "endDate").text = format_datetime(end_date)
        berths = ET.SubElement(body_elem, "berths")

        for berth in berth_data_list:
            isStarboardBerth = True if berth.get("isStarboardBerth") == "1" else False
            planned_bollard = berth.get("plannedBollard", "")
            vessel_loa = berth.get("vesselLOA", 0.0)
            after_metric_point, forward_metric_point, is_real = metrics.get_metrics(planned_bollard, vessel_loa, isStarboardBerth)
            # Maping berthing side
            berthing_side = "StarbordSide" if isStarboardBerth else "PortSide"

            # Formating all datetime fields
            etb = format_datetime(berth.get("etb", ""))
            etd = format_datetime(berth.get("etd", ""))
            etc = format_datetime(berth.get("etc", ""))
            
            binfo = ET.SubElement(berths, "berthinformation")
            ET.SubElement(binfo, "berthPurpose").text = "DischargeLoad"
            ET.SubElement(binfo, "requestStatus").text = "Reservation"
            ET.SubElement(binfo, "voyageNumber").text = str(berth.get("arrivalVoyage", ""))
            ET.SubElement(binfo, "vesselName").text = str(berth.get("vesselName", ""))
            ET.SubElement(binfo, "vesselCode").text = str(berth.get("vesselCode", ""))
            ET.SubElement(binfo, "IMO").text = str(berth.get("imoCode", ""))
            ET.SubElement(binfo, "vesselType").text = "Container"
            ET.SubElement(binfo, "LOA").text = str(berth.get("vesselLOA", ""))
            ET.SubElement(binfo, "afterMetricPoint").text = str(after_metric_point)
            ET.SubElement(binfo, "forwardMetricPoint").text = str(forward_metric_point)
            ET.SubElement(binfo, "ETB").text = str(etb)
            ET.SubElement(binfo, "ETD").text = str(etd)
            ET.SubElement(binfo, "ETC").text = str(etc)
            ET.SubElement(binfo, "forwardDraught").text = "0"
            ET.SubElement(binfo, "afterDraught").text = "0"
            ET.SubElement(binfo, "dockName").text = "1"
            ET.SubElement(binfo, "EMP").text = str(berth.get("operatorCode", ""))
            ET.SubElement(binfo, "bowBollard").text = str(forward_metric_point)
            ET.SubElement(binfo, "berthingSide").text = str(berthing_side)
            ET.SubElement(binfo, "serviceCode").text = str(berth.get("service_Route", ""))
            ET.SubElement(binfo, "serviceName").text = str(berth.get("serviceName", ""))

            total_moves = (
                berth.get("plannedLoadMoves", 0)
                + berth.get("plannedDischargeMoves", 0)
                + berth.get("plannedShiftingMoves", 0)
            )
            ET.SubElement(binfo, "totalMoves").text = str(total_moves)
            ET.SubElement(binfo, "dischargeMoves").text = str(berth.get("plannedDischargeMoves", 0))
            ET.SubElement(binfo, "loadMoves").text = str(berth.get("plannedLoadMoves", 0))
            ET.SubElement(binfo, "restowMoves").text = str(berth.get("plannedShiftingMoves", 0))

            average_cranes = berth.get("averageCranes", 0.0)
            ET.SubElement(binfo, "numberOfCranesAvg").text = f"{average_cranes:.2f}"

            ET.SubElement(binfo, "marineAgent").text = str(agency.get(berth.get("operatorCode", "NOA"), "NOA")) #str(berth.get("operatorCode", "NOA"))

            securite = ET.SubElement(binfo, "securite")
            ET.SubElement(securite, "siCertificatISPS").text = "false"
            ET.SubElement(securite, "referenceCertificatISPS").text = "0"


        # Serializing to XML string
        buffer = BytesIO()
        tree = ET.ElementTree(envelope)
        ET.indent(tree, space="  ")
        tree.write(buffer, encoding="utf-8", xml_declaration=True)
        xml_txt = buffer.getvalue().decode("utf-8")
        logger.info("BerthPlan XML file generated successfully!")
        return xml_txt
    except Exception as e:
        logger.error(f"BerthPlan XML file generation failed! {e}")
        raise RuntimeError("An error occurred while processing.") from e
