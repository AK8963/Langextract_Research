# Confidential Information

|                                                                                               |                                                                      |                                                                                                                                                     | Document<br>Number    |                  | OB-TE-01                              |                |  |
|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------|------------------|---------------------------------------|----------------|--|
|                                                                                               |                                                                      | Revision                                                                                                                                            |                       | 6.7C             |                                       |                |  |
| Battery Management Test Work Instruction<br>Title:                                            |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
|                                                                                               |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| Author                                                                                        |                                                                      |                                                                                                                                                     |                       | Christopher Paul |                                       |                |  |
| BUSINESS UNIT:<br>AIT<br>EVM<br>ALL                                                           |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
|                                                                                               |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| LOCATION(S):<br>ALL (Global)<br>NALA<br>APAC<br>EMEA                                          |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| *Refer to Scope for possible limitations and/or elaborations relating to a selected region(s) |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| DISTRIBUTION                                                                                  |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| REVISION HISTORY                                                                              |                                                                      |                                                                                                                                                     |                       |                  |                                       |                |  |
| Rev                                                                                           | Description for<br>change<br>(Describe impact on<br>process/product) |                                                                                                                                                     | Process impact / risk |                  | Author                                | Date           |  |
| 1                                                                                             | Battery<br>Management Test<br>Process                                |                                                                                                                                                     |                       |                  | Pablo Uresti                          | 01-Jun<br>2018 |  |
| 6.7C                                                                                          | Major revision                                                       | Correction to existing procedure which<br>requires battery voltage measurement, but<br>specifies neither battery quantity nor pass/fail<br>criteria |                       |                  | Christopher<br>Paul, Jesse<br>Abruzzo |                |  |

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

# **PURPOSE**

This document describes the steps required to test battery inventory to successfully maintain a battery management program and avoid shipping expired batteries to customers.

#### **SCOPE**

This procedure is applicable to Zebra Technologies worldwide distribution centers and defines the requirements for testing inventory. It applies to both EVM and ATS lithium-ion batteries but excludes coin cells and other battery technologies.

#### **REFERENCES**

Distribution Center Battery Management Process OB-WA-04

### **DEFINITIONS / ABBREVIATIONS / ACRONYMS (optional)**

DC: Distribution Center

AIT: Asset Identification and Tracking including printers, printing supplies and location

solutions.

EVM: Enterprise Visibility and Mobility including mobile computers, and scanning solutions

### Date Code:

Defines the Manufacture date of the battery pack on the battery pack labels and the labels on the of the various packages enclosing the pack. Date codes are in various formats (see Appendix A, document OB-WA-04.)

BL:

Battery Lot, a group of batteries sharing the same manufacturer, part number and date of manufacture. Regarding part number, for EVM batteries, this refers to the part number on the battery label which is *NOT* the orderable, Inventory part number. It is always human-readable and is also encoded in a barcode unless there is inadequate space available on the label.

# **RESPONSIBILITIES**

Zebra Engineering is responsible for maintaining Cadex battery data files. The testing site test engineer is responsible for the enforcement of this document.

## **TESTING**

Batteries shall be subjected to two types of testing: a voltage measurement test which is executed first, followed by a capacity test run by the Cadex battery tester. Battery Lots shall be selected for testing in accordance with OB-WA-04.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

#### Test Station Procedure:

- a. BEFORE TESTING: Please go to EVMAgile and pull the following file: PD-006437-02 Copy and Overwrite this file in the following path: "C:\mtp\Site\_Ne\_sch\Projects\BAT\_TEST".
  - 1.
- a. Open MTP using the MTP.exe file on the desktop.

![](_page_2_Picture_4.jpeg)

b. After opening, you must login as administrator using the password "03ojdidit".

![](_page_2_Picture_6.jpeg)

c. You will then see this screen as shown in Figure 1. Please enter the following information highlighted in yellow boxes. Enter the word TEST as shown. For "Operator Name Here", please enter the test operator's name. Make sure to check the Simulate CA box and change the "Parametrics" to "Do not upload".

![](_page_2_Picture_8.jpeg)

