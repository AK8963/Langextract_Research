# Confidential Information

| WORK INSTRUCTIONS<br>BATTERY MANAGEMENT TESTING |                   |      |         |                    |
|-------------------------------------------------|-------------------|------|---------|--------------------|
| Work Instruction No.                            |                   |      |         |                    |
| 01<br>Revision No.                              | WI03<br>Site Code | Page | 1 OF 12 | Zebra Technologies |

## 1. **OVERVIEW**

This document describes the steps required to test battery inventory to successfully maintain a battery management program and avoid shipping expired batteries to customers. Batteries shall be subjected to two types of testing: first, a voltage measurement test, and a 2nd test, a capacity test run by the Cadex battery tester will be needed if the battery fails the first test. Battery Lots shall be selected for testing under OB-WA-04- TX4

## 2. **VOLTAGE TESTING**

- ✓ BEFORE TESTING: Please go to EVMAgile and pull the following file: PD-006437-02 Copy and Overwrite this file in the following path: "C:\mtp\Site\_Ne\_sch\Projects\BAT\_TEST".
- 1. Open MTP using the MTP.exe file on the desktop.

![](_page_0_Picture_7.jpeg)

2. Login as an administrator using the password "**03ojdidit**".

![](_page_0_Picture_9.jpeg)

- 3. You will see the screen below. Enter the information highlighted in yellow boxes.
  - Operator Name Here enter TEST
  - Ensure the Simulate CA box is checked.
  - Change Parametrics to Do not upload.

![](_page_0_Picture_14.jpeg)

4. Click on the black arrow button on the right for the test to begin.

