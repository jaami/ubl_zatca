#Invoice.py
import os
import logging
import mysql.connector
from mysql.connector import Error
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta

from .AdditionalDocumentReference import XmlGen as XmlGenAdditionalDocumentReference
from .Signature import XmlGen as XmlGenSignature
from .AccountingSupplierParty import XmlGen as XmlGenAccountingSupplierParty
from .AccountingCustomerParty import XmlGen as XmlGenAccountingCustomerParty
from .AllowanceCharge import XmlGen as XmlGenAllowanceCharge
from .TaxTotal import XmlGen as XmlGenTaxTotal
from .InvoiceLine import XmlGen as XmlGenInvoiceLine

#global variables
rows = 0
InvoiceTypeCode = 0
current_time = datetime.now()
Now = current_time.strftime('%Y-%m-%d %H:%M:%S')

def execute_query(conn, cursor, query: str, theTable: str, params: list = None) -> tuple:
    global InvoiceTypeCode

    isError = False
    msg = ""

    try:
        # Execute the query
        cursor.execute(query, params or [])
        result = cursor.fetchall()

        # Use len(result) to determine row count
        rows = len(result)
        columns = [column[0] for column in cursor.description]

        theparams = ', '.join(map(str, params))
        if not rows > 0:
            print(f"[{Now}]:: Query failed. Query = {query}. Params ={theparams}" )

        # Set global InvoiceTypeCode used in remaining process
        if result and rows > 0 and theTable == "Invoice":
            InvoiceTypeCode = result[0][columns.index('InvoiceTypeCode')]

        if InvoiceTypeCode:  # Without invoice type, optional tables cannot be checked
            # Check if the table is allowed to have no rows
            cursor.execute("SELECT 1 FROM RowsNotRequired WHERE InvoiceTypeCode = %s AND TableName = %s", (InvoiceTypeCode, theTable))
            if cursor.fetchone():  # YES, it is an optional table and may be empty
                logging.info(f"YES, it is an optional table and may be empty: {theTable}")
                msg = f"select from {theTable} returned rows={rows}."
                isError = False
            else:  # Table must have at least 1 row
                if rows < 1:  # NO, table has no row
                    # Format parameters for logging
                    params_str = ', '.join(map(str, params)) if params else 'None'
                    # Construct the error message
                    msg = f"1EQ: Error: {theTable} should have at least one row. Query: {query}. Params: {params_str}"
                    logging.error(msg)
                    isError = True
                else:  # Yes, the table has at least 1 row
                    msg = f"select from {theTable} returned rows={rows}."
                    isError = False
        else:  # InvoiceTypeCode not set
            msg = f"2EQ: Error: InvoiceTypeCode value is not set in Invoice"
            isError = True

        if isError:
            return None, None, msg, isError
        else:
            return result, columns, msg, isError

    except mysql.connector.errors.Error as e:
        msg = f"3EQ: Error executing query for {theTable}: SQL Error Code: {e.args[0]}, Message: {str(e)}, Query:{query}, Params:{', '.join(map(str, params))}"
        isError = True
        return None, None, msg, isError
    finally:
        logging.info(f"Query executed for {theTable}: {msg}")

# ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
# ║║║║║║║║║║║║║║║║║║║║ M A I N  ║║║║║║║║║║║║║║║║║║║║║║║║║║
# ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
def XmlGen(conn, cursor, InvoiceID):
    print(f"[{Now}]:: ║║║║║║║║║║║║║║║  Xml generation requesr received  ║║║║║║║║║║║║║║║")
    global table_name
    global rows
    global InvoiceType
    DeliveryPartyID = ""
    InvoiceType = ""
    parameters = {} #these params are prepared to pass other .py scripts
    msg =""
    isError = False

    try:
        if conn.is_connected():
            print("Successfully connected to the database")
        else:
            isError = True
            return "Error: Invoice generation need successfull connection.", isError

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║ I N V O I C E  ║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Started from Invoice")
        invoice_query = "SELECT * FROM Invoice WHERE ID = %s"
        table_name = "Invoice"
        invoice, invoiceColumns, msg, isError = execute_query(conn, cursor, invoice_query, table_name, (InvoiceID,))

        if isError:
            return msg, isError

        ProfileID = invoice[0][invoiceColumns.index('ProfileID')]
        UUID = invoice[0][invoiceColumns.index('UUID')]
        IssueDate = invoice[0][invoiceColumns.index('IssueDate')]
        IssueTime = invoice[0][invoiceColumns.index('IssueTime')]
        InvoiceTypeCode = invoice[0][invoiceColumns.index('InvoiceTypeCode')]
        InvoiceTypeName = invoice[0][invoiceColumns.index('InvoiceTypeName')] if 'InvoiceTypeName' in invoiceColumns else '0100000'
        Note = invoice[0][invoiceColumns.index('Note')]
        DocumentCurrencyCode = invoice[0][invoiceColumns.index('DocumentCurrencyCode')]
        TaxCurrencyCode = invoice[0][invoiceColumns.index('TaxCurrencyCode')]
        CreatedAt = invoice[0][invoiceColumns.index('CreatedAt')]

        if CreatedAt is None:
            return "Error: CreatedAt timestamp is not correct in Invoice.", True

        current_time = datetime.now()
        if current_time - CreatedAt > timedelta(hours=24):
            return "Invoice data is older than 24 hours. Please delete all data and re-fill.", False

        if InvoiceTypeCode.strip() == "388": #standard
            NoteElement = ""
            DeliveryElements = """<cac:Delivery><cb<cac:AdditionalDocumentReference></cac:AdditionalDocumentReference>c:ActualDeliveryDate>{ActualDeliveryDate}</cbc:ActualDeliveryDate></cac:Delivery>"""
        if InvoiceTypeCode.strip() == "389": #simple
            NoteElement = """<cbc:Note languageID="ar">{Note}</cbc:Note>"""
            DeliveryElements = ""

        CompleteXml = '<?xml version="1.0" encoding="UTF-8"?><Invoice{CompleteElements}</Invoice>'

        NameSpaceElements = """
                xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">"""

        InvoiceElements = """<cbc:ProfileID>{ProfileID}</cbc:ProfileID>
                <cbc:ID>{InvoiceID}</cbc:ID>
                <cbc:UUID>{UUID}</cbc:UUID>
                <cbc:IssueDate>{IssueDate}</cbc:IssueDate>
                <cbc:IssueTime>{IssueTime}</cbc:IssueTime>
                <cbc:InvoiceTypeCode name="{InvoiceTypeName}">{InvoiceTypeCode}</cbc:InvoiceTypeCode>
                {NoteElement}
                <cbc:DocumentCurrencyCode>{DocumentCurrencyCode}</cbc:DocumentCurrencyCode>
                <cbc:TaxCurrencyCode>{TaxCurrencyCode}</cbc:TaxCurrencyCode>"""

        NoteElement = NoteElement.format(Note=Note)
        InvoiceElements = InvoiceElements.format(ProfileID=ProfileID, InvoiceID=InvoiceID, UUID=UUID, IssueDate=IssueDate, IssueTime=IssueTime, InvoiceTypeCode=InvoiceTypeCode, InvoiceTypeName=InvoiceTypeName, NoteElement=NoteElement, DocumentCurrencyCode=DocumentCurrencyCode, TaxCurrencyCode=TaxCurrencyCode)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║ Additional DocumentRe Reference ║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # Assuming invoice_id is defined and valid
        print(f"[{Now}]:: Additional DocumentRe Reference started.")
        ADR_query = "SELECT * FROM AdditionalDocumentReference WHERE InvoiceID = %s"
        table_name = "AdditionalDocumentReference"
        ADR_rows, ADR_columns, msg, isError = execute_query(conn, cursor, ADR_query, table_name, (InvoiceID,))
        if isError:
            return msg, isError

        parameters["AdditionalDocumentReference"] = []
        for ADR_row in ADR_rows:
            ADR_detail = {
                "ID": ADR_row[ADR_columns.index('ID')],
                "UUID": ADR_row[ADR_columns.index('UUID')],
                "EmbeddedDocumentBinaryObject": ADR_row[ADR_columns.index('EmbeddedDocumentBinaryObject')],
            }
            parameters["AdditionalDocumentReference"].append(ADR_detail)
        AdditionalDocumentReferenceElements = XmlGenAdditionalDocumentReference(parameters)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║ S I G N A T U R E ║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Signature started.")
        signature_query = "SELECT * FROM Signature WHERE InvoiceID = %s"
        table_name = "Signature"
        rows, columns, msg, isError = execute_query(conn, cursor, signature_query, table_name, (InvoiceID,))
        if isError:
            return msg, isError

        parameters["Signature"] = []
        for row in rows:
            SignatureDetail = {
                "ID": row[columns.index('ID')],
                "SignatureMethod": row[columns.index('SignatureMethod')]
            }
            parameters["Signature"].append(SignatureDetail)
        SignatureElements = XmlGenSignature(parameters)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║ Accounting  Supplier  Party ║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Accounting  Supplier  Party started.")
        PartyType = 'SUPPLIER'
        AccountingSupplierPartyQuery = "SELECT * FROM AccountingParty WHERE InvoiceID = %s AND UPPER(TRIM(PartyType)) = UPPER(TRIM(%s))"
        table_name = "AccountingParty"
        supplier_rows, supplier_columns, msg, isError = execute_query(conn, cursor, AccountingSupplierPartyQuery, table_name, (InvoiceID, PartyType))
        if isError:
            return msg, isError

        parameters["AccountingSupplierParty"] = []
        parameters["SupplierPartyAddress"] = []
        parameters["SupplierPartyTaxScheme"] = []

        for supplier in supplier_rows:
            AccountingPartyID = supplier[supplier_columns.index('ID')]
            PartyIdentification = supplier[supplier_columns.index('PartyIdentification')]
            SchemeID = supplier[supplier_columns.index('SchemeID')]
            RegistrationName = supplier[supplier_columns.index('RegistrationName')]
            DeliveryPartyID = AccountingPartyID
            supplier_detail = {
                "ID": AccountingPartyID,
                "PartyIdentification": PartyIdentification,
                "SchemeID": SchemeID,
                "RegistrationName": RegistrationName
            }
            parameters["AccountingSupplierParty"].append(supplier_detail)

            # Supplier addresses
            AddressQuery = "SELECT * FROM AccountingPartyAddress WHERE UPPER(TRIM(AccountingPartyID)) = UPPER(TRIM(%s))"
            table_name = "AccountingPartyAddress"
            addresses, address_columns, msg, isError = execute_query(conn, cursor, AddressQuery, table_name, (AccountingPartyID,))

            if isError:
                return msg, isError

            for address in addresses:
                address_detail = {
                    "AccountingPartyID": AccountingPartyID,
                    "ID": address[address_columns.index('ID')],
                    "StreetName": address[address_columns.index('StreetName')],
                    "BuildingNumber": address[address_columns.index('BuildingNumber')],
                    "CitySubdivisionName": address[address_columns.index('CitySubdivisionName')],
                    "CityName": address[address_columns.index('CityName')],
                    "PostalZone": address[address_columns.index('PostalZone')],
                    "CountryID": address[address_columns.index('CountryID')]
                }
                parameters["SupplierPartyAddress"].append(address_detail)

            # Step 2: Retrieve Tax Schemes
            TaxSchemeQuery = "SELECT * FROM AccountingPartyTaxScheme WHERE UPPER(TRIM(AccountingPartyID)) = UPPER(TRIM(%s))"
            table_name = "AccountingPartyTaxScheme"
            scheme_rows, scheme_columns, msg, isError = execute_query(conn, cursor, TaxSchemeQuery, table_name, (AccountingPartyID,))
            if isError:
                return msg, isError

            for scheme in scheme_rows:
                tax_scheme_detail = {
                    "AccountingPartyID": AccountingPartyID,
                    "ID": scheme[scheme_columns.index('ID')],
                    "CompanyID": scheme[scheme_columns.index('CompanyID')],
                    "TaxSchemeCode": scheme[scheme_columns.index('TaxSchemeCode')]
                }
                parameters["SupplierPartyTaxScheme"].append(tax_scheme_detail)

        # Generate the XML
        AccountingSupplierPartyElements = XmlGenAccountingSupplierParty(parameters)


        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║ Accounting  Customer  Party ║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Accounting  Customer  Party started.")
        PartyType = "CUSTOMER"
        AccountingCustomerPartyQuery = "SELECT * FROM AccountingParty WHERE InvoiceID = %s AND UPPER(TRIM(PartyType)) = UPPER(TRIM(%s))"
        table_name = "AccountingParty"
        customer_rows, customer_columns, msg, isError = execute_query(conn, cursor, AccountingCustomerPartyQuery, table_name, (InvoiceID, PartyType))
        if isError:
            return msg, isError

        parameters["AccountingCustomerParty"] = []
        parameters["CustomerPartyAddress"] = []
        parameters["CustomerPartyTaxScheme"] = []

        for customer in customer_rows:
            AccountingPartyID = customer[customer_columns.index('ID')]
            PartyIdentification = customer[customer_columns.index('PartyIdentification')]
            SchemeID = customer[customer_columns.index('SchemeID')]
            RegistrationName = customer[customer_columns.index('RegistrationName')]
            DeliveryPartyID = AccountingPartyID
            customer_detail = {
                "ID": AccountingPartyID,
                "PartyIdentification": PartyIdentification,
                "SchemeID": SchemeID,
                "RegistrationName": RegistrationName
            }
            parameters["AccountingCustomerParty"].append(customer_detail)

            # Customer addresses
            AddressQuery = "SELECT * FROM AccountingPartyAddress WHERE UPPER(TRIM(AccountingPartyID)) = UPPER(TRIM(%s))"
            table_name = "AccountingPartyAddress"
            addresses, address_columns, msg, isError = execute_query(conn, cursor, AddressQuery, table_name, (AccountingPartyID,))

            if isError:
                return msg, isError

            for address in addresses:
                address_detail = {
                    "AccountingPartyID": AccountingPartyID,
                    "ID": address[address_columns.index('ID')],
                    "StreetName": address[address_columns.index('StreetName')],
                    "BuildingNumber": address[address_columns.index('BuildingNumber')],
                    "CitySubdivisionName": address[address_columns.index('CitySubdivisionName')],
                    "CityName": address[address_columns.index('CityName')],
                    "PostalZone": address[address_columns.index('PostalZone')],
                    "CountryID": address[address_columns.index('CountryID')]
                }
                parameters["CustomerPartyAddress"].append(address_detail)

            # Step 2: Retrieve Tax Schemes
            TaxSchemeQuery = "SELECT * FROM AccountingPartyTaxScheme WHERE UPPER(TRIM(AccountingPartyID)) = UPPER(TRIM(%s))"
            table_name = "AccountingPartyTaxScheme"
            scheme_rows, scheme_columns, msg, isError = execute_query(conn, cursor, TaxSchemeQuery, table_name, (AccountingPartyID,))
            if isError:
                return msg, isError

            for scheme in scheme_rows:
                tax_scheme_detail = {
                    "AccountingPartyID": AccountingPartyID,
                    "ID": scheme[scheme_columns.index('ID')],
                    "CompanyID": scheme[scheme_columns.index('CompanyID')],
                    "TaxSchemeCode": scheme[scheme_columns.index('TaxSchemeCode')]
                }
                parameters["CustomerPartyTaxScheme"].append(tax_scheme_detail)

        # Generate the XML
        AccountingCustomerPartyElements = XmlGenAccountingCustomerParty(parameters)


        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║ Delivery Date ║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Delivery started.")
        AllDatesXml = ""
        DeliveryQuery = "SELECT * FROM Delivery WHERE InvoiceID = %s AND AccountingPartyID = %s"
        table_name = "Delivery"
        delivery, columns, msg, isError = execute_query(conn, cursor, DeliveryQuery, table_name, (InvoiceID, DeliveryPartyID))
        if isError:
            return msg, isError

        AllDatesXml = ""
        for row in delivery:
            ActualDeliveryDate = row[columns.index('ActualDeliveryDate')]
            if ActualDeliveryDate:
                newXml = """<cbc:ActualDeliveryDate>{ActualDeliveryDate}</cbc:ActualDeliveryDate>"""
                AllDatesXml += newXml.format(ActualDeliveryDate=ActualDeliveryDate)

        if InvoiceTypeCode.strip() == "388":
            DeliveryElements = """<cac:Delivery>{ActualDeliveryDates}</cac:Delivery>"""
            DeliveryElements = DeliveryElements.format(ActualDeliveryDates=AllDatesXml)
        if InvoiceTypeCode.strip() == "389":
            DeliveryElements = ""

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║ Payment  Means ║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: Payment Means started.")
        PaymentMeansQuery = "SELECT * FROM PaymentMeans WHERE InvoiceID = %s AND AccountingPartyID = %s"
        table_name = "PaymentMeans"
        paymentMeans, columns, msg, isError = execute_query(conn, cursor, PaymentMeansQuery, table_name, (InvoiceID, DeliveryPartyID))
        if isError:
            return msg, isError

        PaymentMeansCodes = ""
        AllDatesXml = ""
        for row in paymentMeans:
            PaymentMeansCode = row[columns.index('PaymentMeansCode')]
            if paymentMeans:
                newXml = """<cbc:PaymentMeansCode>{PaymentMeansCode}</cbc:PaymentMeansCode>"""
                PaymentMeansCodes += newXml.format(PaymentMeansCode=PaymentMeansCode)

        PaymentMeansElements = """<cac:PaymentMeans>{PaymentMeansCodes}</cac:PaymentMeans>"""
        PaymentMeansElements = PaymentMeansElements.format(PaymentMeansCodes=PaymentMeansCodes)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║ Allowance  Charge ║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: AllowanceCharge started.")
        AllowanceChargeQuery = "SELECT * FROM AllowanceCharge WHERE InvoiceID = %s"
        table_name = "AllowanceCharge"
        allowanceChargeRows, allowanceChargeColumns, msg, isError = execute_query(conn, cursor, AllowanceChargeQuery, table_name, (InvoiceID, ))
        if isError:
            return msg, isError

        parameters["AllowanceCharge"] = []
        parameters["AllowanceTaxCategory"] = []
        parameters["AllowanceTaxCategoryScheme"] = []

        for allowanceCharge in allowanceChargeRows:
            AllowanceChargeID = allowanceCharge[allowanceChargeColumns.index('ID')]
            ChargeIndicator = allowanceCharge[allowanceChargeColumns.index('ChargeIndicator')]
            AllowanceChargeReason = allowanceCharge[allowanceChargeColumns.index('AllowanceChargeReason')]
            Amount = allowanceCharge[allowanceChargeColumns.index('Amount')]
            Amount = str(Amount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
            CurrencyID = allowanceCharge[allowanceChargeColumns.index('CurrencyID')]

            AllowanceChargeParameters = {
                "ID": AllowanceChargeID,
                "ChargeIndicator": ChargeIndicator,
                "AllowanceChargeReason": AllowanceChargeReason,
                "Amount": Amount,
                "CurrencyID": CurrencyID
            }
            parameters["AllowanceCharge"].append(AllowanceChargeParameters)

            # AllowanceTaxCategory
            AllowanceTaxCategoryQuery = "SELECT * FROM AllowanceTaxCategory WHERE AllowanceChargeID = %s"
            table_name = "AllowanceTaxCategory"
            allowanceTaxCategory, taxcategory_columns, msg, isError = execute_query(conn, cursor, AllowanceTaxCategoryQuery, table_name, (AllowanceChargeID,))
            if isError:
                return msg, isError

            AllowanceTaxCategoryID=""
            if allowanceTaxCategory is not None:
                parameters["AllowanceTaxCategory"] = []
                for taxCategory in allowanceTaxCategory:
                    AllowanceTaxCategoryID = taxCategory[taxcategory_columns.index('ID')]
                    allowanceTaxCategory_detail = {
                        "AllowanceChargeID": AllowanceChargeID,
                        "ID": taxCategory[taxcategory_columns.index('ID')],
                        "SchemeID": taxCategory[taxcategory_columns.index('SchemeID')],
                        "SchemeAgencyID": taxCategory[taxcategory_columns.index('SchemeAgencyID')],
                        "Percent": taxCategory[taxcategory_columns.index('Percent')],
                        "TaxCategoryCode": taxCategory[taxcategory_columns.index('TaxCategoryCode')],
                    }
                    parameters["AllowanceTaxCategory"].append(allowanceTaxCategory_detail)
                    AllowanceTaxCategoryID = taxCategory[taxcategory_columns.index('ID')]

                    # Step 2: Retrieve tax schemes
                    AllowanceTaxCategorySchemeQuery = "SELECT * FROM AllowanceTaxCategoryScheme WHERE AllowanceTaxCategoryID = %s"
                    table_name = "AllowanceTaxCategoryScheme"
                    taxCategoryScheme, taxCategorySchemeColumns, msg, isError = execute_query(conn, cursor, AllowanceTaxCategorySchemeQuery, table_name, (AllowanceTaxCategoryID,))
                    if isError:
                        return msg, isError

                    if taxCategoryScheme is not None:
                        parameters["AllowanceTaxCategoryScheme"] = []
                        for tax_scheme in taxCategoryScheme:
                            allowanceTaxCategorySchemeDetail = {
                                "AllowanceTaxCategoryID": AllowanceTaxCategoryID,
                                "ID": tax_scheme[taxCategorySchemeColumns.index('ID')],
                                "SchemeID": tax_scheme[taxCategorySchemeColumns.index('SchemeID')],
                                "SchemeAgencyID": tax_scheme[taxCategorySchemeColumns.index('SchemeAgencyID')],
                                "TaxSchemeCode": tax_scheme[taxCategorySchemeColumns.index('TaxSchemeCode')]
                            }
                            parameters["AllowanceTaxCategoryScheme"].append(allowanceTaxCategorySchemeDetail)

        # Generate the XML
        AllowanceChargeElements = XmlGenAllowanceCharge(parameters)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║ Tax Total ║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: TaxTotal started.")
        TaxTotalQuery = "SELECT * FROM TaxTotal WHERE InvoiceID = %s"
        table_name = "TaxTotal"
        taxTotal, taxTotalColumns, msg, isError = execute_query(conn, cursor, TaxTotalQuery, table_name, (InvoiceID, ))
        if isError:
            return msg, isError

        parameters["TaxTotal"] = []
        parameters["TaxSubTotal"] = []
        parameters["TaxSubCategory"] = []
        parameters["TaxSubCategoryScheme"] = []

        for invTotal in taxTotal:
            # apply decimal 2
            TaxAmount = invTotal[taxTotalColumns.index('TaxAmount')]
            TaxAmount = str(TaxAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

            taxTotal_detail = {
                "InvoiceID": InvoiceID,
                "ID": invTotal[taxTotalColumns.index('ID')],
                "TaxAmount": TaxAmount,
                "CurrencyID": invTotal[taxTotalColumns.index('CurrencyID')],
            }
            parameters["TaxTotal"].append(taxTotal_detail)
            TaxTotalID = invTotal[taxTotalColumns.index('ID')]

            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║║║║║ TaxSub Total ║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            print(f"[{Now}]:: TaxSubTotal started.")
            TaxSubTotalQuery = "SELECT * FROM TaxSubTotal WHERE TaxTotalID = %s"
            table_name = "TaxSubTotal"
            taxSubTotal, taxSubTotal_columns, msg, isError = execute_query(conn, cursor, TaxSubTotalQuery, table_name, (TaxTotalID, ))
            if isError:
                return msg, isError

            if taxSubTotal is not None:
                for SubTotal in taxSubTotal:
                    # apply decimal 2
                    TaxableAmount = SubTotal[taxSubTotal_columns.index('TaxableAmount')]
                    TaxableAmount = str(TaxableAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
                    # apply decimal 2
                    TaxAmount = SubTotal[taxSubTotal_columns.index('TaxAmount')]
                    TaxAmount = str(TaxAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

                    taxSubTotal_detail = {
                        "TaxTotalID": TaxTotalID,
                        "ID": SubTotal[taxSubTotal_columns.index('ID')],
                        "TaxableAmount": TaxableAmount,
                        "TaxAmount": TaxAmount,
                        "CurrencyID": SubTotal[taxSubTotal_columns.index('CurrencyID')],
                    }
                    parameters["TaxSubTotal"].append(taxSubTotal_detail)
                    TaxSubTotalID = SubTotal[taxSubTotal_columns.index('ID')]

                    # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                    # ║║║║║║║║║║║║║║║║║║║║ Tax Sub Category ║║║║║║║║║║║║║║║║║║
                    # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                    print(f"[{Now}]:: TaxSubCategory started.")
                    TaxSubCategoryQuery = "SELECT * FROM TaxSubCategory WHERE TaxSubTotalID = %s"
                    table_name = "TaxSubCategory"
                    taxSubCategory, taxSubCategoryColumns, msg, isError = execute_query(conn, cursor, TaxSubCategoryQuery, table_name, (TaxSubTotalID, ))
                    if isError:
                        return msg, isError

                    if taxSubCategory is not None:
                        for SubCategory in taxSubCategory:
                            taxSubCategoryDetail = {
                                "TaxSubTotalID": TaxSubTotalID,
                                "ID": SubCategory[taxSubCategoryColumns.index('ID')],
                                "SchemeID": SubCategory[taxSubCategoryColumns.index('SchemeID')],
                                "SchemeAgencyID": SubCategory[taxSubCategoryColumns.index('SchemeAgencyID')],
                                "Percent": SubCategory[taxSubCategoryColumns.index('Percent')],
                                "TaxCategoryCode": SubCategory[taxSubCategoryColumns.index('TaxCategoryCode')]
                            }
                            parameters["TaxSubCategory"].append(taxSubCategoryDetail)
                            TaxSubCategoryID = SubCategory[taxSubCategoryColumns.index('ID')]

                            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                            # ║║║║║║║║║║║║║║║ Tax Sub Category Scheme ║║║║║║║║║║║║║║║║
                            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                            print(f"[{Now}]:: TaxSubCategoryScheme started.")
                            TaxSubCategorySchemeQuery = "SELECT * FROM TaxSubCategoryScheme WHERE TaxSubCategoryID = %s"
                            table_name = "TaxSubCategoryScheme"
                            TaxSubCategorySchemeRows, TaxSubCategorySchemeColumns, msg, isError = execute_query(conn, cursor, TaxSubCategorySchemeQuery, table_name, (TaxSubCategoryID,))

                            if isError:
                                return msg, isError

                            if TaxSubCategorySchemeRows:
                                for row in TaxSubCategorySchemeRows:
                                    TaxSubCategorySchemeDetail = {
                                        "TaxSubCategoryID": TaxSubCategoryID,
                                        "ID": row[TaxSubCategorySchemeColumns.index('ID')],
                                        "SchemeID": row[TaxSubCategorySchemeColumns.index('SchemeID')],
                                        "SchemeAgencyID": row[TaxSubCategorySchemeColumns.index('SchemeAgencyID')],
                                        "TaxSchemeCode": row[TaxSubCategorySchemeColumns.index('TaxSchemeCode')]
                                    }
                                    parameters["TaxSubCategoryScheme"].append(TaxSubCategorySchemeDetail)
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║ A U T O   T A X   T O T A L ║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # BR-KSA-EN16931-09: when TaxCurrencyCode is present, ZATCA expects a
        # second bare TaxTotal (no TaxSubTotal linked to it). TaxTotal.py
        # already emits a bare <cac:TaxTotal> for any row without matching
        # subtotals. So if the client provided only one TaxTotal and the
        # invoice carries a TaxCurrencyCode, add a synthetic second row here.
        if TaxCurrencyCode and len(parameters["TaxTotal"]) == 1:
            base = parameters["TaxTotal"][0]
            synthetic_row = {
                "InvoiceID": base["InvoiceID"],
                "ID": "TT_TAXCURR",
                "TaxAmount": base["TaxAmount"],
                "CurrencyID": TaxCurrencyCode,
            }
            parameters["TaxTotal"].append(synthetic_row)
            print(f"[{Now}]:: Auto-added second bare TaxTotal in {TaxCurrencyCode}")

        TaxTotalElements = XmlGenTaxTotal(parameters)

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║ Legal Monetary Total ║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: LegalMonetaryTotal started.")
        LegalMonetaryTotalQuery = "SELECT * FROM LegalMonetaryTotal WHERE InvoiceID = %s"
        table_name = "LegalMonetaryTotal"
        rows, columns, msg, isError = execute_query(conn, cursor, LegalMonetaryTotalQuery, table_name, (InvoiceID, ))
        if isError:
            return msg, isError


        try: #LineExtensionAmount
            LineExtensionAmount = rows[0][columns.index('LineExtensionAmount')]
            LineExtensionAmount = str(LineExtensionAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            LineExtensionAmount = ''

        try: # ID
            LineExtensionCurrencyID = rows[0][columns.index('LineExtensionCurrencyID')]
        except IndexError:
            LineExtensionCurrencyID = ''

        try: #TaxExclusiveAmount
            TaxExclusiveAmount = rows[0][columns.index('TaxExclusiveAmount')]
            TaxExclusiveAmount = str(TaxExclusiveAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            TaxExclusiveAmount = ''
        try: # ID
            TaxExclusiveCurrencyID = rows[0][columns.index('TaxExclusiveCurrencyID')]
        except IndexError:
            TaxExclusiveCurrencyID = ''

        try: #TaxInclusiveAmount
            TaxInclusiveAmount = rows[0][columns.index('TaxInclusiveAmount')]
            TaxInclusiveAmount = str(TaxInclusiveAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            TaxInclusiveAmount = ''
        try:
            TaxInclusiveCurrencyID = rows[0][columns.index('TaxInclusiveCurrencyID')]
        except IndexError:
            TaxInclusiveCurrencyID = ''

        try: #AllowanceTotalAmount
            AllowanceTotalAmount = rows[0][columns.index('AllowanceTotalAmount')]
            AllowanceTotalAmount = str(AllowanceTotalAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            AllowanceTotalAmount = ''
        try:
            AllowanceCurrencyID = rows[0][columns.index('AllowanceCurrencyID')]
        except IndexError:
            AllowanceCurrencyID = ''

        try: #PrepaidAmount
            PrepaidAmount = rows[0][columns.index('PrepaidAmount')]
            PrepaidAmount = str(PrepaidAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            PrepaidAmount = ''
        try: # ID
            PrepaidCurrencyID = rows[0][columns.index('PrepaidCurrencyID')]
        except IndexError:
            PrepaidCurrencyID = ''

        try: #PayableAmount
            PayableAmount = rows[0][columns.index('PayableAmount')]
            PayableAmount = str(PayableAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
        except IndexError:
            PayableAmount = ''
        try: # ID
            PayableCurrencyID = rows[0][columns.index('PayableCurrencyID')]
        except IndexError:
            PayableCurrencyID = ''

        LineExtensionAmount = f'<cbc:LineExtensionAmount currencyID="{LineExtensionCurrencyID}">{LineExtensionAmount}</cbc:LineExtensionAmount>'
        TaxExclusiveAmount = f'<cbc:TaxExclusiveAmount currencyID="{TaxExclusiveCurrencyID}">{TaxExclusiveAmount}</cbc:TaxExclusiveAmount>'
        TaxInclusiveAmount = f'<cbc:TaxInclusiveAmount currencyID="{TaxInclusiveCurrencyID}">{TaxInclusiveAmount}</cbc:TaxInclusiveAmount>'
        AllowanceTotalAmount = f'<cbc:AllowanceTotalAmount currencyID="{AllowanceCurrencyID}">{AllowanceTotalAmount}</cbc:AllowanceTotalAmount>'
        PrepaidAmount = f'<cbc:PrepaidAmount currencyID="{PrepaidCurrencyID}">{PrepaidAmount}</cbc:PrepaidAmount>'
        PayableAmount = f'<cbc:PayableAmount currencyID="{PayableCurrencyID}">{PayableAmount}</cbc:PayableAmount>'

        LegalMonetaryTotalElements = f"<cac:LegalMonetaryTotal>{LineExtensionAmount}{TaxExclusiveAmount}{TaxInclusiveAmount}{AllowanceTotalAmount}{PrepaidAmount}{PayableAmount}</cac:LegalMonetaryTotal>"

        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║ Invoice Line ║║║║║║║║║║║║║║║║║║║║║║║
        # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
        print(f"[{Now}]:: InvoiceLine started.")
        InvoiceLineElements = ""
        InvoiceLineQuery = "SELECT * FROM InvoiceLine WHERE InvoiceID = %s"
        table_name = "InvoiceLine"
        InvoiceLineRows, InvoiceLineColumns, msg, isError = execute_query(conn, cursor, InvoiceLineQuery, table_name, (InvoiceID, ))
        if isError:
            return f'InvoiceLine: {msg}', isError

#       initialize lists
        parameters["InvoiceLine"] = []
        parameters["InvoiceLineTaxTotal"] = []
        parameters["InvoiceLineItem"] = []
        parameters["InvoiceLineTaxCategory"] = []
        parameters["InvoiceLineTaxScheme"] = []
        parameters["InvoiceLinePrice"] = []
        parameters["InvoiceLineAllowanceCharge"] = []

        # Level = 0
        for InvoiceLineRow in InvoiceLineRows:
            # apply 2 decimal
            InvoicedQuantity = InvoiceLineRow[InvoiceLineColumns.index('InvoicedQuantity')]
            InvoicedQuantity = str(InvoicedQuantity.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
            # apply 2 decimal
            LineExtensionAmount = InvoiceLineRow[InvoiceLineColumns.index('LineExtensionAmount')]
            LineExtensionAmount = str(LineExtensionAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

            InvoiceLine_detail = {
                "ID": InvoiceLineRow[InvoiceLineColumns.index('ID')],
                "InvoicedQuantity": InvoicedQuantity,
                "UnitCode": InvoiceLineRow[InvoiceLineColumns.index('UnitCode')],
                "LineExtensionAmount": LineExtensionAmount,
                "LineExtensionCurrencyID": InvoiceLineRow[InvoiceLineColumns.index('LineExtensionCurrencyID')]
            }
            parameters["InvoiceLine"].append(InvoiceLine_detail)
            InvoiceLineID = InvoiceLineRow[InvoiceLineColumns.index('ID')]

            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║ InvoiceLine Tax Total ║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # Leaf@Level1
            print(f"[{Now}]:: InvoiceLineTaxTotal started.")
            InvoiceLineTaxTotalQuery = "SELECT * FROM InvoiceLineTaxTotal WHERE LineID = %s"
            table_name = "InvoiceLineTaxTotal"
            InvoiceLineTaxTotalRows, InvoiceLineTaxTotalColumns, msg, isError = execute_query(conn, cursor, InvoiceLineTaxTotalQuery, table_name, (InvoiceLineID, ))
            if isError:
                return f'InvoiceLineTaxTotal: {msg}', isError

            for InvoiceLineTaxTotalRow in InvoiceLineTaxTotalRows:
                # apply decimal 2
                TaxAmount = InvoiceLineTaxTotalRow[InvoiceLineTaxTotalColumns.index('TaxAmount')]
                TaxAmount = str(TaxAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))
                # apply decimal 2
                RoundingAmount = InvoiceLineTaxTotalRow[InvoiceLineTaxTotalColumns.index('RoundingAmount')]
                RoundingAmount = str(RoundingAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

                InvoiceLineTaxTotal_detail = {
                    "InvoiceLineID": InvoiceLineID,
                    "ID": InvoiceLineTaxTotalRow[InvoiceLineTaxTotalColumns.index('ID')],
                    "TaxAmount": TaxAmount,
                    "TaxAmountCurrencyID": InvoiceLineTaxTotalRow[InvoiceLineTaxTotalColumns.index('TaxAmountCurrencyID')],
                    "RoundingAmount": RoundingAmount,
                    "RoundingAmountCurrencyID": InvoiceLineTaxTotalRow[InvoiceLineTaxTotalColumns.index('RoundingAmountCurrencyID')],
                }
                parameters["InvoiceLineTaxTotal"].append(InvoiceLineTaxTotal_detail)
                # A Leaf needed no ID reference

            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║ Invoice Line Item ║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # Group@Level1
            print(f"[{Now}]:: InvoiceLineItem started.")
            InvoiceLineItemQuery = "SELECT * FROM InvoiceLineItem WHERE LineID = %s"
            table_name = "InvoiceLineItem"
            InvoiceLineItemRows, InvoiceLineItemColumns, msg, isError = execute_query(conn, cursor, InvoiceLineItemQuery, table_name, (InvoiceLineID, ))
            if isError:
                return f'InvoiceLineItem: {msg}', isError

            for InvoiceLineItemRow in InvoiceLineItemRows:
                InvoiceLineItemDetail = {
                    "InvoiceLineID": InvoiceLineID,
                    "ID": InvoiceLineItemRow[InvoiceLineItemColumns.index('ID')],
                    "Name": InvoiceLineItemRow[InvoiceLineItemColumns.index('Name')]
                }
                parameters["InvoiceLineItem"].append(InvoiceLineItemDetail)
                InvoiceLineItemID = InvoiceLineItemRow[InvoiceLineItemColumns.index('ID')]

                # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                # ║║║║║║║║║║║║║║ Invoice Line Tax Category ║║║║║║║║║║║║║║║
                # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                # Group@Level2
                InvoiceLineTaxCategoryQuery = "SELECT * FROM InvoiceLineTaxCategory WHERE InvoiceLineItemID = %s"
                table_name = "InvoiceLineTaxCategory"
                InvoiceLineTaxCategoryRows, InvoiceLineTaxCategoryColumns, msg, isError = execute_query(conn, cursor, InvoiceLineTaxCategoryQuery, table_name, (InvoiceLineItemID,))

                if isError:
                    return f'InvoiceLineTaxCategory: {msg}', isError


                for InvoiceLineTaxCategoryRow in InvoiceLineTaxCategoryRows:
                    InvoiceLineTaxCategoryDetail = {
                        "InvoiceLineItemID": InvoiceLineItemID,
                        "ID": InvoiceLineTaxCategoryRow[InvoiceLineTaxCategoryColumns.index('ID')],
                        "Percent": InvoiceLineTaxCategoryRow[InvoiceLineTaxCategoryColumns.index('Percent')],
                        "TaxCategoryCode": InvoiceLineTaxCategoryRow[InvoiceLineTaxCategoryColumns.index('TaxCategoryCode')]
                    }
                    parameters["InvoiceLineTaxCategory"].append(InvoiceLineTaxCategoryDetail)
                    InvoiceLineTaxCategoryID = InvoiceLineTaxCategoryRow[InvoiceLineTaxCategoryColumns.index('ID')]

                    # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                    # ║║║║║║║║║║║║║║║ Invoice Line Tax Scheme ║║║║║║║║║║║║║║║║
                    # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                    # Single@Level3
                    print(f"[{Now}]:: InvoiceLineTaxScheme started.")
                    InvoiceLineTaxSchemeQuery = "SELECT * FROM InvoiceLineTaxScheme WHERE InvoiceLineTaxCategoryID = %s"
                    table_name = "InvoiceLineTaxScheme"
                    InvoiceLineTaxSchemeRows, InvoiceLineTaxSchemeColumns, msg, isError = execute_query(conn, cursor, InvoiceLineTaxSchemeQuery, table_name, (InvoiceLineTaxCategoryID,))

                    if isError:
                        return f'InvoiceLineTaxScheme: {msg}', isError

                    for InvoiceLineTaxSchemeRow in InvoiceLineTaxSchemeRows:
                        InvoiceLineTaxSchemeDetail = {
                            "InvoiceLineTaxCategoryID": InvoiceLineTaxCategoryID,
                            "ID": InvoiceLineTaxSchemeRow[InvoiceLineTaxSchemeColumns.index('ID')],
                            "TaxSchemeCode": InvoiceLineTaxSchemeRow[InvoiceLineTaxSchemeColumns.index('TaxSchemeCode')]
                        }
                        parameters["InvoiceLineTaxScheme"].append(InvoiceLineTaxSchemeDetail)
                        #leaf end

            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║ Invoice Line Price ║║║║║║║║║║║║║║║║║║
            # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
            # Group@Level1
            print(f"[{Now}]:: InvoiceLinePrice started.")
            InvoiceLinePriceQuery = "SELECT * FROM InvoiceLinePrice WHERE LineID = %s"
            table_name = "InvoiceLinePrice"
            InvoiceLinePriceRows, InvoiceLinePriceColumns, msg, isError = execute_query(conn, cursor, InvoiceLinePriceQuery, table_name, (InvoiceLineID, ))
            if isError:
                return f'InvoiceLinePrice: {msg}', isError

            for InvoiceLinePriceRow in InvoiceLinePriceRows:
                # apply decimal 2
                PriceAmount = InvoiceLinePriceRow[InvoiceLinePriceColumns.index('PriceAmount')]
                PriceAmount = str(PriceAmount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

                InvoiceLinePriceDetail = {
                    "InvoiceLineID": InvoiceLineID,
                    "ID": InvoiceLinePriceRow[InvoiceLinePriceColumns.index('ID')],
                    "PriceAmount": PriceAmount,
                    "PriceAmountCurrencyID": InvoiceLinePriceRow[InvoiceLinePriceColumns.index('PriceAmountCurrencyID')]
                }
                parameters["InvoiceLinePrice"].append(InvoiceLinePriceDetail)
                InvoiceLinePriceID = InvoiceLinePriceRow[InvoiceLinePriceColumns.index('ID')]

                # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                # ║║║║║║║║║║║ Invoice Line Allowance Charge ║║║║║║║║║║║║║║
                # ║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║
                # Single@Level2 eeeeee
                print(f"[{Now}]:: InvoiceLineAllowanceCharge started.")
                InvoiceLineAllowanceChargeQuery = "SELECT * FROM InvoiceLineAllowanceCharge WHERE InvoiceLinePriceID = %s"
                table_name = "InvoiceLineAllowanceCharge"
                InvoiceLineAllowanceChargeRows, InvoiceLineAllowanceChargeColumns, msg, isError = execute_query(conn, cursor, InvoiceLineAllowanceChargeQuery, table_name, (InvoiceLinePriceID,))

                if isError:
                    return f'InvoiceLineAllowanceCharge: {msg}', isError

                for InvoiceLineAllowanceChargeRow in InvoiceLineAllowanceChargeRows:
                    # apply deimal 2
                    Amount = InvoiceLineAllowanceChargeRow[InvoiceLineAllowanceChargeColumns.index('Amount')]
                    Amount = str(Amount.quantize(Decimal('0.00'), rounding=ROUND_DOWN))

                    InvoiceLineAllowanceChargeDetail = {
                        "InvoiceLinePriceID": InvoiceLinePriceID,
                        "ID": InvoiceLineAllowanceChargeRow[InvoiceLineAllowanceChargeColumns.index('ID')],
                        "ChargeIndicator": InvoiceLineAllowanceChargeRow[InvoiceLineAllowanceChargeColumns.index('ChargeIndicator')],
                        "AllowanceChargeReason": InvoiceLineAllowanceChargeRow[InvoiceLineAllowanceChargeColumns.index('AllowanceChargeReason')],
                        "Amount": Amount,
                        "CurrencyID": InvoiceLineAllowanceChargeRow[InvoiceLineAllowanceChargeColumns.index('CurrencyID')]
                    }

                    parameters["InvoiceLineAllowanceCharge"].append(InvoiceLineAllowanceChargeDetail)
                    #leaf end

        InvoiceLineElements = XmlGenInvoiceLine(parameters)

        #      ║║║║║║║║║║║║║║║║║║║║║║║║ Complete Xml ║║║║║║║║║║║║║║║║║║║║
        # print("║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║")
        # print(f"║║║║║║║║║║║║║║║║║║║║║║ {InvoiceType} ║║║║║║║║║║║║║║║║║║║║║║║")
        # print("║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║║")
        print(f"[{Now}]:: ║║║║║║║║║║║║║║║ Complete Xml prepared. ║║║║║║║║║║║║║║║")
        CompleteElements = """{NameSpaceElements}{InvoiceElements}{AdditionalDocumentReferenceElements}{SignatureElements}{AccountingSupplierPartyElements}{AccountingCustomerPartyElements}{DeliveryElements}{PaymentMeansElements}{AllowanceChargeElements}{TaxTotalElements}{LegalMonetaryTotalElements}{InvoiceLineElements}"""
        CompleteElements = CompleteElements.format(NameSpaceElements=NameSpaceElements, InvoiceElements=InvoiceElements, AdditionalDocumentReferenceElements=AdditionalDocumentReferenceElements, SignatureElements=SignatureElements, AccountingSupplierPartyElements=AccountingSupplierPartyElements, AccountingCustomerPartyElements=AccountingCustomerPartyElements, DeliveryElements=DeliveryElements, PaymentMeansElements=PaymentMeansElements, AllowanceChargeElements=AllowanceChargeElements, TaxTotalElements=TaxTotalElements, LegalMonetaryTotalElements=LegalMonetaryTotalElements, InvoiceLineElements=InvoiceLineElements)
        CompleteXml = CompleteXml.format(CompleteElements=CompleteElements)
        isError = False
        return CompleteXml, isError



        # accounting_supplier_party = execute_query(conn, accounting_supplier_party_query, "AccountingSupplierParty")
        # if isinstance(accounting_supplier_party, str):
        #     return accounting_supplier_party
        #
        # accounting_customer_party = execute_query(conn, accounting_customer_party_query, "AccountingCustomerParty")
        # if isinstance(accounting_customer_party, str):
        #     return accounting_customer_party
        #
        # payment_means = execute_query(conn, payment_means_query, "PaymentMeans")
        # if isinstance(payment_means, str):
        #     return payment_means
        #
        # allowance_charge = execute_query(conn, allowance_charge_query, "AllowanceCharge")
        # if isinstance(allowance_charge, str):
        #     return allowance_charge
        #
        # tax_total = execute_query(conn, tax_total_query, "TaxTotal")
        # if isinstance(tax_total, str):
        #     return tax_total
        #
        # tax_subtotal = execute_query(conn, tax_subtotal_query, "TaxSubtotal")
        # if isinstance(tax_subtotal, str):
        #     return tax_subtotal
        #
        # legal_monetary_total = execute_query(conn, legal_monetary_total_query, "LegalMonetaryTotal")
        # if isinstance(legal_monetary_total, str):
        #     return legal_monetary_total
        #
        # invoice_line = execute_query(conn, invoice_line_query, "InvoiceLine")
        # if isinstance(invoice_line, str):
        #     return invoice_line
        #
        # # Process the fetched data
        # print(f"Number of rows found in Invoice: {len(invoice)}")
        # for invoice_row in invoice:
        #     print(invoice_row)
        #
        # # Add similar processing for other tables as needed
        # print(f"Number of rows found in Signature: {len(signature)}")
        # for signature_row in signature:Invoice
        #     print(signature_row)

        # Continue processing for other tables...

        return "All queries executed successfully."

    # except sqlite3.Error as e:
    #     return f"General SQL Error: SQL Error Code: {e.args[0]}, Message: {str(e)}"

    finally:
        if conn is not None:
            conn.close()


# AdditionalDocumentReference
# Signature
# AccountingSupplierParty
# AccountingCustomerParty
# Delivery
# PaymentMeans
# AllowanceCharge
# TaxTotal
# LegalMonetaryTotal
# InvoiceLine
#