Figure 1: MTP setup

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

- 2. After this is complete, please click the black arrow button on the right-hand side.
- 3. The test will then begin. If you see the error shown below, please refer to tracknum error handling at the end of this document.

![](_page_3_Picture_2.jpeg)

a. Throughout the test you will see popup messages asking you to enter certain information. The first popup box will look like the following:

![](_page_3_Picture_4.jpeg)

Figure 2. Popup Message

This popup message is asking you to enter the Storage Location that the battery lot came from, in Inventory. Please enter the information in the text field and then click Enter.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

4. Following this there will be a popup for you to enter the Lot Part Number. This is the orderable part number in barcode format which can generally be found on the bag holding the battery (see Appendix B Figure B) and on the box holding the bag (see APPENDIX B Figure A). Usually, this information can be scanned. If there is no barcode on these items, the information might be present in text form only and must be keyed in. Please scan or key in and press Enter. If the Lot Part Number is not available, please enter the Manufacturing date instead.

![](_page_4_Picture_1.jpeg)

Figure 3: Lot Part Number Entry

5. After this will be a popup asking you to enter the number of batteries in the lot. (The number of batteries to test is calculated using this number.)

![](_page_4_Picture_4.jpeg)

Figure 4: Number of Batteries in Lot Entry

6. Following this step, there will be a message asking you to click the cell type of the battery lot being tested. See Image below:

