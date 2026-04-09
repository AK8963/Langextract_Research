| CONFIDENTIAL INFORMATION                |                      |                    |  |  |  |  |
|-----------------------------------------|----------------------|--------------------|--|--|--|--|
| WORK INSTRUCTIONS                       |                      |                    |  |  |  |  |
| HTS<br>REQUEST PROCESS                  |                      |                    |  |  |  |  |
| Work Instruction No.                    |                      |                    |  |  |  |  |
| 01<br>WI03<br>Revision No.<br>Site Code | 1<br>3<br>Page<br>OF | Zebra Technologies |  |  |  |  |

# 1. OVERVIEW

A Harmonized Tariff Schedule is a classification system in the US used to help determine customs duties to be paid on Imports. An HTS report is needed for LTLs over a value of \$2,500. An HTS Report for small parcel shipments is needed only upon request from the Freight Forwarder.

# 2. HTS REQUEST PROCESS

**1.** In Oracle run the HTS Report.

*Reference WI – Outbound – Generate HTS Report V1.0 work instructions.*

**2.** The report should look like the Excel workbook below.

|                 |                      | ٥                | 4                                        | ر          | U                     | I                 | 0        | 2                | 10    |
|-----------------|----------------------|------------------|------------------------------------------|------------|-----------------------|-------------------|----------|------------------|-------|
| H.S. Code Summa | ary List ZTC (       | ou               |                                          |            |                       |                   |          |                  |       |
|                 |                      |                  |                                          |            |                       |                   |          |                  |       |
|                 | Country of<br>Origin | Item             | Item Description                         | HTS Code   | Nett Weight in<br>Kgs |                   | Currency | Quantity         | ECCN# |
| 77637691        | ;CN                  | BTRY-MPP-EXT1-01 | Extended battery for ZQ51,ZQ52,ZQ61/ZQ61 | 8507600020 | 0.049999941           | 53.35             | USD      | 1                | EAR99 |
|                 |                      |                  |                                          |            | <b>Sum:</b> 0.05      | <b>Sum:</b> 53.35 |          | <b>Sum:</b> 1.00 |       |
|                 |                      |                  |                                          |            |                       |                   |          |                  |       |

**3.** Paste the Ultimate Consignee Type Box on the Excel workbook. As shown below.

| Commercial<br>Invoice Number | Country of<br>Origin | Item                      | Item Description                               | HTS Code   | Nett Weight in<br>Kgs | Sales Value of the<br>Product | Currency | Quantity  | ECCN# |
|------------------------------|----------------------|---------------------------|------------------------------------------------|------------|-----------------------|-------------------------------|----------|-----------|-------|
| 77637691                     | ;CN                  | BTRY-MPP-EXT1-01          | Extended battery for ZQ51,ZQ52,ZQ61/ZQ61 Plus, | 8507600020 | 0.049999941           | 53.35                         | USD      | 1         | EAR99 |
|                              |                      |                           |                                                |            | Sum: 0.05             | Sum: 53.35                    |          | Sum: 1.00 |       |
|                              |                      |                           |                                                |            |                       |                               |          |           |       |
|                              |                      | •                         | 1                                              |            |                       |                               |          |           |       |
|                              |                      | Ultimate Consig           | gnee Type                                      | 1          |                       |                               |          |           |       |
|                              |                      | Tax ID                    | 20545884                                       | 7          |                       |                               |          |           |       |
|                              |                      | Routed/Non-routed         | Non-Routed                                     | 7          |                       |                               |          |           |       |
|                              |                      | Related/Non-related       | Related                                        | 7          |                       |                               |          |           |       |
|                              |                      | Hazardous/Non-hazar       | Non-Hazardous                                  | 1          |                       |                               |          |           |       |
|                              |                      | If the freight doesn't re | NLR-033                                        | 7          |                       |                               |          |           |       |
|                              |                      |                           |                                                |            |                       |                               |          |           |       |

- **4.** The highlighted fields in the Ultimate Consignee box need to be updated according to the order final consignee.
- **5.** The Tax ID and the NLR number do not change.

| Ultimate Consignee Type                                      |                 |
|--------------------------------------------------------------|-----------------|
| Tax ID                                                       | 20545884        |
| Routed/Non-routed                                            | Non-Routed      |
| Related/Non-related                                          | Related         |
| Hazardous/Non-hazardous                                      | Non-Hazardous   |
| If the freight doesn't require a license<br>to ship then NLR | NLR-033         |
| Reseller, Customer, etc                                      | Direct Customer |

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

### **6.** Routed vs Non-Routed

**Routed**: Shipments where Zebra is not acting as the USPPI (U.S Principal Party in Interest) for export but working with assigned FF (Freight Forwarder) for our customers.

**Non-Routed**: Direct to Customer shipments.

## **7.** Related vs Non-Related

**Related**: Related company/Sister companies

*Ex: Z2Z Shipments.*

**Non-Related:** Non-Zebra Companies as final consignee

**8.** Hazardous or Non-Hazardous\*

**Haz**: Hazardous Material.

**Non-Haz**: Non-Hazardous Material

*\*Normally Zebra products are Non-Hazardous but if any question please reach out to GTC NALA group.*

**9.** Consignee Type

**Consignee Type:** Actual role of the final consignee.

- Direct Consumer
- Reseller
- Government Entity
- Other

*Ex: Z2Z is a Direct Consumer. AGIS is a Reseller.*

- **10.** Save the document but first change the document name and the file type.
- **11.** Document name Tracking- Delivery # + HTS Ex (DN ORD230361900 77637691 HTS)

![](_page_1_Figure_20.jpeg)

- **12.** File type click on the drop-down menu and select Excel Workbook.
- **13.** Send to Freight Forwarder along with the Packing List (PL) and Customs Invoice (CI)

![](_page_1_Figure_23.jpeg)

**14.** If the requester is only requesting the HTS report, only send the report.

# 3. REFERENCES

| Document # | Document Title                                    |  |  |  |  |
|------------|---------------------------------------------------|--|--|--|--|
|            | WI -<br>Outbound -<br>Generate HTS Report 1.0.pdf |  |  |  |  |

# 4. REVISION HISTORY

The following table lists all revisions (including the original document) to this procedure, the date, and the reason for the revision.

| Rev. | Rev. Date  | Description of Change | Revised By |  |
|------|------------|-----------------------|------------|--|
| 01   | 06/16/2016 | Original issue        | A.Cabrera  |  |