![](_page_0_Picture_16.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

| WORK INSTRUCTIONS<br>BATTERY MANAGEMENT TESTING            |                    |
|------------------------------------------------------------|--------------------|
| Work Instruction No.                                       |                    |
| 01<br>WI03<br>2 OF 12<br>Revision No.<br>Site Code<br>Page | Zebra Technologies |

5. If you see the error shown below, please refer to *Tracknum Error Handling***.**

![](_page_1_Picture_2.jpeg)

- 6. If no Test Error, proceed with the testing. Throughout the test, you will see pop messages asking you to enter certain information.
- 7. At the first pop-up box enter the Storage Location that the battery lot came from in inventory then click Enter.

![](_page_1_Picture_5.jpeg)

8. At the 2nd pop-up box enter the Lot Part Number. Usually, this information can be scanned. If there is no barcode on these items, the information might be present in text form only and must be keyed in. Scan or key in and press Enter. If the Lot Part Number is not available, please enter the Manufacturing date instead.

![](_page_1_Picture_7.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

![](_page_2_Figure_0.jpeg)

9. At the 3rd pop-up enter the number of batteries in the lot.

✓ The number of batteries to test is calculated using this number of batteries.

![](_page_2_Picture_3.jpeg)

10.At the 4th pop-up box will ask you to click the cell type of the battery lot being tested.

![](_page_2_Figure_5.jpeg)

![](_page_2_Figure_6.jpeg)

11.The 5th pop-up box will ask you to indicate whether the batteries you are testing have labels containing a barcode.

![](_page_2_Picture_8.jpeg)

✓ Make the applicable selection.

# 3. **SCANNABLE OPTION PATH**

1. If the battery contains only 1 barcode scan it. If there are two barcodes, first scan the one associated with "ID", and ensure SN and date are valid. (see **APPENDIX B Figures D, E and F) in Doc OB-TE-01**

![](_page_2_Picture_12.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

![](_page_3_Figure_0.jpeg)

![](_page_3_Figure_1.jpeg)

- 2. The operator will be asked to scan the PN barcode, which should be the 2nd available barcode.
  - ✓ If PN barcode is not available, manually look for this information and key it in.
- 3. The tester has a built-in safeguard to automatically detect good vs bad barcode IDs but as a safety precaution it asks the operator if the information is correct

![](_page_3_Picture_5.jpeg)

![](_page_3_Picture_6.jpeg)

![](_page_3_Picture_7.jpeg)

*The pack date does not make sense.*

✓ The operator should be able to confirm that the information in the pop-up is correct by comparing it to the text on the appropriate battery label. (See one of APPENDIX B Figures S, I, A, B, C, D, E or F).

If such text is not available on the label, please decide if the pop-up information appears correct, i.e.,

- There should be no symbols,
- The pack date is a valid date format,
- The part number and serial number appear reasonable.
- 4. Click "Yes' or "No" on the pop-up.

If you select Yes, the information is correct, pop-ups for later batteries will ask you only to scan the battery's barcodes.

✓ The program will automatically check to confirm that all the part numbers and dates are the same and the serial numbers are different. If any of this is not correct, the program will restart the entry process from the last battery entered.

If you choose No, the operator must enter the required information manually as described in the Manual Option Path.

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

| WORK INSTRUCTIONS<br>BATTERY MANAGEMENT TESTING |                 |                    |
|-------------------------------------------------|-----------------|--------------------|
| Work Instruction No.                            |                 |                    |
| 01<br>WI03<br>Revision No.<br>Site Code         | 5 OF 12<br>Page | Zebra Technologies |

# 4. **MANUAL ENTRY PATH**

- **1.** In case you are dealing with a battery label without a barcode, you will be asked to key in the Battery Part Number (not the orderable PN). Enter the PN and click enter.
  - ✓ If PN is not available, click the "NA-Stop Test" button and escalate the problem to your supervisor. The test will end.

![](_page_4_Picture_4.jpeg)

- **2.** If you are proceeding with the test, a 2 nd pop-up box requesting the Battery Serial Number to be entered will displayed. If the serial number is available enter it, if not available click the "Skip" button.
  - ✓ If skipped, a temporary serial number will be assigned to each battery for tracking purposes.

![](_page_4_Picture_7.jpeg)

**3.** The 3rd pop-up box will request you to enter the Pack Date. The pack date barcode can be found on the battery pack bag holding the battery or the battery pack box that contains the bag (see **Appendix B - Figures A and B of Doc OB-TE-01**). If it's not available in text or barcode form anywhere, click the "Skip" button.

![](_page_4_Picture_9.jpeg)

![](_page_4_Picture_10.jpeg)

![](_page_4_Picture_11.jpeg)

**Figure A Individual Box Label Figure B Battery Bag Label**

✓ For a quicker keyed-in entry, tab over after the month, day, and year entered. The information will need to be entered for each battery being tested, the information will be remembered from the previous entry, so ensure you verify before submitting.

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

![](_page_5_Figure_0.jpeg)

- 4. A check will be done for the Serial Number, Part Number, and Pack Date after each battery information is entered.
  - o If the Serial Number matches that of a previous battery entered, a message will be shown, see image below.
  - o If the Part Number or Pack date entered DOES NOT match the previous batteries entered a similar popup will be shown stating this issue.
  - o If any of these issues mentioned above occur, then the test will allow you to retry one time.
  - o If any of these issues happen again then the test will end.
    - ✓ If the operator fixes the issue the test will continue. You will get one retry per battery before the test ends.

![](_page_5_Picture_7.jpeg)

![](_page_5_Picture_8.jpeg)

![](_page_5_Picture_9.jpeg)

## 5. **ADAPTOR SELECTION**

**1.** After The Option Path selection is made (Scannable or Manual) and data is entered for the first battery to be tested, the test station will show a message telling the operator to get the adaptor that works for the battery being tested, which corresponds to the Part Number shown.

![](_page_5_Picture_12.jpeg)

- ✓ Unfortunately, because some batteries do not have scannable barcodes, the test cannot determine whether these are EVM or AIT.
- **2.** To find the correct adapter, the operator might need to look through both AIT and EVM documents to find the adaptor that corresponds to the battery part number.
  - ❖ EVM batteries, the document bsmodels.txt is attached to part number PD-006437-01 in EVM Agile. bsmodels.txt should be opened using Excel as a tab-delimited file. Locate the battery part number in the fourth column D. The adaptor part number can be found in the same row as column E. This adaptor shall be used both at this test station and, if Cadex testing is needed, at the Cadex battery capacity analyzer test station. The bsmodels.txt file will also be needed by Cadex. Its use is described in (Appendix A - Doc OB-TE-01)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

| WORK INSTRUCTIONS                                  |                 |                    |
|----------------------------------------------------|-----------------|--------------------|
| BATTERY MANAGEMENT TESTING<br>Work Instruction No. |                 |                    |
| 01<br>WI03<br>Revision No.<br>Site Code            | 7 OF 12<br>Page | Zebra Technologies |

o The adapters for EVM batteries will be the Cadex ones with this small cable attached. The green connector goes to the Cadex adapter and the banana cables to the test equipment Power Supply and Multi-meter.

![](_page_6_Picture_2.jpeg)

- ❖ AIT batteries, the "Serial Number Map" tab found in the spreadsheet stored under "Attachments" in document D10016195 in AIT Agile correlates battery part numbers with Zbatt adapter part numbers. Locate the battery part number in column A. The ZBatt Adapter part number can be found in the same row of either column L or M. This adaptor shall be used at this test station.
- o For AIT batteries, there is the Zbatt adapter. An example is found in the image below. In the lookup table for AIT batteries mentioned above, the Zbatt adapter which correlates to each specific battery can be found.
  - ✓ Please refer to the setup instructions in (Appendix C Doc OB-TE-01), for instructions on how these adapters should be connected.

![](_page_6_Picture_6.jpeg)

**3.** In some cases, AIT batteries, will also need to employ Cadex capacity test equipment. This will require different, Cadex-compliant battery adapters. The part numbers of these adapters can be found in bsmodels\_coder.txt, which reports to D10013896 in AIT Agile. The adapters' part numbers are found in the same manner as with the EVM bsmodels.txt file as specified above. The bsmodels.txt file will also be needed by Cadex. Its use is described in (Appendix A - Doc OB-TE-01)

**Commented [DJW1]:** Appendix D1

![](_page_7_Figure_0.jpeg)

**4.** After the proper connector has been identified, a pop-up will appear to confirm the battery is correctly attached to the adaptor. Click OK, to proceed.

![](_page_7_Picture_2.jpeg)

**5.** Once voltage testing is complete, remove the battery from the adaptor and place it on a table or other surface in a specific pattern. The pattern has 10 columns, but the number of rows depends on how many batteries are being tested in the lot. Start from the left position of the top row and place each battery after that on the right. After there are 10 batteries in a row, start a new row underneath. You will follow the same pattern with each battery to be tested, adding rows as needed.

![](_page_7_Picture_4.jpeg)

#### **Battery Placement Pattern**

✓ If the battery has failed the limit test of that specific cell type, the operator will see the message below.

![](_page_7_Picture_7.jpeg)

- **6.** Place a Yellow or Red sticker on that battery as an indicator of the failure.
- **7.** The testing station knows which Option Path was selected (Section 2 or 3). It will display the appropriate set of step pop-ups for use with the next battery to be tested.
- **8.** Having the proper adapter connected, it will skip asking you to select Scannable or Manual path and go directly to entering battery information.
- **9.** When the last battery to be tested is removed from the adaptor and placed in the pattern the station will display the pop-up below.

![](_page_7_Picture_12.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

| WORK INSTRUCTIONS                                          |                    |
|------------------------------------------------------------|--------------------|
| BATTERY MANAGEMENT TESTING                                 |                    |
| Work Instruction No.                                       |                    |
| 01<br>WI03<br>9 OF 12<br>Revision No.<br>Site Code<br>Page | Zebra Technologies |

- **10.** The system will display the test summary.
- **11.** If all the batteries pass the test will end and the lot will be accepted.

![](_page_8_Picture_3.jpeg)

![](_page_8_Picture_4.jpeg)

- ❖ Voltage tests identify batteries with extremely low voltages.
- ❖ Batteries with these voltages are shown in red on the following pop-up. (These are the same batteries that were, marked with the yellow or red stickers). They shall be removed and scrapped.
- ❖ Any batteries shown in green shall be tested by the Cadex battery analyzer, which will require the use of the correct battery adaptor.
- ❖ The tan boxes represent other batteries, which shall be returned to their original bags and boxes. The greyed boxes are void spaces - they don't represent anything.

![](_page_8_Picture_9.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

![](_page_9_Figure_0.jpeg)

✓ If there are batteries that require Cadex testing, the system will display the pop-up message below.

![](_page_9_Figure_2.jpeg)

- **12.** Depending on how many batteries failed, the test station will tell the operator how many are needed to be tested by the Cadex. The example above indicates six batteries failed, and 4 batteries were chosen to be tested using the Cadex. Up to 4 batteries can be tested in any lot. Press "OK" to proceed.
- **13.** The system will display the battery that needs to be tested in Cadex. All green highlighted batteries must be pulled from the battery set for testing before the test can be finished.

![](_page_9_Picture_5.jpeg)

**14.** Pull the battery to be woken up again to get a reading from the Cadex machine. This pop-up will appear after each battery to ensure that the battery in in the nest.

![](_page_9_Picture_7.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

![](_page_10_Figure_0.jpeg)

**15.** Place the battery back in the adaptor to be woken, after each battery is confirmed to be woken up, it can be removed, labeled, and placed aside for Cadex testing. Repeat for each battery that needs Cadex testing.

![](_page_10_Picture_2.jpeg)

**16.** Once all the batteries that need Cadex testing are confirmed and labeled, they should be brought over to the Cadex tester to be tested. (See Appendix A – OB-TE-01) for the Cadex test procedure.

![](_page_10_Picture_4.jpeg)

- **17.** After the Cadex testing is complete, record the Cadex capacity percentages (without the "%" sign) into the respective test field matching their SN as shown below.
  - ✓ Might need to utilize a sticky to record the percentages and then enter them in the system.

![](_page_10_Picture_7.jpeg)

- **18.** After all the percentages are entered click Submit.
- **19.** The operator will see another pop-up message, stating whether the lot passed or failed.

![](_page_10_Picture_10.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

| WORK INSTRUCTIONS<br>BATTERY MANAGEMENT TESTING |                  |                    |
|-------------------------------------------------|------------------|--------------------|
| Work Instruction No.                            |                  |                    |
| 01<br>WI03<br>Revision No.<br>Site Code         | 12 OF 12<br>Page | Zebra Technologies |

- **20.** If Lot failed, follow the instructions in OB-WA—04 that indicate the process for LOT testing failure. Reference OB-WA-04-TX4 for further instructions
- **21.** If LOT passed, place only the tan-colored batteries in their bags and boxes and prepare to return to inventory. Reference OB-WA-04-TX4 for further instructions.

## 6. **REFERENCES**

| Document #                     | Document Title                                     |  |
|--------------------------------|----------------------------------------------------|--|
| OB-TE-01_Rev2.pdf              | Battery Management Test Work Instruction           |  |
| OB-WA-04-TX4 8-<br>14-2023.pdf | TX4 Distribution Center Battery Management Process |  |

# 7. **REVISION HISTORY**

The following table lists all revisions (including the original document) to this procedure, the date, and the reason for the revision.

| Rev. | Rev. Date  | Description of Change | Revised By |
|------|------------|-----------------------|------------|
| 01   | 09/18/2023 | Original issue        | A.Cabrera  |