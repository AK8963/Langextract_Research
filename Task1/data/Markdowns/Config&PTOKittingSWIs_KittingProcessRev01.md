| CONFIDENTIAL INFORMATION  |    |           |      |      |              |                    |
|---------------------------|----|-----------|------|------|--------------|--------------------|
| WORK INSTRUCTIONS         |    |           |      |      |              |                    |
| PTO<br>KITTING<br>PROCESS |    |           |      |      |              |                    |
| Work Instruction No.      |    |           |      |      |              |                    |
| Revision No.              | 01 | Site Code | W103 | Page | 1<br>4<br>OF | Zebra Technologies |

### 1. OVERVIEW

This instruction provides an overview of the entire PTO Kitting process within the Zebra Kenosha DC. Please see the attached SWIs for instructions on specific functions; refer to the [Kitting Process Flow.](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200016A8C712D8402748968B56F4E0369F2E&id=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s%2FKenosha%20%2D%20Outbound%20Process%20%2D%20PTO%20Orders%20v1%2E1%2Epdf&parent=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s)

# 2. STAGING

- **1.** Once the Picking team has picked the product, it must be physically moved to the PTO Kitting Drop-Zone area, which will trigger Oracle MWA to print a Pick Drop Audit Label.
- **2.** Once the last drop of an order has occurred, the system will generate a PCR. The Picker will then verify that the LPN's/Quantity is correct.
  - ✓ If the check has not passed, please escalate to Lead/Supervisor.
- **3.** The PCR will be collected by the Kitting Lead, who confirms the locations of the drops as well as the quantity.
  - ✓ The lead will write the locations on the PCR in pen for the Kitting Team.
- **4.** The lead will either assign specific deliveries to Kitting Stations or place the PCR on top of the order, allowing the Stager to retrieve their order.

### 3. WORKSTATION SETUP

- **1.** Before any kitting can begin, the workstation must be appropriately configured to ensure that Kitting can be completed as efficiently as possible. Please reference [PTO Workstation Set Up.](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/SWI)
  - A) The process is designed to allow users to scan barcodes for all actions required to create a Kit or Overpack; the following items must be present.
    - ✓ Two PC Displays
    - ✓ Two printers
    - ✓ Barcodes (Validate and Close, packing station #, Validate/Close Overpack LPN)
    - ✓ Barcode Scanner
    - ✓ Fixed Industrial Scanner
- **2.** The station should also contain a sheet containing two barcodes (zDss/Oracle).
  - ✓ The Oracle barcode is applicable for Kitting Associates.
- **3.** The top-rack line, closest to the monitor, should be used for empty cartons; all the other cartons or bins for product go where the associate sees fit.

| CONFIDENTIAL INFORMATION  |    |           |      |      |              |                    |
|---------------------------|----|-----------|------|------|--------------|--------------------|
| WORK INSTRUCTIONS         |    |           |      |      |              |                    |
| PTO<br>KITTING<br>PROCESS |    |           |      |      |              |                    |
| Work Instruction No.      |    |           |      |      |              |                    |
| Revision No.              | 01 | Site Code | W103 | Page | 2<br>4<br>OF | Zebra Technologies |

# 4. BACK-END

- **1.** The kitting station should ideally contain three associates, the first being the 'Stager', who gathers all the LPNs associated with that order in the staging area.
- **2.** The Stager brings the LPNs to the assigned Kitting area, along with cartons that are either pre-formed or formed by the Backer.
- **3.** Before the product and cartons are loaded into the Kitting racks, the Stager will do a count of the product.
  - A) Using the PCR, verify that the 'Picked Quantity' matches the present quantity.
  - B) Determine which product can be loaded into the racking with the cartons it came in, versus placing it into separate bins.
    - ✓ If loading product into bins, perform an additional count of the picked product to ensure the quantity is correct.
- **4.** The Stager will cut open the cartons and load the product into the racking.
  - C) Once enough product has been loaded into the racking, the Splitter can begin its process, even if the Backer is still loading.
    - ✓ If any product remains, please return it to the Picking Supervisor along with the Pick Ticket so that it may be reprocessed.
- **5.** Additionally, the Stager will be responsible for ensuring that the Splitters and Packers have enough cartons to complete the Kitting order, including cartons used for the Overpack.
  - ✓ The Stager will also be responsible for cleaning and sorting the back area as needed, which includes removing any empty cartons and preparing for the following order.

### 5. SPLITTING

- **1.** Before any Kitting, Splitting or Consolidating can take place, the PCR should be inspected to ensure that no Country of Origin (COO) is left with 'XX'.
  - A) Please bring to the attention of Leads/Supervisor and reference the following SWIs: [Updating The Country of](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200016A8C712D8402748968B56F4E0369F2E&id=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FOutbound%20SWI%27s%2FWI%20%2D%20Outbound%20%2D%20Updating%20COO%20v1%2E0%2Epdf&parent=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FOutbound%20SWI%27s)  [Origin For A Delivery](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200016A8C712D8402748968B56F4E0369F2E&id=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FOutbound%20SWI%27s%2FWI%20%2D%20Outbound%20%2D%20Updating%20COO%20v1%2E0%2Epdf&parent=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FOutbound%20SWI%27s) and [Country of Origin Validation.](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/SWI)
