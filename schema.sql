-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Dec 01, 2024 at 02:48 AM
-- Server version: 8.0.39
-- PHP Version: 8.1.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `keytouse_zatca`
--

-- --------------------------------------------------------

--
-- Table structure for table `AccountingParty`
--

CREATE TABLE `AccountingParty` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `PartyIdentification` varchar(50) DEFAULT NULL,
  `SchemeID` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `PartyType` varchar(10) DEFAULT NULL,
  `RegistrationName` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AccountingParty`
--

INSERT INTO `AccountingParty` (`InvoiceID`, `ID`, `PartyIdentification`, `SchemeID`, `PartyType`, `RegistrationName`) VALUES
('INV001', 'CUST001', '6534565243524', 'IQA', 'CUSTOMER', 'Customer Name'),
('INV001', 'SUPP001', '1010010000', 'CRN', 'SUPPLIER', 'Supplier Company Name');

-- --------------------------------------------------------

--
-- Table structure for table `AccountingPartyAddress`
--

CREATE TABLE `AccountingPartyAddress` (
  `AccountingPartyID` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `StreetName` varchar(255) DEFAULT NULL,
  `BuildingNumber` varchar(50) DEFAULT NULL,
  `CitySubdivisionName` varchar(255) DEFAULT NULL,
  `CityName` varchar(255) DEFAULT NULL,
  `PostalZone` varchar(20) DEFAULT NULL,
  `CountryID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AccountingPartyAddress`
--

INSERT INTO `AccountingPartyAddress` (`AccountingPartyID`, `ID`, `InvoiceID`, `StreetName`, `BuildingNumber`, `CitySubdivisionName`, `CityName`, `PostalZone`, `CountryID`) VALUES
('CUST001', 'CustomerAddress1', 'INV001', 'Choburji Chowk', '5472', 'Ichra more', 'Lahore', '54788', 'SA'),
('SUPP001', 'ADDR001', 'INV001', '123 Supplier St', '5847', 'Downtown', 'Supplier City', '12415', 'SA');

-- --------------------------------------------------------

--
-- Table structure for table `AccountingPartyTaxScheme`
--

CREATE TABLE `AccountingPartyTaxScheme` (
  `AccountingPartyID` varchar(10) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `CompanyID` varchar(50) DEFAULT NULL,
  `TaxSchemeCode` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AccountingPartyTaxScheme`
--

INSERT INTO `AccountingPartyTaxScheme` (`AccountingPartyID`, `ID`, `InvoiceID`, `CompanyID`, `TaxSchemeCode`) VALUES
('CUST001', '2', 'INV001', '312345678965413', 'VAT'),
('SUPP001', '1', 'INV001', '310000678965413', 'VAT');

-- --------------------------------------------------------

--
-- Table structure for table `AdditionalDocumentReference`
--

CREATE TABLE `AdditionalDocumentReference` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `UUID` varchar(50) DEFAULT NULL,
  `EmbeddedDocumentBinaryObject` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AdditionalDocumentReference`
--

INSERT INTO `AdditionalDocumentReference` (`InvoiceID`, `ID`, `UUID`, `EmbeddedDocumentBinaryObject`) VALUES
('INV001', 'ICV', '1', NULL),
('INV001', 'PIH', NULL, 'NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=='),
('INV001', 'QR', NULL, 'AW/YtNix2YPYqSDYqtmI2LHZitivINin2YTYqtmD2YbZiNmE2YjYrNmK2Kcg2KjYo9mC2LXZiSDYs9ix2LnYqSDYp9mE2YXYrdiv2YjYr9ipIHwgTWF4aW11bSBTcGVlZCBUZWNoIFN1cHBseSBMVEQCDzM5OTk5OTk5OTkwMDAwMwMTMjAyMi0wOS0wN1QxMjoyMToyOAQENC42MAUDMC42BixmKzBXQ3FuUGtJbkkrZUw5RzNMQXJ5MTJmVFBmK3RvQzlVWDA3RjRmSStzPQdgTUVVQ0lCeHlSOHJjNEs4NzI4d2RTRjRYU0RxUHMrcklMKzNURmg5bSthTnhRUHRTQWlFQTZjSGFwSXR2cDEzeU1TdTY2TmJPZzJDcG9tSHdVU25ZSjloNnVHUTY1YVk9CFgwVjAQBgcqhkjOPQIBBgUrgQQACgNCAAShYIprRJr0UgStM6/S4CQLVUgpfFT2c+nHa+V/jKEx6PLxzTZcluUOru0/J2jyarRqE4yY2jyDCeLte3UpP1R4');

-- --------------------------------------------------------

--
-- Table structure for table `AllowanceCharge`
--

CREATE TABLE `AllowanceCharge` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `ChargeIndicator` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `AllowanceChargeReason` varchar(255) DEFAULT NULL,
  `Amount` decimal(18,6) DEFAULT NULL,
  `CurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AllowanceCharge`
--

INSERT INTO `AllowanceCharge` (`InvoiceID`, `ID`, `ChargeIndicator`, `AllowanceChargeReason`, `Amount`, `CurrencyID`) VALUES
('INV001', '1', 'false', 'discount', 0.000000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `AllowanceTaxCategory`
--

CREATE TABLE `AllowanceTaxCategory` (
  `AllowanceChargeID` varchar(50) NOT NULL,
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `SchemeID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `SchemeAgencyID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `Percent` decimal(5,2) DEFAULT NULL,
  `TaxCategoryCode` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AllowanceTaxCategory`
