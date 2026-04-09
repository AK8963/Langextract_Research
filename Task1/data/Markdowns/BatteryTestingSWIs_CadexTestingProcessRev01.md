# Confidential Information

| WORK INSTRUCTIONS<br>CADEX TESTING<br>PROCESS |                   |                      |                    |
|-----------------------------------------------|-------------------|----------------------|--------------------|
| Work Instruction No.                          |                   |                      |                    |
| 01<br>Revision No.                            | WI03<br>Site Code | 1<br>7<br>Page<br>OF | Zebra Technologies |

# 1. OVERVIEW

The automated voltage measurement tool employed a Cadex adapter to test battery voltages. The tool indicates anywhere from none to four batteries must be Cadex-tested.

## 2. CADEX TESTING (APPENDIX A1)

- **1.** Confirm that a type A to type B USB cable interconnects a PC to the Cadex C7400-C battery analyzer.
- **2.** Cycle the power to the analyzer.
- **3.** Test Confirm that V1.10 /1.01 and \*\* DIAGNOSTICS Passed \*\* are displayed. If something different is shown, please escalate the problem.
- **4.** Confirm that a sticker has been affixed to the analyzer stating that the ZebraCapTest cpg was installed. If there is no sticker, follow **ZebraCapTest.cpg (Appendix A2)**.
- **5.** Obtain and store on the Cadex PC the file bsmodels.txt found under the Attachments pull-down which reports to PD-006437-01 in EVM Agile. Also, obtain and store the file bsmodels\_ccoder.txt which reports to D10013896 in ATS Agile.
  - ✓ These files are periodically updated by Zebra Engineering and must be imported into BatteryShop each time a battery lot is tested.
- **6.** Launch Cadex BatteryShop

![](_page_0_Picture_12.jpeg)

**7.** Select HELP near the top of the screen and then ABOUT, the following pop-up will display.

![](_page_0_Figure_14.jpeg)

**8.** Click on Database then Battery Models it will display the Battery Models.

![](_page_1_Figure_1.jpeg)

![](_page_1_Figure_2.jpeg)

- **9.** Select the first model row, hold down the shift key, and scroll to the end of the list.
- **10.** All models will be highlighted, click on the delete icon on the screen.
  - ✓ Some Cadex machines could retain old incorrect files for which there is no replacement yet available, therefore deletion is required.

![](_page_1_Picture_6.jpeg)

- **11.** When the process is complete the screen will be blank.
- **12.** Click on the import icon at the top of the screen.

![](_page_2_Picture_2.jpeg)

**13.** Navigate to where the bsmodels.txt is stored (see below), select the file, and click OPEN.

![](_page_2_Picture_4.jpeg)

**14.** The screen below will appear. Click OK

![](_page_2_Picture_6.jpeg)

- **15.** Repeat the Import process for the bsmodels\_ccoder.txt file. Click OK again. The Information pop-up will disappear.
- **16.** Click CLOSE in the upper right-hand corner.
- **17.** Select Connect button.

![](_page_3_Picture_3.jpeg)

**18.** An icon will appear in the upper left-hand corner. The number of white vertical bars in the icon should match the number of installed adapters.

![](_page_3_Picture_5.jpeg)

**19.** Select Analyze Battery

![](_page_3_Picture_7.jpeg)

**20.** The screen below will appear.

![](_page_4_Figure_1.jpeg)

- **21.** In the Battery Model window near the top left, type the part number (not the orderable part number) to be tested. Alternatively, scroll through the list and select the model you need.
  - ✓ Ensure the selected model matches the battery part number and there is a green text on the bottom of the window.

![](_page_4_Figure_4.jpeg)

**22.** If you are testing more than one battery, ensure the Analyzer Mode is set to Batch. Otherwise, set it to Single.

![](_page_5_Picture_0.jpeg)

- **23.** Insert the batteries into the adapters. The test(s) should start up and the green text on the Analyzer Battery window will change to yellow (showing the port(s) and station(s) used.)
  - A) Connect the Red Lead to the Positive pad on the battery.
  - B) Connect the Black Lead to the Negative pad on the battery.

![](_page_5_Picture_4.jpeg)

- ✓ Upon connecting the batteries to the adaptors, the test will start immediately.
- **24.** When the test is completed. The BatteryShop unit icon will show green.

![](_page_5_Picture_7.jpeg)

*This document contains proprietary information which is the exclusive property of Zebra Technologies Corp.*

- **25.** The C7400's will show a green "READY" LED and the word "FINISHED" and the battery voltage in the associated adapter on the LCD.
  - ✓ Only one station is shown here because in this case, only one adapter was installed.
- **26.** Select the active station, the display will indicate a percentage.
  - ✓ Write the percentage on a sticky note and place it on the battery that was tested. The percentage will need to be recorded.

![](_page_6_Picture_4.jpeg)

**27.** Return all tested batteries with their sticky labels to the automated voltage test tool to record the percentages.

This completes the Cadex Testing.

## 3. REFERENCES

| Document # | Document Title                       |  |  |
|------------|--------------------------------------|--|--|
|            | ZebraCap Test Installation Rev01.pdf |  |  |
|            | BatteryShop Installation Rev01.pdf   |  |  |

## 4. REVISION HISTORY

The following table lists all revisions (including the original document) to this procedure, the date, and the reason for the revision.

| Rev. | Rev. Date | Description of Change | Revised By |
|------|-----------|-----------------------|------------|
| 01   | 09/19/23  | Original issue        | A.Cabrera  |