- **2.** Two applications are needed to pack the material into Kits successfully: Oracle ERP/MWA, along with the station's printer.
  - ✓ Please ensure that the 'H-File' is enabled.
- **3.** The Splitter will then want to consolidate all the LPNs associated with the order into one single LPN (Parent LPN). Reference [LPN Consolidate After LPN Picks.](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/SWI)

| CONFIDENTIAL INFORMATION  |    |           |      |      |              |                    |
|---------------------------|----|-----------|------|------|--------------|--------------------|
| WORK INSTRUCTIONS         |    |           |      |      |              |                    |
| PTO<br>KITTING<br>PROCESS |    |           |      |      |              |                    |
| Work Instruction No.      |    |           |      |      |              |                    |
| Revision No.              | 01 | Site Code | W103 | Page | 3<br>4<br>OF | Zebra Technologies |

- **4.** Once logged into the necessary application, please follow the SWI PTO [Kit Creation](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200016A8C712D8402748968B56F4E0369F2E&id=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s%2FWI%2D%20PTO%20%2D%20Kit%20Creation%20v1%2E0%2Epdf&parent=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s) to create the individual kits.
  - ✓ Once in LPN Split, ensure that the options Serial Triggered, Each Pack, and Kitting are selected under Packing Process in Packing Initialization.
- **5.** Once the kit's components have been scanned, validated, and closed, place the newly printed 'TXK' label neatly on the carton.

### 6. PACKING

- **1.** Like the Splitter, the associate who will be Packing will have Oracle ERP open at their station.
  - ✓ Verify that 'LPN Pack' is selected under the Packing Process.
- **2.** Once the Packers ERP screen is situated, please follow the instructions provided in the PTO [Overpack Creation](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200016A8C712D8402748968B56F4E0369F2E&id=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s%2FWI%2D%20PTO%20%2D%20Overpack%20Creation%20v1%2E1%2Epdf&parent=%2Fsites%2FKenoshaDistributionCenter%2FShared%20Documents%2FSWI%27s%2FConfig%20%26%20PTO%20Kitting%20SWI%27s) SWI.
- **3.** Once the Overpack Carton is full and the LPN is closed, a 'TXB' label should be printed.
  - ✓ Check the PCR for DG instructions, apply the corresponding DG label, if applicable, on the carton, along with the TXB.
- **4.** Ensure that the proper amount of dunnage is added to the Overpack carton.
- **5.** The final step would be to merge the LPNs and remove the Parent-Child link.
  - ✓ Ensure Label is printed before anything is merged-up.

### 7. STAGE MOVING

- **1.** Once enough Overpack cartons have been created, the entire pallet must be Stage Moved before another Overpack carton can be made, as described in SWI [Stage Move.](https://zebra.sharepoint.com/sites/KenoshaDistributionCenter/Shared%20Documents/SWI)
- **2.** Continue with the stage moving process for each Overpack created for the Delivery Order.
  - A) 'Stage Move' locators are the locators assigned to the Staging Lanes.
    - ✓ PTO Kitting uses the subinventory 'CVS' for TXK/TXB/TX4P.
- **3.** If a Delivery Order is larger than two pallets/25 cases, it will have to be consolidated into a 'TX4P'

| CONFIDENTIAL INFORMATION                |                      |                    |  |  |  |
|-----------------------------------------|----------------------|--------------------|--|--|--|
| WORK INSTRUCTIONS                       |                      |                    |  |  |  |
| PTO<br>KITTING<br>PROCESS               |                      |                    |  |  |  |
| Work Instruction No.                    |                      |                    |  |  |  |
| Revision No.<br>01<br>Site Code<br>W103 | Page<br>4<br>4<br>OF | Zebra Technologies |  |  |  |

# 8. REFERENCES

| Document # | Document Title                                |  |  |  |  |  |
|------------|-----------------------------------------------|--|--|--|--|--|
|            | PTO Workstation Set Up                        |  |  |  |  |  |
|            | Kitting Process Flow                          |  |  |  |  |  |
|            | Updating The Country of Origin For A Delivery |  |  |  |  |  |
|            | Country of Origin Validation                  |  |  |  |  |  |
|            | LPN Consolidate After LPN Picks               |  |  |  |  |  |
|            | PTO –<br>Overpack Creation                    |  |  |  |  |  |
|            | Stage Move                                    |  |  |  |  |  |
|            | PTO –<br>Kit Creation                         |  |  |  |  |  |

### 9. REVISION HISTORY

The following table lists all revisions (including the original document) to this procedure, the date, and the reason for the revision.

| Rev. | Rev. Date  | Description of Change | Revised By  |
|------|------------|-----------------------|-------------|
| 01   | 06/12/2025 | Original issue        | V.<br>Savic |