from flask import Flask, request, jsonify, Response
import json
import os
from collections import OrderedDict
import mysql.connector
import logging
import requests
from DeleteInvoice import delete_invoice, delete_all
from InsertIntoDB import json_to_database
from datetime import datetime
from xmlToSDK import XmlCheckWithoutX10
import jpype
from jpype.imports import *
import atexit

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#Function to start the JVM
def start_jvm():
    if not jpype.isJVMStarted():
        try:
            jpype.startJVM(classpath=['/app/zatcasdk/Apps/zatca-einvoicing-sdk-238-R3.3.8.jar'])
            logging.info("JVM started.")
        except Exception as e:
            logging.error(f"Failed to start JVM: {e}")

# Function to shut down the JVM
def shutdown_jvm():
    if jpype.isJVMStarted():
        try:
            jpype.shutdownJVM()
            logging.info("JVM shut down.")
        except Exception as e:
            logging.error(f"Failed to shut down JVM: {e}")

# Register shutdown_jvm to be called when the program exits
atexit.register(shutdown_jvm)

# Start JVM on first request
@app.before_first_request
def before_first_request():
    start_jvm()


class InitConfigInfo:
    def __init__(self):
        self.config_data = {}

    def load_config(self):
        config_file_path = os.path.join(os.path.dirname(__file__), 'init_config.json')
        # logging.basicConfig(level=logging.INFO)
        try:
            with open(config_file_path, 'r') as config_file:
                self.config_data = json.load(config_file)
            logging.info("Configuration loaded successfully.")
        except FileNotFoundError:
            logging.error("Configuration file not found.")
        except json.JSONDecodeError:
            logging.error("Error decoding JSON from configuration file.")

    def get_flag_value(self, flag_name):
        return self.config_data.get(flag_name, None)

# Create a global instance of InitConfigInfo
init_config_info = InitConfigInfo()

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='ktuzatca-mysql-1',  # Use service name defined in docker-compose
        user='root',
        password='TheRoot@Pass',
        database='keytouse_zatca'
    )


# Function to check if invoice_data.json exists and create it if necessary
def init_invoice_data():
    invoice_data_path = os.path.join(os.path.dirname(__file__), 'invoice_data.json')
    if not os.path.exists(invoice_data_path):
        with open(invoice_data_path, 'w+') as f:
            json.dump({}, f)