--

INSERT INTO `AllowanceTaxCategory` (`AllowanceChargeID`, `ID`, `InvoiceID`, `SchemeID`, `SchemeAgencyID`, `Percent`, `TaxCategoryCode`) VALUES
('1', 'ATC1', 'INV001', 'UN/ECE 5305', '6', 15.00, 'S');

-- --------------------------------------------------------

--
-- Table structure for table `AllowanceTaxCategoryScheme`
--

CREATE TABLE `AllowanceTaxCategoryScheme` (
  `AllowanceTaxCategoryID` varchar(50) NOT NULL,
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `SchemeID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `SchemeAgencyID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `TaxSchemeCode` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `AllowanceTaxCategoryScheme`
--

INSERT INTO `AllowanceTaxCategoryScheme` (`AllowanceTaxCategoryID`, `ID`, `InvoiceID`, `SchemeID`, `SchemeAgencyID`, `TaxSchemeCode`) VALUES
('ATC1', 'ATCS1', 'INV001', 'UN/ECE 5153', '6', 'VAT');

-- --------------------------------------------------------

--
-- Table structure for table `Config`
--

CREATE TABLE `Config` (
  `InvoiceType` varchar(50) DEFAULT NULL,
  `ClientIP` varchar(20) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `Config`
--

INSERT INTO `Config` (`InvoiceType`, `ClientIP`, `InvoiceID`, `CreatedAt`) VALUES
('STANDARD', '', '', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `CurrencyList`
--

CREATE TABLE `CurrencyList` (
  `CurrencyCode` varchar(3) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `CurrencyName` varchar(35) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `CurrencySymbol` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `CurrencyList`
--

INSERT INTO `CurrencyList` (`CurrencyCode`, `CurrencyName`, `CurrencySymbol`) VALUES
('AFN', 'Afghanis', '؋'),
('ALL', 'Leke', 'Lek'),
('ANG', 'Guilders', 'ƒ'),
('ARS', 'Pesos', '$'),
('AUD', 'Dollars', '$'),
('AWG', 'Guilders', 'ƒ'),
('AZN', 'New Manats', 'ман'),
('BAM', 'Convertible Marka', 'KM'),
('BBD', 'Dollars', '$'),
('BGN', 'Leva', 'лв'),
('BMD', 'Dollars', '$'),
('BND', 'Dollars', '$'),
('BOB', 'Bolivianos', '$b'),
('BRL', 'Reais', 'R$'),
('BSD', 'Dollars', '$'),
('BWP', 'Pula', 'P'),
('BYR', 'Rubles', 'p.'),
('BZD', 'Dollars', 'BZ$'),
('CAD', 'Dollars', '$'),
('CHF', 'Switzerland Francs', 'CHF'),
('CLP', 'Pesos', '$'),
('CNY', 'Yuan Renminbi', '¥'),
('COP', 'Pesos', '$'),
('CRC', 'Colón', '₡'),
('CUP', 'Pesos', '₱'),
('CZK', 'Koruny', 'Kč'),
('DKK', 'Kroner', 'kr'),
('DOP', 'Pesos', 'RD$'),
('EGP', 'Pounds', '£'),
('EUR', 'Euro', '€'),
('FJD', 'Dollars', '$'),
('FKP', 'Pounds', '£'),
('GBP', 'Pounds', '£'),
('GGP', 'Pounds', '£'),
('GHC', 'Cedis', '¢'),
('GIP', 'Pounds', '£'),
('GTQ', 'Quetzales', 'Q'),
('GYD', 'Dollars', '$'),
('HKD', 'Dollars', '$'),
('HNL', 'Lempiras', 'L'),
('HRK', 'Kuna', 'kn'),
('HUF', 'Forint', 'Ft'),
('IDR', 'Rupiahs', 'Rp'),
('ILS', 'New Shekels', '₪'),
('IMP', 'Pounds', '£'),
('INR', 'Rupees', 'Rp'),
('IRR', 'Rials', '﷼'),
('ISK', 'Kronur', 'kr'),
('JEP', 'Pounds', '£'),
('JMD', 'Dollars', 'J$'),
('JPY', 'Yen', '¥'),
('KGS', 'Soms', 'лв'),
('KHR', 'Riels', '៛'),
('KPW', 'Won', '₩'),
('KRW', 'Won', '₩'),
('KYD', 'Dollars', '$'),
('KZT', 'Tenge', 'лв'),
('LAK', 'Kips', '₭'),
('LBP', 'Pounds', '£'),
('LKR', 'Rupees', '₨'),
('LRD', 'Dollars', '$'),
('LTL', 'Litai', 'Lt'),
('LVL', 'Lati', 'Ls'),
('MKD', 'Denars', 'ден'),
('MNT', 'Tugriks', '₮'),
('MUR', 'Rupees', '₨'),
('MXN', 'Pesos', '$'),
('MYR', 'Ringgits', 'RM'),
('MZN', 'Meticais', 'MT'),
('NAD', 'Dollars', '$'),
('NGN', 'Nairas', '₦'),
('NIO', 'Cordobas', 'C$'),
('NOK', 'Krone', 'kr'),
('NPR', 'Rupees', '₨'),
('NZD', 'Dollars', '$'),
('OMR', 'Rials', '﷼'),
('PAB', 'Balboa', 'B/.'),
('PEN', 'Nuevos Soles', 'S/.'),
('PHP', 'Pesos', 'Php'),
('PKR', 'Rupees', '₨'),
('PLN', 'Zlotych', 'zł'),
('PYG', 'Guarani', 'Gs'),
('QAR', 'Rials', '﷼'),
('RON', 'New Lei', 'lei'),
('RSD', 'Dinars', 'Дин.'),
('RUB', 'Rubles', 'руб'),
('SAR', 'Riyals', '﷼'),
('SBD', 'Dollars', '$'),
('SCR', 'Rupees', '₨'),
('SEK', 'Kronor', 'kr'),
('SGD', 'Dollars', '$'),
('SHP', 'Pounds', '£'),
('SOS', 'Shillings', 'S'),
('SRD', 'Dollars', '$'),
('SVC', 'Colones', '$'),
('SYP', 'Pounds', '£'),
('THB', 'Baht', '฿'),
('TRL', 'Liras', '£'),
('TRY', 'Lira', '₺'),
('TTD', 'Dollars', 'TT$'),
('TVD', 'Dollars', '$'),
('TWD', 'New Dollars', 'NT$'),
('UAH', 'Hryvnia', '₴'),
('USD', 'Dollars', '$'),
('UYU', 'Pesos', '$U'),
('UZS', 'Sums', 'лв'),
('VEF', 'Bolivares Fuertes', 'Bs'),
('VND', 'Dong', '₫'),
('XCD', 'Dollars', '$'),
('YER', 'Rials', '﷼'),
('ZAR', 'Rand', 'R'),
('ZWD', 'Zimbabwe Dollars', 'Z$');

-- --------------------------------------------------------

--
-- Table structure for table `Delivery`
--

CREATE TABLE `Delivery` (
  `InvoiceID` varchar(50) NOT NULL,
  `AccountingPartyID` varchar(50) NOT NULL,
  `ActualDeliveryDate` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `Delivery`
--

INSERT INTO `Delivery` (`InvoiceID`, `AccountingPartyID`, `ActualDeliveryDate`) VALUES
('INV001', 'CUST001', '2024-10-12'),
('INV001', 'SUPP001', '2024-09-26');

-- --------------------------------------------------------

--
-- Table structure for table `Invoice`
--

CREATE TABLE `Invoice` (
  `ID` varchar(50) NOT NULL,
  `ProfileID` varchar(50) DEFAULT NULL,
  `UUID` varchar(50) DEFAULT NULL,
  `IssueDate` date DEFAULT NULL,
  `IssueTime` time DEFAULT NULL,
  `InvoiceTypeCode` varchar(50) DEFAULT NULL,
  `InvoiceTypeName` varchar(10) DEFAULT '0100000',
  `Note` varchar(255) DEFAULT NULL,
  `DocumentCurrencyCode` varchar(10) DEFAULT NULL,
  `TaxCurrencyCode` varchar(10) DEFAULT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `Invoice`
--

INSERT INTO `Invoice` (`ID`, `ProfileID`, `UUID`, `IssueDate`, `IssueTime`, `InvoiceTypeCode`, `Note`, `DocumentCurrencyCode`, `TaxCurrencyCode`, `CreatedAt`) VALUES
('INV001', 'reporting:1.0', 'UUID-456', '2024-09-06', '14:30:00', '388', 'descriptive note sample invoice', 'SAR', 'SAR', '2024-11-23 11:31:30');

--
-- Triggers `Invoice`
--
DELIMITER $$
CREATE TRIGGER `before_invoice_insert` BEFORE INSERT ON `Invoice` FOR EACH ROW BEGIN
    -- Example action: Validate that ID is not null
    IF NEW.ID IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ID cannot be null.';
    END IF;
    
    -- Check if DocumentCurrencyCode exists in Currency table
    IF NEW.DocumentCurrencyCode IS NULL OR 
       NOT EXISTS (SELECT 1 FROM CurrencyList WHERE CurrencyCode = NEW.DocumentCurrencyCode) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid Document Currency Code.';
    END IF;
    
    -- create date from client will be null so must be set here
    -- no matter client set null or set datetime, the vlaue will always
    -- be overwritten
    SET NEW.CreatedAt = CURRENT_TIMESTAMP;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLine`
--

CREATE TABLE `InvoiceLine` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoicedQuantity` decimal(18,6) DEFAULT NULL,
  `UnitCode` varchar(10) DEFAULT NULL,
  `LineExtensionAmount` decimal(18,6) DEFAULT NULL,
  `LineExtensionCurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLine`
--

INSERT INTO `InvoiceLine` (`InvoiceID`, `ID`, `InvoicedQuantity`, `UnitCode`, `LineExtensionAmount`, `LineExtensionCurrencyID`) VALUES
('INV001', 'L1', 2.000000, 'PCE', 4.000000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLineAllowanceCharge`
--

CREATE TABLE `InvoiceLineAllowanceCharge` (
  `InvoiceLinePriceID` varchar(10) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `ChargeIndicator` varchar(5) DEFAULT NULL,
  `AllowanceChargeReason` varchar(250) DEFAULT NULL,
  `Amount` decimal(18,6) DEFAULT NULL,
  `CurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLineAllowanceCharge`
--

INSERT INTO `InvoiceLineAllowanceCharge` (`InvoiceLinePriceID`, `ID`, `InvoiceID`, `ChargeIndicator`, `AllowanceChargeReason`, `Amount`, `CurrencyID`) VALUES
('LP1', 'LAC1', 'INV001', 'true', 'Streight Discount', 0.000000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLineItem`
--

CREATE TABLE `InvoiceLineItem` (
  `LineID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `Name` varchar(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLineItem`
--

INSERT INTO `InvoiceLineItem` (`LineID`, `ID`, `InvoiceID`, `Name`) VALUES
('L1', 'LI1', 'INV001', 'Apple Juice 100% organic');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLinePrice`
--

CREATE TABLE `InvoiceLinePrice` (
  `LineID` varchar(50) NOT NULL,
  `ID` varchar(10) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `PriceAmount` decimal(18,6) DEFAULT NULL,
  `PriceAmountCurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLinePrice`
--

INSERT INTO `InvoiceLinePrice` (`LineID`, `ID`, `InvoiceID`, `PriceAmount`, `PriceAmountCurrencyID`) VALUES
('L1', 'LP1', 'INV001', 2.000000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLineTaxCategory`
--

CREATE TABLE `InvoiceLineTaxCategory` (
  `InvoiceLineItemID` varchar(50) NOT NULL,
  `ID` varchar(10) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `Percent` decimal(5,2) DEFAULT NULL,
  `TaxCategoryCode` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLineTaxCategory`
--

INSERT INTO `InvoiceLineTaxCategory` (`InvoiceLineItemID`, `ID`, `InvoiceID`, `Percent`, `TaxCategoryCode`) VALUES
('LI1', 'ILTC1', 'INV001', 15.00, 'S');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLineTaxScheme`
--

CREATE TABLE `InvoiceLineTaxScheme` (
  `InvoiceLineTaxCategoryID` varchar(10) NOT NULL,
  `ID` varchar(10) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `TaxSchemeCode` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLineTaxScheme`
--

INSERT INTO `InvoiceLineTaxScheme` (`InvoiceLineTaxCategoryID`, `ID`, `InvoiceID`, `TaxSchemeCode`) VALUES
('ILTC1', 'ILTCS1', 'INV001', 'VAT');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceLineTaxTotal`
--

CREATE TABLE `InvoiceLineTaxTotal` (
  `LineID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `TaxAmount` decimal(18,6) DEFAULT NULL,
  `TaxAmountCurrencyID` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `RoundingAmount` decimal(18,6) DEFAULT NULL,
  `RoundingAmountCurrencyID` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceLineTaxTotal`
--

INSERT INTO `InvoiceLineTaxTotal` (`LineID`, `ID`, `InvoiceID`, `TaxAmount`, `TaxAmountCurrencyID`, `RoundingAmount`, `RoundingAmountCurrencyID`) VALUES
('L1', 'LTT1', 'INV001', 0.600000, 'SAR', 4.600000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceType`
--

CREATE TABLE `InvoiceType` (
  `InvoiceTypeCode` varchar(10) NOT NULL,
  `IncoiceTypeName` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='all invoice types and their codes';

--
-- Dumping data for table `InvoiceType`
--

INSERT INTO `InvoiceType` (`InvoiceTypeCode`, `IncoiceTypeName`) VALUES
('388', 'Standard Tax Invoice'),
('389', 'Simplified Tax Invoice'),
('390', 'Credit Note'),
('391', 'Debit Note'),
('392', 'Proforma Invoice'),
('393', 'Advance Payment Invoice');

-- --------------------------------------------------------

--
-- Table structure for table `InvoiceTypeList`
--

CREATE TABLE `InvoiceTypeList` (
  `code` varchar(3) NOT NULL,
  `name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `InvoiceTypeList`
--

INSERT INTO `InvoiceTypeList` (`code`, `name`) VALUES
('381', 'Credit note'),
('383', 'Debit note'),
('386', 'Prepayment Invoice'),
('388', 'Standard Tax Invoice'),
('389', 'Simple Tax Invoice');

-- --------------------------------------------------------

--
-- Table structure for table `LegalMonetaryTotal`
--

CREATE TABLE `LegalMonetaryTotal` (
  `InvoiceID` varchar(50) NOT NULL,
  `LineExtensionAmount` decimal(18,6) DEFAULT NULL,
  `LineExtensionCurrencyID` varchar(10) DEFAULT NULL,
  `TaxExclusiveAmount` decimal(18,6) DEFAULT NULL,
  `TaxExclusiveCurrencyID` varchar(10) DEFAULT NULL,
  `TaxInclusiveAmount` decimal(18,6) DEFAULT NULL,
  `TaxInclusiveCurrencyID` varchar(10) DEFAULT NULL,
  `AllowanceTotalAmount` decimal(18,6) DEFAULT NULL,
  `AllowanceCurrencyID` varchar(10) DEFAULT NULL,
  `PrepaidAmount` decimal(18,6) DEFAULT NULL,
  `PrepaidCurrencyID` varchar(10) DEFAULT NULL,
  `PayableAmount` decimal(18,6) DEFAULT NULL,
  `PayableCurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `LegalMonetaryTotal`
--

INSERT INTO `LegalMonetaryTotal` (`InvoiceID`, `LineExtensionAmount`, `LineExtensionCurrencyID`, `TaxExclusiveAmount`, `TaxExclusiveCurrencyID`, `TaxInclusiveAmount`, `TaxInclusiveCurrencyID`, `AllowanceTotalAmount`, `AllowanceCurrencyID`, `PrepaidAmount`, `PrepaidCurrencyID`, `PayableAmount`, `PayableCurrencyID`) VALUES
('INV001', 4.000000, 'SAR', 4.000000, 'SAR', 4.600000, 'SAR', 0.000000, 'SAR', 0.000000, 'SAR', 4.600000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `PaymentMeans`
--

CREATE TABLE `PaymentMeans` (
  `InvoiceID` varchar(50) NOT NULL,
  `AccountingPartyID` varchar(50) NOT NULL,
  `PaymentMeansCode` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `PaymentMeans`
--

INSERT INTO `PaymentMeans` (`InvoiceID`, `AccountingPartyID`, `PaymentMeansCode`) VALUES
('INV001', 'CUST001', '10');

-- --------------------------------------------------------

--
-- Table structure for table `RowsNotRequired`
--

CREATE TABLE `RowsNotRequired` (
  `TableName` varchar(50) NOT NULL,
  `InvoiceTypeCode` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `RowsNotRequired`
--

INSERT INTO `RowsNotRequired` (`TableName`, `InvoiceTypeCode`) VALUES
('Config', '388'),
('TaxSubCategory', '388'),
('TaxSubCategoryScheme', '388'),
('TaxSubTotal', '388'),
('Config', '389'),
('TaxSubCategory', '389'),
('Config', '390'),
('Config', '391'),
('Config', '392');

-- --------------------------------------------------------

--
-- Table structure for table `Signature`
--

CREATE TABLE `Signature` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(255) NOT NULL,
  `SignatureMethod` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `Signature`
--

INSERT INTO `Signature` (`InvoiceID`, `ID`, `SignatureMethod`) VALUES
('INV001', 'urn:oasis:names:specification:ubl:signature:Invoice', 'urn:oasis:names:specification:ubl:dsig:enveloped:xades');

-- --------------------------------------------------------

--
-- Table structure for table `TaxSubCategory`
--

CREATE TABLE `TaxSubCategory` (
  `TaxSubTotalID` varchar(50) NOT NULL,
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `TaxCategoryCode` varchar(5) NOT NULL,
  `SchemeID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `SchemeAgencyID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `Percent` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `TaxSubCategory`
--

INSERT INTO `TaxSubCategory` (`TaxSubTotalID`, `ID`, `InvoiceID`, `TaxCategoryCode`, `SchemeID`, `SchemeAgencyID`, `Percent`) VALUES
('TST1', 'TSC1', 'INV001', 'S', 'UN/ECE 515', '6', 15.00);

-- --------------------------------------------------------

--
-- Table structure for table `TaxSubCategoryScheme`
--

CREATE TABLE `TaxSubCategoryScheme` (
  `TaxSubCategoryID` varchar(50) NOT NULL,
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `TaxSchemeCode` varchar(5) NOT NULL,
  `SchemeID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `SchemeAgencyID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `TaxSubCategoryScheme`
--

INSERT INTO `TaxSubCategoryScheme` (`TaxSubCategoryID`, `ID`, `InvoiceID`, `TaxSchemeCode`, `SchemeID`, `SchemeAgencyID`) VALUES
('TSC1', 'TSCS1', 'INV001', 'VAT', 'UN/ECE 5153', '6');

-- --------------------------------------------------------

--
-- Table structure for table `TaxSubTotal`
--

CREATE TABLE `TaxSubTotal` (
  `TaxTotalID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `InvoiceID` varchar(50) NOT NULL,
  `TaxableAmount` decimal(10,6) DEFAULT NULL,
  `TaxAmount` decimal(10,6) DEFAULT NULL,
  `CurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `TaxSubTotal`
--

INSERT INTO `TaxSubTotal` (`TaxTotalID`, `ID`, `InvoiceID`, `TaxableAmount`, `TaxAmount`, `CurrencyID`) VALUES
('TT1', 'TST1', 'INV001', 4.000000, 0.600000, 'SAR');

-- --------------------------------------------------------

--
-- Table structure for table `TaxTotal`
--

CREATE TABLE `TaxTotal` (
  `InvoiceID` varchar(50) NOT NULL,
  `ID` varchar(50) NOT NULL,
  `TaxAmount` decimal(10,6) DEFAULT NULL,
  `CurrencyID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `TaxTotal`
--

INSERT INTO `TaxTotal` (`InvoiceID`, `ID`, `TaxAmount`, `CurrencyID`) VALUES
('INV001', 'TT1', 0.600000, 'SAR'),
('INV001', 'TT2', 0.600000, 'SAR');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `AccountingParty`
--
ALTER TABLE `AccountingParty`
  ADD PRIMARY KEY (`InvoiceID`,`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `AccountingPartyAddress`
--
ALTER TABLE `AccountingPartyAddress`
  ADD PRIMARY KEY (`AccountingPartyID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `AccountingPartyTaxScheme`
--
ALTER TABLE `AccountingPartyTaxScheme`
  ADD PRIMARY KEY (`AccountingPartyID`,`ID`),
  ADD UNIQUE KEY `ID` (`ID`),
  ADD KEY `ID_2` (`ID`);

--
-- Indexes for table `AdditionalDocumentReference`
--
ALTER TABLE `AdditionalDocumentReference`
  ADD PRIMARY KEY (`InvoiceID`,`ID`);

--
-- Indexes for table `AllowanceCharge`
--
ALTER TABLE `AllowanceCharge`
  ADD PRIMARY KEY (`InvoiceID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `AllowanceTaxCategory`
--
ALTER TABLE `AllowanceTaxCategory`
  ADD PRIMARY KEY (`AllowanceChargeID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `AllowanceTaxCategoryScheme`
--
ALTER TABLE `AllowanceTaxCategoryScheme`
  ADD PRIMARY KEY (`AllowanceTaxCategoryID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `CurrencyList`
--
ALTER TABLE `CurrencyList`
  ADD PRIMARY KEY (`CurrencyCode`),
  ADD KEY `code` (`CurrencyCode`);

--
-- Indexes for table `Delivery`
--
ALTER TABLE `Delivery`
  ADD PRIMARY KEY (`InvoiceID`,`AccountingPartyID`),
  ADD KEY `AccountingPartyID` (`AccountingPartyID`);

--
-- Indexes for table `Invoice`
--
ALTER TABLE `Invoice`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `fk_invoicetypecode` (`InvoiceTypeCode`);

--
-- Indexes for table `InvoiceLine`
--
ALTER TABLE `InvoiceLine`
  ADD PRIMARY KEY (`InvoiceID`,`ID`),
  ADD KEY `InvoiceID` (`InvoiceID`,`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLineAllowanceCharge`
--
ALTER TABLE `InvoiceLineAllowanceCharge`
  ADD PRIMARY KEY (`InvoiceLinePriceID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLineItem`
--
ALTER TABLE `InvoiceLineItem`
  ADD PRIMARY KEY (`LineID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLinePrice`
--
ALTER TABLE `InvoiceLinePrice`
  ADD PRIMARY KEY (`LineID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLineTaxCategory`
--
ALTER TABLE `InvoiceLineTaxCategory`
  ADD PRIMARY KEY (`InvoiceLineItemID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLineTaxScheme`
--
ALTER TABLE `InvoiceLineTaxScheme`
  ADD PRIMARY KEY (`InvoiceLineTaxCategoryID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceLineTaxTotal`
--
ALTER TABLE `InvoiceLineTaxTotal`
  ADD PRIMARY KEY (`LineID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `InvoiceType`
--
ALTER TABLE `InvoiceType`
  ADD PRIMARY KEY (`InvoiceTypeCode`);

--
-- Indexes for table `InvoiceTypeList`
--
ALTER TABLE `InvoiceTypeList`
  ADD PRIMARY KEY (`code`),
  ADD KEY `code` (`code`);

--
-- Indexes for table `LegalMonetaryTotal`
--
ALTER TABLE `LegalMonetaryTotal`
  ADD PRIMARY KEY (`InvoiceID`);

--
-- Indexes for table `PaymentMeans`
--
ALTER TABLE `PaymentMeans`
  ADD PRIMARY KEY (`InvoiceID`,`AccountingPartyID`,`PaymentMeansCode`),
  ADD KEY `AccountingPartyID` (`AccountingPartyID`);

--
-- Indexes for table `RowsNotRequired`
--
ALTER TABLE `RowsNotRequired`
  ADD PRIMARY KEY (`TableName`,`InvoiceTypeCode`) USING BTREE,
  ADD KEY `fk_invoicetype` (`InvoiceTypeCode`);

--
-- Indexes for table `Signature`
--
ALTER TABLE `Signature`
  ADD PRIMARY KEY (`InvoiceID`,`ID`);

--
-- Indexes for table `TaxSubCategory`
--
ALTER TABLE `TaxSubCategory`
  ADD PRIMARY KEY (`TaxSubTotalID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `TaxSubCategoryScheme`
--
ALTER TABLE `TaxSubCategoryScheme`
  ADD PRIMARY KEY (`TaxSubCategoryID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `TaxSubTotal`
--
ALTER TABLE `TaxSubTotal`
  ADD PRIMARY KEY (`TaxTotalID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `TaxTotal`
--
ALTER TABLE `TaxTotal`
  ADD PRIMARY KEY (`InvoiceID`,`ID`),
  ADD UNIQUE KEY `ID_2` (`ID`),
  ADD KEY `ID` (`ID`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `AccountingParty`
--
ALTER TABLE `AccountingParty`
  ADD CONSTRAINT `AccountingParty_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `AccountingPartyAddress`
--
ALTER TABLE `AccountingPartyAddress`
  ADD CONSTRAINT `fk_party_id` FOREIGN KEY (`AccountingPartyID`) REFERENCES `AccountingParty` (`ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Constraints for table `AccountingPartyTaxScheme`
--
ALTER TABLE `AccountingPartyTaxScheme`
  ADD CONSTRAINT `AccountingPartyTaxScheme_ibfk_1` FOREIGN KEY (`AccountingPartyID`) REFERENCES `AccountingParty` (`ID`);

--
-- Constraints for table `AdditionalDocumentReference`
--
ALTER TABLE `AdditionalDocumentReference`
  ADD CONSTRAINT `AdditionalDocumentReference_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `AllowanceCharge`
--
ALTER TABLE `AllowanceCharge`
  ADD CONSTRAINT `AllowanceCharge_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `AllowanceTaxCategory`
--
ALTER TABLE `AllowanceTaxCategory`
  ADD CONSTRAINT `AllowanceTaxCategory_ibfk_1` FOREIGN KEY (`AllowanceChargeID`) REFERENCES `AllowanceCharge` (`ID`);

--
-- Constraints for table `AllowanceTaxCategoryScheme`
--
ALTER TABLE `AllowanceTaxCategoryScheme`
  ADD CONSTRAINT `AllowanceTaxCategoryScheme_ibfk_1` FOREIGN KEY (`AllowanceTaxCategoryID`) REFERENCES `AllowanceTaxCategory` (`ID`);

--
-- Constraints for table `Delivery`
--
ALTER TABLE `Delivery`
  ADD CONSTRAINT `Delivery_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`),
  ADD CONSTRAINT `Delivery_ibfk_2` FOREIGN KEY (`AccountingPartyID`) REFERENCES `AccountingParty` (`ID`);

--
-- Constraints for table `Invoice`
--
ALTER TABLE `Invoice`
  ADD CONSTRAINT `fk_invoicetypecode` FOREIGN KEY (`InvoiceTypeCode`) REFERENCES `InvoiceType` (`InvoiceTypeCode`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Constraints for table `InvoiceLine`
--
ALTER TABLE `InvoiceLine`
  ADD CONSTRAINT `InvoiceLine_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `InvoiceLineAllowanceCharge`
--
ALTER TABLE `InvoiceLineAllowanceCharge`
  ADD CONSTRAINT `InvoiceLineAllowanceCharge_ibfk_1` FOREIGN KEY (`InvoiceLinePriceID`) REFERENCES `InvoiceLinePrice` (`ID`);

--
-- Constraints for table `InvoiceLineItem`
--
ALTER TABLE `InvoiceLineItem`
  ADD CONSTRAINT `InvoiceLineItem_ibfk_1` FOREIGN KEY (`LineID`) REFERENCES `InvoiceLine` (`ID`);

--
-- Constraints for table `InvoiceLinePrice`
--
ALTER TABLE `InvoiceLinePrice`
  ADD CONSTRAINT `InvoiceLinePrice_ibfk_1` FOREIGN KEY (`LineID`) REFERENCES `InvoiceLine` (`ID`);

--
-- Constraints for table `InvoiceLineTaxCategory`
--
ALTER TABLE `InvoiceLineTaxCategory`
  ADD CONSTRAINT `InvoiceLineTaxCategory_ibfk_1` FOREIGN KEY (`InvoiceLineItemID`) REFERENCES `InvoiceLineItem` (`ID`);

--
-- Constraints for table `InvoiceLineTaxScheme`
--
ALTER TABLE `InvoiceLineTaxScheme`
  ADD CONSTRAINT `InvoiceLineTaxScheme_ibfk_1` FOREIGN KEY (`InvoiceLineTaxCategoryID`) REFERENCES `InvoiceLineTaxCategory` (`ID`);

--
-- Constraints for table `InvoiceLineTaxTotal`
--
ALTER TABLE `InvoiceLineTaxTotal`
  ADD CONSTRAINT `InvoiceLineTaxTotal_ibfk_1` FOREIGN KEY (`LineID`) REFERENCES `InvoiceLine` (`ID`);

--
-- Constraints for table `LegalMonetaryTotal`
--
ALTER TABLE `LegalMonetaryTotal`
  ADD CONSTRAINT `LegalMonetaryTotal_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `PaymentMeans`
--
ALTER TABLE `PaymentMeans`
  ADD CONSTRAINT `PaymentMeans_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`),
  ADD CONSTRAINT `PaymentMeans_ibfk_2` FOREIGN KEY (`AccountingPartyID`) REFERENCES `AccountingParty` (`ID`);

--
-- Constraints for table `RowsNotRequired`
--
ALTER TABLE `RowsNotRequired`
  ADD CONSTRAINT `fk_invoicetype` FOREIGN KEY (`InvoiceTypeCode`) REFERENCES `InvoiceType` (`InvoiceTypeCode`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Constraints for table `Signature`
--
ALTER TABLE `Signature`
  ADD CONSTRAINT `Signature_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);

--
-- Constraints for table `TaxSubCategory`
--
ALTER TABLE `TaxSubCategory`
  ADD CONSTRAINT `TaxSubCategory_ibfk_1` FOREIGN KEY (`TaxSubTotalID`) REFERENCES `TaxSubTotal` (`ID`);

--
-- Constraints for table `TaxSubCategoryScheme`
--
ALTER TABLE `TaxSubCategoryScheme`
  ADD CONSTRAINT `TaxSubCategoryScheme_ibfk_1` FOREIGN KEY (`TaxSubCategoryID`) REFERENCES `TaxSubCategory` (`ID`);

--
-- Constraints for table `TaxSubTotal`
--
ALTER TABLE `TaxSubTotal`
  ADD CONSTRAINT `TaxSubTotal_ibfk_1` FOREIGN KEY (`TaxTotalID`) REFERENCES `TaxTotal` (`ID`);

--
-- Constraints for table `TaxTotal`
--
ALTER TABLE `TaxTotal`
  ADD CONSTRAINT `TaxTotal_ibfk_1` FOREIGN KEY (`InvoiceID`) REFERENCES `Invoice` (`ID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
-- --------------------------------------------------------

--
-- Table structure for table `SubmissionLog`
-- Records every submission attempt to a ZATCA gateway
--

CREATE TABLE `SubmissionLog` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `InvoiceID` varchar(50) NOT NULL,
  `InvoiceUUID` varchar(50) DEFAULT NULL,
  `InvoiceHash` varchar(255) DEFAULT NULL,
  `Environment` varchar(20) NOT NULL DEFAULT 'sandbox',
  `Endpoint` varchar(120) DEFAULT NULL,
  `HTTPStatus` int DEFAULT NULL,
  `ZATCAStatus` varchar(20) DEFAULT NULL,
  `ClearanceStatus` varchar(20) DEFAULT NULL,
  `ReportingStatus` varchar(20) DEFAULT NULL,
  `RequestJSON` longtext,
  `ResponseJSON` longtext,
  `ErrorSummary` text,
  `SubmittedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  KEY `idx_invoice_id` (`InvoiceID`),
  KEY `idx_uuid` (`InvoiceUUID`),
  KEY `idx_submitted_at` (`SubmittedAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
