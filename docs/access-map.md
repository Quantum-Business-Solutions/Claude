# Access map

Key `10` (ECI e-automate) against `https://devclientsapi.ceojuice.com`.

| Status | Endpoint | Note |
| --- | --- | --- |
| 0 | `/api/MeterReadings/EquipmentMetersBySerial/{serialNumber}` | <urlopen error [Errno 104] Connection reset by peer> |
| 200 | `/api/Contact` |  |
| 200 | `/api/Contact/Recentchanges/{sinceTime}` |  |
| 200 | `/api/Contact/byCustomerNumber/{customerNumber}` |  |
| 200 | `/api/Contact/byEmail/{email}` |  |
| 200 | `/api/Contract/Recentchanges/{sinceTime}` |  |
| 200 | `/api/Contract/active` |  |
| 200 | `/api/Contract/active/customer/{customerNumber}` |  |
| 200 | `/api/Customer` |  |
| 200 | `/api/Customer/Countries` |  |
| 200 | `/api/Customer/PriceLevels` |  |
| 200 | `/api/Customer/Recentchanges/{sinceTime}` |  |
| 200 | `/api/Customer/States` |  |
| 200 | `/api/Customer/Terms` |  |
| 200 | `/api/Customer/{customerNumber}` |  |
| 200 | `/api/Equipment/AllActive` |  |
| 200 | `/api/Equipment/Recentchanges/{sinceTime}` |  |
| 200 | `/api/Equipment/byEquipmentNumber/{equipmentNumber}` |  |
| 200 | `/api/Equipment/bySerialNumber/{serialNumber}` |  |
| 200 | `/api/Invoice/Recentchanges/{sinceTime}` |  |
| 200 | `/api/Invoice/byInvoiceNumber/{invoiceNumber}` |  |
| 200 | `/api/Invoice/{id}` |  |
| 200 | `/api/Item/GetByItemNumber/{itemNumber}` |  |
| 200 | `/api/Item/Makes` |  |
| 200 | `/api/Item/ModelCategories` |  |
| 200 | `/api/Item/Models` |  |
| 200 | `/api/Item/Models/{modelId}/Meters` |  |
| 200 | `/api/Item/SearchByItemNumber/{itemNumber}` |  |
| 200 | `/api/KM/Id285/CallTypes` |  |
| 200 | `/api/KM/Id285/OpenCalls` |  |
| 200 | `/api/MeterReadings/EquipmentMetersByEqNo/{equipmentNumber}` |  |
| 200 | `/api/MeterReadings/MeterTypes` |  |
| 200 | `/api/PrintReleaf/customers` |  |
| 200 | `/api/SalesOrder/AllOpen` |  |
| 200 | `/api/SalesOrder/ByOrderId/{SOID}` |  |
| 200 | `/api/SalesOrder/ByOrderNumber/{orderNumber}` |  |
| 200 | `/api/SalesOrder/ByPurchaseOrderNumber/{poNumber}` |  |
| 200 | `/api/SalesOrder/OrderStatuses` |  |
| 200 | `/api/SalesOrder/OrderTypes` |  |
| 200 | `/api/SalesOrder/PriceLevels` |  |
| 200 | `/api/SalesOrder/Recentchanges/{sinceTime}` |  |
| 200 | `/api/SalesOrder/ShipMethods` |  |
| 200 | `/api/SalesOrder/Terms` |  |
| 200 | `/api/ServiceCall/AllOpen` |  |
| 200 | `/api/ServiceCall/ByCallId/{callId}` |  |
| 200 | `/api/ServiceCall/ByCallNumber/{callNumber}` |  |
| 200 | `/api/ServiceCall/CallTypes` |  |
| 200 | `/api/ServiceCall/CancelCodes` |  |
| 200 | `/api/ServiceCall/NoteTypes` |  |
| 200 | `/api/ServiceCall/OnHoldCodes` |  |
| 200 | `/api/ServiceCall/Priorities` |  |
| 200 | `/api/ServiceCall/ProblemCodes` |  |
| 200 | `/api/ServiceCall/Recentchanges/{sinceTime}` |  |
| 200 | `/api/ServiceCall/RepairCodes` |  |
| 200 | `/api/ServiceCall/SLACodes` |  |
| 200 | `/api/Test` |  |
| 400 | `/api/PrintReleaf/customers/{customerId}` | {"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validati |
| 403 | `/api/Branch` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/CallTypes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/CancelCodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/Countries` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/MeterTypes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/NoteTypes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/OnHoldCodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/OrderStatuses` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/OrderTypes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/PriceLevels` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/Priorities` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/ProblemCodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/RepairCodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/SLACodes` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/ShipMethods` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/States` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/Terms` | Status Code: 403; Forbidden |
| 403 | `/api/ListsAndCodes/{key}` | Status Code: 403; Forbidden |
| 403 | `/api/Process/GetProcessOutput` | Status Code: 403; Forbidden |
| 403 | `/api/User/SalesReps` | Status Code: 403; Forbidden |
| 403 | `/api/User/Technicians` | Status Code: 403; Forbidden |
| 403 | `/api/User/Users` | Status Code: 403; Forbidden |
| 404 | `/api/KM/Id285/Call/{externalRef}` | {"type":"https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status": |

0: 1, 200: 55, 400: 1, 403: 23, 404: 1

Claims granted (18):
  - APInvoice_Create
  - Contacts_Create
  - Contacts_Read
  - Contacts_Update
  - Contracts_Read
  - Customers_Read
  - Customers_Update
  - Equipment_Read
  - Inventory_Read
  - Inventory_Update
  - Invoices_Read
  - MeterReadings_Read
  - MeterReadings_Update
  - PrintReleaf_Read
  - SalesOrders_Read
  - SalesOrders_Update
  - ServiceCalls_Read
  - ServiceCalls_Update