@app.route("/invoiceid", methods=["GET", "POST"])
def handle_invoice_by_id():
    invoice_id = request.args.get('id')  # Get the invoice ID from query parameters
    if not invoice_id:
        return jsonify({"error": "Invoice ID is required"}), 400

    if request.method == "POST":
        data = request.json
        result = process_invoice(data)

        # Update invoice_data.json with new data
        invoice_data_path = os.path.join(os.path.dirname(__file__), 'invoice_data.json')
        try:
            with open(invoice_data_path, 'r') as json_file:
                existing_data = json.load(json_file)

            # Assuming you want to append/update data based on the invoice ID
            existing_data[invoice_id] = result  # Use the invoice ID as a key

            with open(invoice_data_path, 'w') as json_file:
                json.dump(existing_data, json_file, indent=4)

            return jsonify(result), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == "GET":
        # Fetch the specific invoice data from the JSON file
        invoice_data_path = os.path.join(os.path.dirname(__file__), 'invoice_data.json')
        try:
            with open(invoice_data_path, 'r') as json_file:
                existing_data = json.load(json_file)

            # Search for the invoice ID in the Invoice array
            invoices = existing_data.get("Invoice", [])

            for invoice in invoices:
                if invoice.get("ID") == invoice_id:
                    # Create an OrderedDict to maintain the order of keys
                    ordered_invoice = OrderedDict()
                    for key in existing_data["Invoice"][0].keys():  # Use keys from the first invoice object
                        ordered_invoice[key] = invoice[key]
                    return jsonify(ordered_invoice), 200

            return jsonify({"error": "Invoice not found"}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/hi", methods=["GET"])
def hi():
    return "Hello there!"

@app.route("/init_config", methods=["GET"])
def init_config():
    return jsonify(init_config_info.config_data)

@app.route("/get_flag", methods=["GET"])
def get_flag():
    flag_name = request.args.get('name')
    flag_value = init_config_info.get_flag_value(flag_name)

    if flag_value is not None:
        return jsonify({flag_name: flag_value}), 200
    else:
        return Response("Flag not found.", status=404)

@app.route("/cat", methods=["GET"])
def cat_file():
    filename = request.args.get('name')
    file_path = os.path.join(os.getcwd(), filename)

    if not os.path.isfile(file_path):
        return Response("File not found.", status=404)

    with open(file_path, 'r') as f:
        content = f.read()

    return Response(content, mimetype='text/plain')

@app.route('/deleteall', methods=['GET'])
def delete_all_route():
    """Route to delete all invoices and related data."""
    try:
        delete_all()  # Call the delete function
        info_msg = {"message": "All invoices and related data deleted successfully."}
        logging.info(info_msg)
        return jsonify(info_msg), 200
    except Exception as e:
        err_msg = {"error": str(e)}
        logging.error(err_msg)
        return jsonify(), 500


@app.route('/deleteinvoice', methods=['DELETE'])
def delete_invoice_route():
    """Route to delete a specific invoice by ID."""
    invoice_id = request.args.get('id')  # Get invoice ID from query parameters

    if not invoice_id:
        return jsonify({"error": "Invoice ID is required."}), 400

    result = delete_invoice(invoice_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    return jsonify(result), 200



# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[ U P L O A D ]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
@app.route('/upload', methods=['POST'])
def upload_file():
    logging.info("Upload file process started.")

    """Handle file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(os.getcwd(), file.filename)

    try:
        file.save(file_path)  # Save the uploaded file

        # Check if the uploaded file is named 'invoice.json'
        if file.filename == 'invoice.json':
            # Load and validate JSON data
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)


            # Get current date and time
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Update CreatedAt for Invoice
            data["Invoice"][0]["CreatedAt"] = current_datetime

            # Extract the Invoice ID from the Invoice section
            invoice_id = data["Invoice"][0]["ID"]

            # Update CreatedAt and InvoiceID for other sections
            for section in data:
                if section != "Config":
                    for item in data[section]:
                        item["CreatedAt"] = current_datetime
                        item["InvoiceID"] = invoice_id

            # Extract invoice ID from the loaded data
            invoice_id = data["Invoice"][0]["ID"]
            logging.info(f"Deleting previous invoice first: {invoice_id}")

            # Step 1: Delete existing invoice using the extracted ID
            delete_result = delete_invoice(invoice_id)

            if isinstance(delete_result, dict) and "error" in delete_result:
                err_msg = {"error": delete_result["error"]}
                logging.error(err_msg)
                return jsonify(err_msg), 500
            elif isinstance(delete_result, dict) and "message" in delete_result:
                logging.info(f"Invoice deleted successfully: {invoice_id}")
            else:
                logging.warning(f"Unexpected response from delete_invoice for ID {invoice_id}: {delete_result}")

            logging.info(f"Now inserting new data for the Invoice: {invoice_id}")
            # Load required elements from external JSON file
            with open('required_invoice_elements.json', 'r') as req_file:
                required_elements = json.load(req_file)

            # Get invoice type from the uploaded data
            invoice_type = data["Config"][0]["InvoiceType"]
            logging.info(f"The Invoice {invoice_id} is type of {invoice_type}")

            # Validate if invoice type exists in required elements
            if invoice_type not in required_elements:
                err_msg = f"Unknown invoice type: {invoice_type}"
                logging.error(err_msg)
                return jsonify({"REQCHK#1": err_msg}), 400
            else:
                logging.info(f"Requirement successfully loaded for type: {invoice_type}")

            required_keys = required_elements[invoice_type][0]  # Get the first object

            # Validate required parent elements based on invoice type
            for section, keys in required_keys.items():
                if section not in data:
                    err_msg = f"Missing required section: {section}"
                    logging.error(err_msg)
                    return jsonify({"error": err_msg}), 400

                for key in keys:
                    if key not in data[section][0]:  # Check first item in array for required keys
                        err_msg = f"Missing required key '{key}' in section '{section}'"
                        logging.error(err_msg)
                        return jsonify({"error": err_msg}), 400

            # Step 2: Insert data into MySQL database
            insert_result = json_to_database(data)

            if isinstance(insert_result, dict) and "error" in insert_result:
                err_msg = {"error": insert_result["error"], "query": insert_result.get("query")}
                logging.error(f"Invoice insert process failed with error: {err_msg}")
                return jsonify(err_msg), 500
            else:
                logging.info(f"Invoice inserted into database successfully. {invoice_id}")

            # Step 3: Send POST request to remote server
            logging.info("About to send invoice as JSON to ubl.keytouse.com")
            payload = [{"requesttype": "setdata", "data": json.dumps(data)}]  # Prepare payload with JSON contents
            try:
                # Retry once on transient connection errors
                for attempt in range(2):
                    try:
                        response = requests.post(
                            "https://ubl.keytouse.com/zatca",
                            json=payload,
                            timeout=30,
                        )
                        response.raise_for_status()
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == 0:
                            logging.warning(f"LOC#16: Remote call failed (attempt 1): {e}. Retrying...")
                            time.sleep(2)
                        else:
                            raise

                resp_data = response.json()

                # Check remote's own status, not just HTTP
                if resp_data.get("status") != "200":
                    err = resp_data.get("message", "Unknown remote error")
                    logging.error(f"LOC#17: Remote rejected invoice: {err}")
                    return jsonify({"error": f"Remote error: {err}"}), 400

                xml_invoice = resp_data.get("message")

                # Now response received, start Local validation
                if xml_invoice:
                    logging.info("LOC#18: Response successfully received from remote server.")

                    # Perform local checking of XML invoice before sending it to ZATCA
                    local_check_result = XmlCheckWithoutX10(xml_invoice)

                    if local_check_result[0]['status'] == 'error':
                        return jsonify(local_check_result[0]), local_check_result[1]  # Return local check errors

                    # If local check is successful, proceed with sending to ZATCA
                    # (You may want to call another function here to handle that)
                    return jsonify({"message": "XML invoice passed local checks and is ready for ZATCA."}), 200

                else:
                    logging.error("LOC#19: No XML invoice found in response.")
                    return jsonify({"error": "No XML invoice found"}), 400


            except requests.exceptions.RequestException as e:
                err_msg = {"error": f"LOC#11: Remote JSON send error {str(e)}"}
                logging.error(err_msg)
                return jsonify(err_msg), 500

            info_msg = f"LOC#14: Invoice processed successfully: {file.filename}"
            logging.info(info_msg)
            return jsonify({"message": info_msg}), 200

        else:  # it is some other file but not invoice.json
            info_msg = f"File uploaded successfully: {file.filename}. No processing done."
            logging.info(info_msg)
            return jsonify({"message": info_msg}), 200

    except Exception as e:
        err_msg = {"error": str(e)}
        logging.error(err_msg)
        return jsonify(err_msg), 500

    # Fallback return statement (optional but good practice)
    return jsonify({"message": "Upload completed."}), 200


# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[ U P L O A D ]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[    E N D    ]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]


# Initialize invoice data on startup
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    init_config_info.load_config()
    init_invoice_data()
