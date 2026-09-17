import logging
import os
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

def json_to_database(data):
    """Insert invoice data into MySQL database."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host='ktuzatca-mysql-1',  # Adjust as necessary
            user='root',
            password='TheRoot@Pass',
            database='keytouse_zatca'
        )
        cursor = connection.cursor()

        # Load required elements from external JSON file
        with open('required_invoice_elements.json', 'r') as req_file:
            required_elements = json.load(req_file)

        invoice_type = data["Config"][0]["InvoiceType"]

        if invoice_type not in required_elements:
            return {"error": f"LOC-IIDB#11: Invalid invoice type: {invoice_type}"}

        required_keys = required_elements[invoice_type][0]

        # Extract Invoice ID from the data
        invoice_id = data["Invoice"][0]["ID"]

        # Set CreatedAt to current date and time
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"LOC-IIDB#22:The invoice {invoice_id} of type {invoice_type} CreatedAt {created_at} is being inserted into database.")

        # Insert Data for Each Section Dynamically
        for section, keys in required_keys.items():
            if section in data:
                for item in data[section]:
                    # Prepare values directly from item, assuming ID and CreatedAt are included in keys
                    if section == "Invoice":
                        values = tuple(item.get(key) for key in keys)
                    else:
                        values = tuple(item.get(key) for key in keys)

                    columns = ', '.join(keys)  # Join keys to form column names
                    placeholders = ', '.join(['%s'] * len(keys))  # Create placeholders for values

                    sql_insert = f"INSERT INTO {section} ({columns}) VALUES ({placeholders})"

                    # Validate only required fields before executing
                    missing_keys = [key for key in keys if key not in item]
                    if missing_keys:
                        err_msg = f"LOC-IIDB#33: Missing required values for section '{section}': {missing_keys}"
                        logging.error(err_msg)
                        return {"error": err_msg}

                    try:
                        logging.info(f"LOC-IIDB#44: Executing SQL: {sql_insert} with values: {values}")
                        cursor.execute(sql_insert, values)
                    except mysql.connector.Error as err:
                        logging.error(f"LOC-IIDB#55: Database error occurred: {str(err)}. Query: {sql_insert}")
                        return {
                            "error": f"LOC-IIDB#66: Database error: {str(err)}",
                            "query": sql_insert,
                            "values": values
                        }

        connection.commit()  # Commit changes to the database
        return {"status": "success", "message": "Data inserted successfully"}

    except mysql.connector.Error as err:
        logging.error(f"LOC-IIDB#77: Connection error: {str(err)}")
        return {"error": f"LOC-IIDB#88: Connection error: {str(err)}"}

    except Exception as e:
        logging.error(f"LOC-IIDB#92: Unexpected error: {str(e)}")
        return {"error": f"LOC-IIDB# 94: Unexpected error: {str(e)}"}

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
