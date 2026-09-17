import logging
import json
import mysql.connector

def delete_invoice(invoice_id):
    """Delete a specific invoice and its related rows from all relevant tables."""
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

        # Assuming we want to delete based on all invoice types
        # Get the first object from the loaded elements (adjust if necessary)
        required_keys = required_elements["StandardInvoice"][0]  # You can adjust this if you have multiple types

        # Start a transaction
        connection.start_transaction()

        # Delete related rows from each table in reverse order based on InvoiceID
        for section in reversed(required_keys.keys()):
            if section == "Invoice":
                break
            delete_query = f"DELETE FROM {section} WHERE InvoiceID = %s"
            cursor.execute(delete_query, (invoice_id,))
            logging.debug(f"Deleted rows from {section} where InvoiceID={invoice_id}: {cursor.rowcount}")

        # Finally, delete the specific invoice
        cursor.execute("DELETE FROM Invoice WHERE ID = %s", (invoice_id,))
        logging.debug(f"Deleted rows from Invoice where ID={invoice_id}: {cursor.rowcount}")

        # Commit the transaction
        connection.commit()
        return {"message": "Invoice deleted successfully."}

    except mysql.connector.Error as err:
        logging.error(f"Error during deletion: {err}")
        if connection:
            connection.rollback()  # Rollback on error
        return {"error": str(err)}, 500

    finally:
        if connection is not None and connection.is_connected():
            connection.close()

def delete_all():
    """Delete all invoices and their related rows from all relevant tables."""
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

        # Assuming you want to delete based on a specific invoice type
        invoice_type = "StandardInvoice"  # Adjust as necessary
        required_keys = required_elements[invoice_type][0]  # Get the first object

        # Start a transaction
        connection.start_transaction()

        # Delete related rows from each table in reverse order
        for section in reversed(required_keys.keys()):
            delete_query = f"DELETE FROM {section}"
            cursor.execute(delete_query)
            logging.debug(f"Deleted rows from {section}: {cursor.rowcount}")

        # Finally, delete all invoices
        cursor.execute("DELETE FROM Invoice")
        logging.debug(f"Deleted rows from Invoice: {cursor.rowcount}")

        # Commit the transaction
        connection.commit()

    except mysql.connector.Error as err:
        logging.error(f"Error during deletion: {err}")
        if connection:
            connection.rollback()  # Rollback on error
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

