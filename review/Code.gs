/**
 * @OnlyCurrentDoc Limits the script to only accessing the spreadsheet it's bound to.
 */

const CONFIG = {
  REVIEW_STATUS: "Review Status",
  REVIEWER_EMAIL: "Reviewer Email",
  TIMESTAMP: "Review Timestamp",
  NOTES: "Review Notes",
  STATUS_IN_PROGRESS: "In Progress",
  LOCK_TIMEOUT: 30000, // 30 seconds
  REQUIRED_COLUMNS: ["Review Status", "Reviewer Email", "Review Timestamp", "Review Notes"],
  VALID_DECISIONS: new Set(["True", "False", "Unsure"])
};

function doGet(e) {
  const sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!sheetId) {
    return HtmlService.createHtmlOutput(
      '<b>Error:</b> Spreadsheet ID not configured. Please set the SHEET_ID script property.'
    );
  }

  try {
    SpreadsheetApp.openById(sheetId).getName(); // Test access
    return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('Sheet Row Reviewer')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  } catch (err) {
    Logger.log("Error accessing Sheet ID '%s': %s", sheetId, err);
    return HtmlService.createHtmlOutput(
      `<b>Error:</b> Cannot access Spreadsheet with ID: ${sheetId}. Check ID and permissions. Error: ${err.message}`
    );
  }
}

/**
 * Gets the next available row for review and assigns it to the current user.
 * Uses LockService for concurrency control.
 * @return {object} Response containing row data or error/message
 */
function getNextRowToReview() {
  const userEmail = Session.getActiveUser().getEmail();
  if (!userEmail) {
    Logger.log('Could not get user email.');
    return { error: "Could not identify the current user. Please ensure you are logged into a Google Account." };
  }

  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(CONFIG.LOCK_TIMEOUT)) {
      Logger.log('Could not obtain lock to get next row.');
      return { error: "Could not get a lock to find the next row. Server might be busy. Please try again." };
    }

    const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
    const sheet = ss.getActiveSheet();
    const headerData = getOrAddHeaders_(sheet);

    if (!headerData.success) {
      throw new Error(headerData.error);
    }

    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      return { message: "No data rows found in the sheet." };
    }

    // Efficiently get status and reviewer columns
    const statusCol = headerData.indices[CONFIG.REVIEW_STATUS] + 1;
    const reviewerCol = headerData.indices[CONFIG.REVIEWER_EMAIL] + 1;
    const reviewRange = sheet.getRange(2, Math.min(statusCol, reviewerCol), lastRow - 1, 
                                     Math.abs(statusCol - reviewerCol) + 1);
    const reviewData = reviewRange.getValues();

    // Find first unreviewed row
    let nextRowIndex = -1;
    for (let i = 0; i < reviewData.length; i++) {
      const [status, reviewer] = statusCol < reviewerCol ? reviewData[i] : reviewData[i].reverse();
      if (!status) {
        nextRowIndex = i + 2;
        break;
      }
    }

    if (nextRowIndex === -1) {
      return { message: "All rows have been reviewed or assigned." };
    }

    // Assign row to user
    sheet.getRange(nextRowIndex, statusCol).setValue(CONFIG.STATUS_IN_PROGRESS);
    sheet.getRange(nextRowIndex, reviewerCol).setValue(userEmail);
    
    // Release lock before reading full row data
    lock.releaseLock();

    // Get complete row data
    const rowRange = sheet.getRange(nextRowIndex, 1, 1, sheet.getLastColumn());
    const rowData = rowRange.getValues()[0];

    Logger.log(`Assigned row ${nextRowIndex} to ${userEmail}`);
    return {
      rowIndex: nextRowIndex,
      headers: headerData.headers,
      rowData: rowData
    };

  } catch (error) {
    Logger.log(`Error in getNextRowToReview: ${error}`);
    return { error: `An error occurred: ${error.message}` };
  } finally {
    if (lock.hasLock()) {
      lock.releaseLock();
    }
  }
}

