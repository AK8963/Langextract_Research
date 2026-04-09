# Confidential Information

| WORK INSTRUCTIONS<br>TX4<br>DC<br>BATTERY MANAGEMENT<br>PROCESS |                    |
|-----------------------------------------------------------------|--------------------|
| Work Instruction No.                                            |                    |
| 01<br>WI03<br>1<br>3<br>Revision No.<br>Site Code<br>Page<br>OF | Zebra Technologies |

# 1. OVERVIEW

This procedure outlines the process to periodically purge battery stock from inventory and perform testing to ensure the product in stock meets quality standards before shipping.

# 2. INBOUND

- **1.** When Stock Rotation or Shipment of batteries is received, check the Manufacture Date (MFD).
  - ✓ The Inbound or RMA team will need to record the MFD in the Report.
- **2.** If not older than 1 year put away/move to a pickable location.
- **3.** If older than 1 year, perform a stage move to Rework2 (REW2) physically and systematically.
- **4.** The planner will raise a WIP job + pick release for battery testing.
- **5.** The picker will pick and drop the material physically and systematically in the LS locator in the Reconfiguration area RMF1.
- **6.** The reconfiguration operator will physically move the WIP job from RMF1 to the Battery testing area.
- **7.** Perform Testing according to **Battery Management Testing Rev01**
  - ✓ If there are test application issues, please see VAS Engineers.
- **8.** If the Lot passes, the testing stock will be moved back to inventory.
- **9.** The re-configuration team will place the passed battery lot in the put-away location.
- **10.** Inbound will physically and systematically transfer the batteries back to inventory.
- **11.** If the Lot fails:
  - Due to low voltage, then it will be scrapped,
  - The batteries that indicate further testing will be tested in CADEX.
  - If it continues to fail, it will be moved to be scrapped.
- **12.** Quality will obtain disposition once in the area.
  - ✓ SLA is 20 days.

# 3. BATTERY MANAGEMENT PROCESS

- **1.** Quality will run a monthly report on aging batteries from OAC.
- **2.** Quality will determine impacted battery lots (according to OB-WA-04).
  - ✓ Batteries 1-2 years old and 2-2.9 years old will be transferred to REW2.
  - ✓ The table below will determine the number of batteries to test.

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

✓ Inventory Control will Pick the number of batteries to test based on the lot size and transfer them to REW2 sub-inventory.

| Lot Size   | Batteries to Test |  |
|------------|-------------------|--|
| <30        | Entire Lot        |  |
| 31-80      | Entire Lot        |  |
| 81-1200    | 80                |  |
| 1201-3200  | 125               |  |
| 3201-10000 | 200               |  |
| 10001+     | 315               |  |

- **3.** Quality to work with the VAS Supervisor a month before to coordinate the material move.
- **4.** The planner will raise a WIP job + pick release for battery testing.
- **5.** The picker will pick and drop the material physically and systematically in the LS locator in the Reconfiguration area RMF1.
  - ✓ The sample material MUST be picked from the same location.
- **6.** A Reconfiguration operator will run the labor load report to verify all material has been dropped.
- **7.** The Re-Config operator will perform the test according to **Battery Management Testing Rev01**
- **8.** Test results will be automatically recorded in Splunk.
- **9.** If the Lot passes the testing stock will be moved back to inventory.
- **10.** The re-configuration team will place the passed battery lot in the put-away location.
- **11.** The reconfiguration team will provide the locator and inbound will physically and systematically transfer the batteries to the same locator they were originally pulled from.
- **12.** If the Lot fails:
  - Due to low voltage, then it will be scrapped,
  - The batteries that indicate further testing will be tested in CADEX.
  - If it continues to fail, it will be moved to be scrapped.
- **13.** Quality will obtain disposition once in the area.
  - ✓ SLA is 20 days.

# 4. REFERENCES

| Document # | Document Title                                             |  |
|------------|------------------------------------------------------------|--|
| OB-TE-01   | Battery Management Test Work Instruction OB-TE-01_Rev2.pdf |  |
|            | Battery Management Testing Rev01.pdf                       |  |
|            | Cadex Testing Process Rev01.pdf                            |  |
|            | BatteryShop Installation Rev01.pdf                         |  |
|            | ZebraCap Test Installation Rev01.pdf                       |  |
|            | Tracknum Error Handling Rev01.pdf                          |  |

# 5. REVISION HISTORY

The following table lists all revisions (including the original document) to this procedure, the date, and the reason for the revision.

| Rev. | Rev. Date | Description of Change | Revised By |
|------|-----------|-----------------------|------------|
| 01   | 09/19/23  | Original issue        | A.Cabrera  |