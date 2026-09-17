import xml.etree.ElementTree as ET
import logging
import os
import subprocess
from flask import Flask, request, jsonify
import re

# Set up logging
logging.basicConfig(level=logging.INFO)

def XmlCheckWithoutX10(xml_invoice):
    logging.info("LOC#49: Escape characters are removed from XML invoice")
    cleaned_xml_invoice = xml_invoice.replace('\\\"', '"')
    cleaned_xml_invoice = cleaned_xml_invoice.replace('\n', '').strip()
    logging.info(f"LOC-XTS#45: Cleaned xml file: {cleaned_xml_invoice}")

    logging.info("LOC#31: XML invoice is about to go through local validation.")

    try:
        # Validate XML syntax
        root = ET.fromstring(cleaned_xml_invoice)
        logging.info("LOC#40: General XML syntax is valid.")

        # Save XML before validation
        logging.info("LOC#43: Save xml invoice on disk.")
        result = save_b4_validation(cleaned_xml_invoice, "/app/invoice.xml") 
        if not result:
            err_msg = "XML invoice could not be saved on disk."
            logging.error(err_msg)
            return {"status": "error", "message": err_msg}, 400

        logging.info("LOC#46: Now validating invoice")

        # Run the Fatoora command
        validation_result = run_fatoora_command()

        if not validation_result['success']:
            err_msg = f"XML invoice could not be validated: {validation_result['message']}"
            logging.error(err_msg)
            return {"status": "error", "message": err_msg}, 400
        else:
            logging.info(f"Invoice validated successfully")
            return {
                "status": "OK",
                "message": "Invoice validated successfully.",
                "details": validation_result['details']
            }, 200

    except ET.ParseError as e:
        logging.error(f"LOC-XTS #24: XML syntax error: {str(e)}")
        return {"status": "error", "message": f"XML syntax error: {str(e)}"}, 400
    except Exception as e:
        err_msg = f"LOC-XTS#26: Unexpected error during XML validation: {str(e)}"
        logging.error(err_msg)
        return {"status": "error", "message": err_msg}, 500

def save_b4_validation(xml_invoice, file_path):
    if not file_path:
        file_path = "/app/invoice.xml"

    logging.info("Remove BOM if present and trim leading/trailing whitespace")
    if xml_invoice.startswith('\ufeff'):
        xml_invoice = xml_invoice[1:]  # Remove BOM

    xml_invoice = xml_invoice.strip()  # Remove leading/trailing whitespace

    # Remove invalid XML characters (e.g., control characters)
    xml_invoice = re.sub(r'[\x00-\x1F\x7F]', '', xml_invoice)  # Remove control characters

    try:
        with open(file_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_invoice)
            logging.info(f"LOC-XTS#27: XML Invoice saved to {file_path}")
            return True
    except Exception as e:
        logging.error(f"LOC-XTS#28: Failed to save XML Invoice to {file_path}: {e}")
        return False

def parse_fatoora_output(output):
    logging.info("CHKOUT#10: Parse the output from the fatoora command to determine success or failure.")
    # Define the required validation results
    required_results = [
        "[XSD] validation result : PASSED",
        "[EN] validation result : PASSED",
        "[KSA] validation result : PASSED",
        "[PIH] validation result : PASSED",
        "GLOBAL VALIDATION RESULT = PASSED"
    ]

    # Check for the presence of each required result
    for result in required_results:
        if result not in output:
            logging.info(f"CHKOUT#11: Missing required output: {result}")
            return False, f"Validation failed: missing required output: {result}"

    # If all required results are present, check for any failed validation
    if "validation result : FAILED" in output:
        logging.info(f"CHKOUT#12: Found failed output {output}")
        return False, "Validation failed: errors found."

    logging.info("CHKOUT#13: All required validations passed.")
    return True, "Invoice validated successfully."


def run_fatoora_command():
    logging.info("RUNFC#002: Construct the command to run the Fatoora tool")

    command = 'fatoora -validate -invoice /app/invoice.xml'
    env = os.environ.copy()  # Copy the current environment variables

    try:
        logging.info(f"RUNFC#005: Now execute the command and capture output")

        # Run the command with shell=True
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, env=env)

        logging.info("RUNFC#009: Parse execution output")
        
        # Check if the command was successful and log accordingly
        if result.returncode == 0:
            logging.info(f"STDOUT: {result.stdout.strip()}")
            is_success, message = parse_fatoora_output(result.stdout)

            if is_success:
                logging.info("RUNFC#012: Fatoora commandline validation successful.")
                return {
                    'success': True,
                    'message': message,
                    'details': result.stdout.strip()  # Capture standard output
                }
            else:
                logging.error("RUNFC#016: Fatoora commandline validation failed.")
                return {
                    'success': False,
                    'message': message,
                    'details': result.stderr.strip()  # Capture error output
                }
        else:
            # Log STDERR only if there was an error
            logging.error(f"STDERR: {result.stderr.strip()}")
            return {
                'success': False,
                'message': "Command failed without a valid return code.",
                'details': result.stderr.strip() if result.stderr else "No error output available."
            }

    except subprocess.CalledProcessError as e:
        logging.error(f"RUNFC#099: Error running Fatoora command: {e}")
        logging.error(f"Command: {command}")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"STDOUT: {e.stdout.strip()}")
        logging.error(f"STDERR: {e.stderr.strip()}")
        return {
            'success': False,
            'message': f"Command failed with return code {e.returncode}. Please check the command and try again.",
            'details': e.stderr.strip() if e.stderr else "No error output available."
        }
    except Exception as e:
        logging.error(f"RUNFC#099: Unexpected error running Fatoora command: {e}")
        return {
            'success': False,
            'message': "An unexpected error occurred. Please try again.",
            'details': str(e)
        }
        