/**
 * Submits the review data for a specific row.
 * @param {number} rowIndex Row being reviewed (1-based)
 * @param {string} decision Review decision ('True', 'False', 'Unsure')
 * @param {string} notes Reviewer notes
 * @return {object} Success status and optional message
 */
function submitReview(rowIndex, decision, notes) {
  const userEmail = Session.getActiveUser().getEmail();
  if (!userEmail) {
    Logger.log('Could not get user email for submission.');
    return { success: false, message: "Could not identify the current user for submission." };
  }

  if (!rowIndex || !CONFIG.VALID_DECISIONS.has(decision)) {
    Logger.log(`Invalid submission data: rowIndex=${rowIndex}, decision=${decision}`);
    return { success: false, message: "Invalid submission data received." };
  }

  try {
    const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
    const sheet = ss.getActiveSheet();
    const headerData = getOrAddHeaders_(sheet);

    if (!headerData.success) {
      throw new Error(headerData.error);
    }

    // Get column indices
    const columns = {
      status: headerData.indices[CONFIG.REVIEW_STATUS] + 1,
      reviewer: headerData.indices[CONFIG.REVIEWER_EMAIL] + 1,
      timestamp: headerData.indices[CONFIG.TIMESTAMP] + 1,
      notes: headerData.indices[CONFIG.NOTES] + 1
    };

    // Optional ownership verification
    const currentReviewer = sheet.getRange(rowIndex, columns.reviewer).getValue();
    const currentStatus = sheet.getRange(rowIndex, columns.status).getValue();
    
    if (currentReviewer !== userEmail || currentStatus !== CONFIG.STATUS_IN_PROGRESS) {
      Logger.log(`Warning: Row ${rowIndex} submission ownership mismatch. Current: ${currentReviewer}, Status: ${currentStatus}`);
    }

    // Update all fields at once
    const range = sheet.getRange(rowIndex, columns.status, 1, 4);
    range.setValues([[
      decision,
      userEmail,
      new Date(),
      notes || ""
    ]]);

    SpreadsheetApp.flush();
    Logger.log(`Review submitted for row ${rowIndex} by ${userEmail}: ${decision}`);
    return { success: true };

  } catch (error) {
    Logger.log(`Error in submitReview for row ${rowIndex}: ${error}`);
    return { success: false, message: `An error occurred while submitting: ${error.message}` };
  }
}

/**
 * Ensures required columns exist and returns their indices
 * @param {Sheet} sheet The sheet to check/modify
 * @return {object} Header information and status
 */
function getOrAddHeaders_(sheet) {
  try {
    const headerRange = sheet.getRange(1, 1, 1, sheet.getMaxColumns());
    const headers = headerRange.getValues()[0].map(h => String(h).trim());
    const headerIndices = {};
    const missingCols = [];
    let nextCol = headers.length;

    // Find existing headers and identify missing ones
    CONFIG.REQUIRED_COLUMNS.forEach(colName => {
      const index = headers.findIndex(h => h === colName);
      if (index !== -1) {
        headerIndices[colName] = index;
      } else {
        missingCols.push(colName);
        headerIndices[colName] = nextCol++;
      }
    });

    // Add missing columns if needed
    if (missingCols.length > 0) {
      Logger.log("Adding missing columns: " + missingCols.join(', '));
      const currentCols = sheet.getMaxColumns();
      const neededCols = Math.max(...Object.values(headerIndices)) + 1;
      
      if (neededCols > currentCols) {
        sheet.insertColumnsAfter(currentCols, neededCols - currentCols);
      }

      missingCols.forEach(colName => {
        sheet.getRange(1, headerIndices[colName] + 1).setValue(colName);
      });

      // Refresh headers after adding new columns
      const updatedHeaders = sheet.getRange(1, 1, 1, neededCols).getValues()[0];
      return {
        success: true,
        headers: updatedHeaders,
        indices: headerIndices
      };
    }

    return {
      success: true,
      headers: headers,
      indices: headerIndices
    };

  } catch (error) {
    Logger.log(`Error in getOrAddHeaders_: ${error}`);
    return {
      success: false,
      error: `Failed to set up review columns: ${error.message}`
    };
  }
}