![](_page_4_Picture_7.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

7. There will be another popup asking you to indicate whether the batteries you are testing have labels containing a barcode.

![](_page_5_Picture_1.jpeg)

If so, then please click the scannable option, and if not, please click the manual one.

#### Scannable Option Path:

a. If there is only one barcode, (see APPENDIX B Figures D, E and F), scan it. If there are two (see APPENDIX B Figure C), first scan the one associated with the text "ID:", check if SN and Date are valid. If so then the operator will be asked to scan the PN barcode, which should be the second available barcode. If not available please manually look for this information and key it in.

![](_page_5_Picture_5.jpeg)

b. The tester has a built in safeguard to automatically detect good vs bad barcode IDs but as a safety precaution it asks the operator if the information is correct. Figure 5 is an example of correct looking information and the image below that is an example of bad information. Note the pack date does not make sense as it is NA/NA/NA.

![](_page_5_Picture_7.jpeg)

Figure 5. Information Check Automatic

![](_page_5_Picture_9.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

The operator should be able to confirm that the information in the pop-up Is correct by comparing it to text on the appropriate battery label (See one of APPENDIX B Figures S, I, A, B, C, D, E or F). If such text is not available on the label, please decide if the pop-up information appears correct, i.e., there are no symbols, the pack date looks like a valid date format, and the part number and serial number appear reasonable. Click "yes" or "no" on the pop-up. If you click "yes", Pop-ups for later batteries will ask you only to scan the battery's barcodes. The program will automatically check to confirm that all the part numbers and dates are the same and the serial numbers are different. If any of this is not correct, the program will restart the entry process from the last battery entered. If you choose no, the operator must enter the required information manually as described in the Manual Option Path.

#### Manual Option Path:

a. You might be dealing with a battery label without a barcode. In this case, you will be asked to key in the Battery Part number (not the orderable PN) through a popup message. Please do so and click Enter if this is available. If not, please click the "NA-Stop Test" button and escalate the problem. The test will then end. Procedure

![](_page_7_Picture_2.jpeg)

b. Another popup message gives you the opportunity to key in the Battery Serial Number if that information is available. If it's not available, click the "Skip" button. If skipped, a temporary serial number will be assigned to each battery to keep track of them for purposes to be described later.

![](_page_7_Picture_4.jpeg)

c. Finally, a 3rd popup will give you the opportunity to enter the Pack Date. Most likely a pack date barcode can be found on the battery pack bag holding the battery or the battery pack box which contains the bag (please see Figures A and B). If it's not available in text or barcode form anywhere, click the "Skip" button.

![](_page_7_Picture_6.jpeg)

Figure 7. Pack Date Code

- d. A tip for quicker keyed-in entry is to start from the month field, click Tab to get to Day, and Tab again for Year.
- e. This information will need to be entered for each battery being tested, but the info will be remembered from the previous battery. Most likely after entering the first battery, you can just double check the info and click submit.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

8. As Information for each battery is entered, a check will be done for the Serial Number, Part Number and Pack Date. If the Serial Number matches that of a previous battery entered, a message will be shown, see image below. If the Part Number or Pack date entered DOES NOT match the previous batteries entered a similar popup will be shown stating this issue. If any of these issues mentioned above occur, then the test will allow you to retry one time. If any of these issues happens again then the test will end. If the operator fixes the issue the test will continue. You will get one retry per battery before the test ends.

![](_page_8_Figure_1.jpeg)

9. After The Option Path selection is made (Scannable or Manual) and data is entered for the first battery to be tested, the test station will show a message telling the operator to get the adaptor that works for the battery being tested, which corresponds to the Part Number shown.

![](_page_8_Picture_3.jpeg)

Unfortunately, because some batteries do not have scannable barcodes, the test cannot determine whether these are EVM or AIT. To find the correct adapter, the operator might need to look through both AIT and EVM documents to find the adaptor that corresponds to the battery part number. For EVM batteries, the document bsmodels.txt is attached to part number PD-006437-01 in EVM Agile. bsmodels.txt should be opened using Excel as a tab-delimited file. Locate the battery part number in the fourth column D. The adaptor part number can be found in the same row of column E. This adaptor shall be used both at this test station and, if Cadex testing is needed, at the Cadex battery capacity analyzer test station. The bsmodels.txt file will also be needed by the Cadex. Its use is described in Appendix A.

For AIT batteries, the "Serial Number Map" tab found in the spreadsheet stored under "Attachments" in document D10016195 in AIT Agile correlates battery part numbers with Zbatt adapter part numbers. Locate the battery part number in column A. The ZBatt Adapter part number can be found in the same row of either column L or M. This adaptor shall be used at this test station.

In some cases with AIT batteries, it will also be necessary to employ Cadex capacity test equipment. This will require different, Cadex-compliant battery adapters. The part numbers of these adapters can be found in bsmodels\_coder.txt, which reports to D10013896 in AIT Agile. The adapters' part numbers are found in the same manner as with the EVM bsmodels.txt file as specified above. The bsmodels.txt file will also be needed by the Cadex. Its use is described in Appendix A.

The operator shall connect the appropriate adaptor to the test station.

The adapters for EVM batteries will be the Cadex ones with this small cable attached. The green connector goes to the Cadex adapter and the banana cables to the test equipment Power Supply and Multi-meter.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_9_Picture_0.jpeg)

Attaching the green connector end to the cadex adapter and the banana cables to the Power Supply and Multimeter, refer to Appendix C.

For AIT batteries, there is the Zbatt adapter. An example is found in the image below. In the lookup table for AIT batteries mentioned above, the Zbatt adapter which correlates to each specific battery can be found.

![](_page_9_Picture_3.jpeg)

Please refer to the setup instructions in appendix C, at the end of this document to check how these adapters should be connected.

## 10. The following pop-up appears:

![](_page_9_Figure_6.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

**Company Confidential** Form OB-CQ-01A Global Procedure Template Rev. 02

**Commented [DJW1]:** Appendix D1

**Commented [DJW2]:** Appendix D1

11. Once the voltage testing is complete, the battery must be removed from the adaptor and placed on a table or other surface in a specific pattern. If the battery has failed the limit test of that specific cell type, then the operator will see the message shown in Figure 7.9. This will tell the operator to place a yellow or red sticker on that battery, indicting the failure. The pattern has 10 columns, but the number of rows depends on how many batteries are being tested in the lot (see Figure 8.) Start from the left most position of the top row and place each battery after that on the right. After there are 10 batteries in a row, start a new row underneath. You will follow the same pattern with each battery to be tested, adding rows as needed (see Figure 8.)

![](_page_10_Picture_1.jpeg)

Figure 7.9. Battery Cell Type Limit Failure

![](_page_10_Picture_3.jpeg)

Figure 8. Battery Placement

The testing station knows which Option Path was selected in step 7. It will begin to display the appropriate set of step 7 pop-ups for use with the next battery to be tested. Having the proper adapter connected, it will skip step 7 and move on to step 8. When the last battery to be tested has been removed from the adaptor and placed in the pattern described in step 11, the testing station will display the pop-up shown below.

![](_page_10_Picture_6.jpeg)

12. Voltage tests identify batteries with extreme low voltages. Batteries with these voltages are shown in red on the following pop-up. (These are the same batteries that are mentioned in step 11, marked with the yellow or red stickers). They shall be removed and scrapped. Any batteries shown in green shall be tested by the Cadex battery analyzer, which will require the use of the correct battery adaptor. The tan boxes represent other batteries, which shall be returned to their original bags and boxes. The greyed boxes are void spaces - they don't represent anything.

If there are no batteries that require Cadex testing, skip to step 18. If one or more batteries require Cadex testing, then the following paragraph will be repeated for each one and the following popup will be shown. This will be explained later on in the procedure.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_11_Figure_0.jpeg)

If the scannable option is active then the operator will be asked to scan the ID of the barcode, else then they will be asked to key in the SN of the green battery shown. If the battery has no SN then the tool assigns one. Please add a sticky note to the unit with the serial number written on it. This is to keep track of the unit as it moves to the Cadex tester and then back again.

![](_page_11_Picture_2.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

13. The Figure 9 pop-up will appear if all batteries passed, the test will end, and the lot will be accepted. In this case, the operator shall proceed to step 20. Otherwise, the Figure 10 pop-up will appear, and testing of the batteries shown in green in the step 12 pop-up will be required using the Cadex battery analyzer.

![](_page_12_Picture_1.jpeg)

Figure 9. All Batteries Passed Voltage testing

![](_page_12_Picture_3.jpeg)

Figure 10. All Batteries Did Not Pass Voltage testing

14. Depending on how many batteries failed, the test station will tell the operator how many are needed to be tested by the Cadex. In Figure 10, six batteries failed, and 4 batteries were chosen to be tested using the Cadex. Up to 4 batteries can be tested in any lot. The operator shall press "OK".

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

- 15. The step 12 pop-up shows one green battery that needs to be Cadex-tested. All green highlighted batteries must be pulled from the battery set for testing, before the test can be finished.
  - a. After pulling a battery they must be woken up again to get a reading from the Cadex machine. This popup will be shown after each battery to ensure this. Each battery will need to be placed back into the adapter to be woken up. After the battery is confirmed to be woken up, it can be removed, label and placed aside for cadex testing. Again, this will be done for each battery that needs to be cadex tested.

![](_page_13_Picture_2.jpeg)

16. Once all the batteries that need to be Cadex-tested are confirmed and labeled, they should be brought over to the Cadex tester to be tested. See Appendix A for the Cadex test procedure.

![](_page_13_Picture_4.jpeg)

17. Once the Cadex testing is complete, the operator will need to enter the corresponding Cadex capacity percentages (without the "%" sign) into the respective text fields matching their Serial Numbers as shown in this section's pop-up. These percentages can be read from the sticky notes on the batteries that will have been updated from the Cadex test results by the operator.

![](_page_13_Picture_6.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

Once the values are entered, the operator shall click the Submit button. After the information is entered, follow the procedure at your Distribution Center and scrap the Cadex-tested batteries.

18. The operator will now see another popup message stating whether the entire lot passed or failed:

![](_page_14_Picture_2.jpeg)

- 19. If the Lot failed, follow the instructions in OB-WA-04 that dictate how to handle a lot which failed testing. If the lot passed, proceed to step 20. This ends this procedure for failed battery lots.
- 20. Place only the tan coloured batteries shown in the step 11 pop-up in their bags and boxes in preparation for their return to inventory. Follow the instructions in OB-WA-04 that dictate how to handle a lot which passed testing.

This concludes the battery test.

### **Tracknum Error Handling**:

1. If you see this error below, then please preform the following steps to fix it:

![](_page_14_Picture_8.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

2. Please procced to the following path in file explorer and copy the TEST.nsb file into the tracknums folder. See image below. Then click OK, and try to test again.

![](_page_15_Picture_1.jpeg)

# APPENDIX A – Cadex Testing

# **APPENDIX A1**

Confirm that a type A to type B USB cable interconnects a PC to the Cadex C7400-C battery analyzer. Cycle the power to the analyzer.

![](_page_16_Picture_3.jpeg)

Confirm that V1.10 /1.01 and \*\* DIAGNOSTICS Passed \*\* are displayed. If something different is shown, please escalate the problem.

Confirm that a sticker has been affixed to the analyzer stating that ZebraCapTest.cpg was installed. If there is no sticker, follow the procedure in **APPENDIX A2**.

The automated voltage measurement tool employed a Cadex adapter to test battery voltages. The tool indicates anywhere from none to four batteries must be Cadex-tested. Install as many identical adapters of the part number supplied by the tool as there are batteries that the tool requires to be tested by the C7400.

Obtain and store on the Cadex PC the file bsmodels.txt found under the Attachments pull-down which reports to PD-006437-01 in EVM Agile. Also obtain and store the file bsmodels\_ccoder.txt which reports to D10013896 in ATS Agile. These files are periodically updated by Zebra engineering and must be imported into BatteryShop each time a battery lot is tested.

Launch Cadex BatteryShop. You should see the following:

![](_page_16_Picture_9.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

**Company Confidential** Form OB-CQ-01A Global Procedure Template Rev. 02

**Commented [DJW3]:** Should this be a appendix or just a

**Commented [PC4R3]:** I don't see that it matters. If you'd

**Commented [DJW5R3]:** This is still basically the test, so it

**Commented [DJW6]:** Make sure to include DC whenever there is a update/change in these documents. For NL1 Eric/Wybe will update the latest version of these files in the batshop.

**Commented [PC7R6]:** I can add individuals now for each DC. But there are personnel changes as time goes on. There is no good mechanism for tracking these changes. That is why the procedure requires a download of data for each lot. That is the only way I can think of to ensure that tests are always current.

**Commented [DJW8R6]:** We have user groups for these, in which all engineers are in. So also a new hired. It's more that I don't want to burden the operator with this kind tasks as they are not really used to agile and stuff.

Select HELP near the top of the screen and then ABOUT. You should see the following:

![](_page_17_Picture_1.jpeg)

Confirm the Build number shown. If you see a different number, escalate the problem. Click OK.

See below. From the pulldown DATABASE , select the BATTERY MODELS option.

![](_page_17_Picture_4.jpeg)

This opens the Battery Models window.

![](_page_17_Picture_6.jpeg)

Click on the first model, hold down the shift key and scroll to the end of the list.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

All models will be highlighted as seen below. Press the DELETE button next to the yellow arrow. Deletion will take some time, perhaps a minute. The deletion process is required because some Cadex machines could contain old, incorrect files for which there are no replacements yet available.

![](_page_18_Figure_1.jpeg)

When the process is complete, you will see the window below.

![](_page_18_Picture_3.jpeg)

Press the IMPORT Icon near the top of the screen above.

Navigate to where bsmodels.txt is stored (see below), select the file, and click OPEN.

![](_page_19_Picture_1.jpeg)

You'll see something like what is pictured below:

![](_page_19_Picture_3.jpeg)

Click OK and repeat the IMPORT process for bsmodels\_ccoder.txt file. Click OK again. The Information pop-up will disappear. Click CLOSE in the upper right hand corner.

## On the following screen, select the CONNECT button:

![](_page_20_Picture_1.jpeg)

You should see an icon appear in the upper left-hand corner. The number of white vertical bars in the icon should match the number of installed adapters:

![](_page_20_Picture_3.jpeg)

Make the **Analyze Battery** selection shown below:

![](_page_20_Picture_5.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

## You should see the following screen:

![](_page_21_Figure_1.jpeg)

In the Battery Model window near the top left, type the part number of the battery (not its orderable part number) to be tested. Alternatively, you can scroll through the list and make a selection. Verify that the selected model matches the battery part number and that there's green text on the bottom of the window as seen below:

![](_page_21_Picture_3.jpeg)

If you are testing more than one battery, ensure the Analyzer Mode is set to Batch. Otherwise, set it to Single. *Note that upon insertion of batteries into the adapter, the test will start immediately.*

![](_page_22_Picture_1.jpeg)

Insert batteries into the adapters. The test(s) should start up and the green text on the Analyzer Battery window will change to yellow (showing the port(s) and station(s) used.)

When the test is complete, the BatteryShop unit icon will show that station as green.

![](_page_22_Picture_4.jpeg)

**Commented [DJW9]:** Maybe mention that the test will start

**Commented [PC10R9]:** Doesn't the existing text say that the

**Commented [DJW11R9]:** Correct, however I think it should

The C7400's will show a green "READY" LED, and the word "FINISHED" and the voltage of the battery in the associated adapter on its LCD. See below. Only one station is shown here because in this case, only one adapter was installed.

![](_page_23_Picture_1.jpeg)

Select each active station one by one. The display will indicate a percentage (see below). Copy that percentage onto the sticky note that came with the battery to be tested that was installed in the selected station.

![](_page_23_Picture_3.jpeg)

This completes testing in the **APPENDIX 1** section of this document and of the entire Cadex test procedure. Return all tested batteries with their sticky labels to the automated voltage test tool for further processing of information.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

## **APPENDIX A2**

# **Installation of ZebraCapTest.cpg and Configuration of BatteryShop**

The following procedure assumes that there is no sticker on the analyzer indicating that Zebra Cap Test.cpg has been installed. This procedure takes this opportunity to install this file and ensure that BatteryShop is properly configured. If such a sticker exists, there is no need to execute this procedure. Return to **APPENDIX A1**.

If Cadex BatteryShop has not been installed, proceed to **APPENDIX A3**. Upon completion of the **APPENDIX A3** procedure, the user will be instructed to execute the following procedure:

1. Using Notepad or a simple text editor (not Word), create a text file named ZebraCapTest.cpg with the following content and store it on the PC:

> Zebra Test Zebra T 2\1\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 0\0\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 0\0\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 0\0\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 0\0\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 7\0\0\0\0\0\0\0\100\100\0\0\0\0\0\0\0\0\0\0\0\0\ 1

2. Open BatteryShop and Click "Help" which is one of the selections at the top of the screen, and then click "About". Confirm that the Version is Cadex BatteryShop 7.2 or later. (If the version is earlier, proceed to **APPENDIX A3**.)

Make the selection shown below:

![](_page_24_Picture_8.jpeg)

The above selection opens the custom products window. Remove the check marks for all the items in the Active column:

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_25_Figure_0.jpeg)

Press the Import button seen below and select **ZebraCapTest.cpg .** 

![](_page_25_Picture_2.jpeg)

Press the SAVE icon and then the CLOSE icon.

This completes the **APPENDIX A2** procedure. Please place a sticker on the C7400 that reads, "Zebra Cap Test.cpg has been installed." Please return to and follow the instructions in **APPENDIX A1**.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

#### **APPENDIX A3**

# **Installation of BatteryShop**

Locate and double click the BatteryShop. Install file Batshop\_7.1.1.0.exe. This will unzip the needed files to a temporary folder and get things ready for installation onto the computer.

![](_page_26_Picture_3.jpeg)

Once the files are unzipped, run the Setup option to start the installation wizard. The Wizard will walk you through the setup of BatteryShop.

![](_page_26_Figure_5.jpeg)

Press NEXT on the above screen to see this:

![](_page_26_Figure_7.jpeg)

Enter the information and press NEXT.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

You should see the following (you might see 7.2 rather than 7.1):

![](_page_27_Figure_1.jpeg)

Press FINISH. You should see

![](_page_27_Figure_3.jpeg)

Press NEXT.

With the C7 connected, you'll need to identify the Comm Port that it's installed on by using Windows Device Manager and opening Ports (COM & LPT):

![](_page_27_Figure_6.jpeg)

The screen below will ask you to select the C74xx COM port shown (COM6 is shown above)

![](_page_27_Figure_8.jpeg)

Press NEXT. The following should appear:

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_28_Figure_0.jpeg)

Since we are printing neither labels nor Service Reports, simply press Next on the above and on the following two screens:

![](_page_28_Figure_2.jpeg)

![](_page_28_Figure_3.jpeg)

Enter a Service period of 6 months below and press Next to continue.

![](_page_28_Figure_5.jpeg)

Set the options as shown below and press Next to continue

![](_page_28_Picture_7.jpeg)

Press Next to continue. You should see the following:

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_29_Picture_0.jpeg)

Press FINISH.

This concludes the **APPENDIX A3** PROCEDURE. Execute the procedure in **APPENDIX A2**.

# **APPENDIX B: Battery and shipping carton labels:**

![](_page_30_Figure_3.jpeg)

Figure S Shipping label

![](_page_31_Figure_2.jpeg)

![](_page_32_Figure_0.jpeg)

Figure A Individual Box Label

Additionally, a plastic bag containing a battery will be found inside the boxes that hold individual batteries. The bag has a label that looks like this:

![](_page_32_Picture_3.jpeg)

Figure B Battery Bag Label

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_33_Figure_0.jpeg)

Figure C

| Character | Description                                                                                                               |  |  |  |  |  |
|-----------|---------------------------------------------------------------------------------------------------------------------------|--|--|--|--|--|
| 1         | Pack Manufacturer                                                                                                         |  |  |  |  |  |
|           | (see table in 70-108225-07)                                                                                               |  |  |  |  |  |
| 2         | Cell Production Year                                                                                                      |  |  |  |  |  |
|           | (see table in 70-108225-07)                                                                                               |  |  |  |  |  |
| 3         | Cell Production Week                                                                                                      |  |  |  |  |  |
| 4         | 01 to 53                                                                                                                  |  |  |  |  |  |
| 5         | Cell Vendor                                                                                                               |  |  |  |  |  |
|           | (see table in 70-108225-07)                                                                                               |  |  |  |  |  |
| 6         | Pack Production Year                                                                                                      |  |  |  |  |  |
|           | (see table in 70-108225-07)                                                                                               |  |  |  |  |  |
| 7         | Pack Production Month                                                                                                     |  |  |  |  |  |
|           | 1: Jan 2: Feb 9: Sep A: Oct                                                                                               |  |  |  |  |  |
|           | B: Nov C: Dec                                                                                                             |  |  |  |  |  |
| 8         | Pack Production Date                                                                                                      |  |  |  |  |  |
| 9         | 01 to 31                                                                                                                  |  |  |  |  |  |
| A         | PCB Production Year (for day primary PCB was tested after being populated)                                                |  |  |  |  |  |
|           | Last digit                                                                                                                |  |  |  |  |  |
| В         | PCB Production Month (for day primary PCB was tested after being populated)                                               |  |  |  |  |  |
|           | 1: Jan 2: Feb 9: Sep A: Oct                                                                                               |  |  |  |  |  |
|           | B: Nov C: Dec                                                                                                             |  |  |  |  |  |
| C         | PCB Production Day (for day primary PCB was tested after being populated)                                                 |  |  |  |  |  |
| D         | 01 to 31                                                                                                                  |  |  |  |  |  |
| E         | PCB Production Shift (for shift primary PCB was tested after being populated)                                             |  |  |  |  |  |
|           | A: Day Shift B: Night Shift                                                                                               |  |  |  |  |  |
| F         | Pack Production Line No.                                                                                                  |  |  |  |  |  |
|           | 1: 1 2: 2 9: 9 A: 10                                                                                                      |  |  |  |  |  |
| G         | Pack Production Shift                                                                                                     |  |  |  |  |  |
|           | A: Day Shift B: Night Shift                                                                                               |  |  |  |  |  |
| H         | Normal/Rework                                                                                                             |  |  |  |  |  |
|           | Print "." for normal, original pack production year code for rework.                                                      |  |  |  |  |  |
|           | # : IN I                                                                                                                  |  |  |  |  |  |
| I         | Serial Number                                                                                                             |  |  |  |  |  |
| J         |                                                                                                                           |  |  |  |  |  |
| K         | 00000000 to FFFFFFF (Eight hexadecimal characters,                                                                        |  |  |  |  |  |
| L         | unique for any given pack date code and part number)                                                                      |  |  |  |  |  |
| M         | I                                                                                                                         |  |  |  |  |  |
| N         | Please refer to the individual pack specifications for details on programming this number into applicable smart batteries |  |  |  |  |  |
| 0         | smart batteries.                                                                                                          |  |  |  |  |  |

![](_page_34_Figure_0.jpeg)

Figure D

![](_page_34_Figure_2.jpeg)

(There is a barcode in the white space above, but it is not shown in the above image.) Figure E

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_35_Figure_0.jpeg)

Figure F

There are two pieces of information on labels S, I, A and B that are needed by the tool. The tool can capture them from one or more of these labels: "(1P) PART NUMBER:" or "(1P) Symbol P/N:" precedes the orderable battery part number (The word 'Symbol' might be replaced with other company names.) "(D)DATE:" precedes the date of manufacture. This information is the same on all the above labels.

Scanning any of the above labels' barcodes will copy these pieces of information into the tool. The Date of Manufacture is typically, but not always, available on the battery pack label as well, but the labels shown above are the only places that the orderable part number is available in barcode form. (On many battery pack labels, the orderable part number is available in text form only.)

It is expected that all batteries in the lot delivered for testing will have the same orderable part number and Date of Manufacture. However, the operator, working with the tool, must confirm that this is case.

The battery pack label (non-orderable) part number is different from the orderable part number. The pack label part number and the battery serial number must still be obtained. Most but not all battery pack labels will have this information available in barcode form, which is scannable by the tool – otherwise, the information should be keyed into the tool after reading human-readable text. The tool and the operator must work together to ensure that all orderable part numbers are the same, all pack label part numbers are the same, all dates of manufacture are the same, and all serial numbers are different.

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

# **APPENDIX C**

![](_page_36_Figure_1.jpeg)

Page 1: Main Layout

iring Diagram for I2C

![](_page_36_Picture_4.jpeg)

NI 4 1 Pinout

![](_page_36_Picture_6.jpeg)

![](_page_36_Picture_7.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

Start with finding the correct zbat adpater on the AIT lookup table. After this please attach the battery. Usually the battery goes in at an angle and clips into place. Please see image below.

**Commented [DJW12]:** Should also be a appendix D1 (?)

**Commented [AJ13R12]:** Its not in Appendix C

![](_page_37_Picture_5.jpeg)

When the battery is inserted, now match the red cable from the power supply to the red connector on the adapter. Same with the black cable. Please see the image below.

![](_page_37_Picture_7.jpeg)

After inserting the red and black cables, please connect the aux cable to the adapter as well. As shown in the image

![](_page_37_Picture_9.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

The final setup show look at follows: After this please continue in the test.

![](_page_38_Picture_1.jpeg)

#### Instructions for EVM batteries:

Please refer to the EVM lookup table to find the correct adapter for the battery you are testing. After this please insert the battery into the adapter. Once the battery is inserted into the adapter, connect the cable adapter into the cadex adapter. Make sure the red wires and the black wires match their respected colors on the cadex adapter. See the image below.

![](_page_38_Picture_4.jpeg)

Once that is inserted you can then connect the power supply cables to the cable adapter, red to red and black to black. See image below.

![](_page_39_Picture_1.jpeg)

You can now continue in the test.

# Appendix D: Query Battery Data

![](_page_40_Picture_7.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_41_Picture_1.jpeg)

![](_page_41_Picture_7.jpeg)

*If using a printed copy of this procedure, verify its revision level is the latest before use. Refer to ISO Library.*

![](_page_42_Figure_1.jpeg)