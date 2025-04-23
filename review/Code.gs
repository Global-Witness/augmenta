/**
 * @OnlyCurrentDoc Limits the script to only accessing the spreadsheet it's bound to.
 */

const CONFIG = {
  REVIEW_STATUS: "Review Status",
  REVIEWER_EMAIL: "Reviewer Email",
  TIMESTAMP: "Review Timestamp",
  NOTES: "Review Notes",
  STATUS_IN_PROGRESS: "In Progress",
  LOCK_TIMEOUT: 10000, // Reduced to 10 seconds
  CHUNK_SIZE: 1000, // Process data in chunks
  REQUIRED_COLUMNS: ["Review Status", "Reviewer Email", "Review Timestamp", "Review Notes"],
  VALID_DECISIONS: new Set(["True", "False", "Unsure"]),
  CACHE_DURATION: 21600 // 6 hours in seconds
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
      .setTitle('Augmenta Review')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  } catch (err) {
    Logger.log("Error accessing Sheet ID '%s': %s", sheetId, err);
    return HtmlService.createHtmlOutput(
      `<b>Error:</b> Cannot access Spreadsheet with ID: ${sheetId}. Check ID and permissions. Error: ${err.message}`
    );
  }
}

/**
 * Executes a function with a lock and proper cleanup
 * @param {Function} callback Function to execute under lock
 * @param {number} timeout Lock timeout in milliseconds
 * @return {*} Result of the callback function
 */
function withLock_(callback, timeout = CONFIG.LOCK_TIMEOUT) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(timeout)) {
      throw new Error("Could not obtain lock. Server might be busy. Please try again.");
    }
    return callback();
  } finally {
    if (lock.hasLock()) {
      lock.releaseLock();
    }
  }
}

/**
 * Gets cached header indices or generates them if not cached
 * @param {Sheet} sheet The sheet to get headers from
 * @return {object} Header indices
 */
function getHeaderIndices_(sheet) {
  const cache = CacheService.getScriptCache();
  const cacheKey = `header_indices_${sheet.getSheetId()}`;
  
  let indices = cache.get(cacheKey);
  if (indices) {
    return JSON.parse(indices);
  }

  const headerData = getOrAddHeaders_(sheet);
  if (!headerData.success) {
    throw new Error(headerData.error);
  }

  cache.put(cacheKey, JSON.stringify(headerData.indices), CONFIG.CACHE_DURATION);
  return headerData.indices;
}

/**
 * Finds the next unreviewed row efficiently
 * @param {Sheet} sheet The sheet to search
 * @param {number} statusCol Status column index
 * @param {number} reviewerCol Reviewer column index
 * @return {number} Row index or -1 if none found
 */
function findNextUnreviewedRow_(sheet, statusCol, reviewerCol) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return -1;

  for (let startRow = 2; startRow <= lastRow; startRow += CONFIG.CHUNK_SIZE) {
    const endRow = Math.min(startRow + CONFIG.CHUNK_SIZE - 1, lastRow);
    const range = sheet.getRange(startRow, statusCol, endRow - startRow + 1, 1);
    const values = range.getValues();
    
    const rowIndex = values.findIndex(row => !row[0]);
    if (rowIndex !== -1) {
      return startRow + rowIndex;
    }
  }
  return -1;
}

/**
 * Gets the next available row for review and assigns it to the current user.
 * Uses optimized locking and caching strategies.
 * @return {object} Response containing row data or error/message
 */
function getNextRowToReview() {
  const userEmail = Session.getActiveUser().getEmail();
  if (!userEmail) {
    Logger.log('Could not get user email.');
    return { error: "Could not identify the current user. Please ensure you are logged into a Google Account." };
  }

  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
  const sheet = ss.getActiveSheet();

  return withLock_(() => {
    try {
      const headerIndices = getHeaderIndices_(sheet);
      const statusCol = headerIndices[CONFIG.REVIEW_STATUS] + 1;
      const reviewerCol = headerIndices[CONFIG.REVIEWER_EMAIL] + 1;

      const nextRowIndex = findNextUnreviewedRow_(sheet, statusCol, reviewerCol);
      if (nextRowIndex === -1) {
        return { message: "All rows have been reviewed or assigned." };
      }

      // Batch update status and reviewer
      sheet.getRange(nextRowIndex, statusCol, 1, 2).setValues([[
        CONFIG.STATUS_IN_PROGRESS,
        userEmail
      ]]);

      // Get complete row data outside of critical section
      const rowRange = sheet.getRange(nextRowIndex, 1, 1, sheet.getLastColumn());
      const rowData = rowRange.getValues()[0];
      const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

      Logger.log(`Assigned row ${nextRowIndex} to ${userEmail}`);
      return {
        rowIndex: nextRowIndex,
        headers: headers,
        rowData: rowData
      };

    } catch (error) {
      Logger.log(`Error in getNextRowToReview: ${error}`);
      return { error: `An error occurred: ${error.message}` };
    }
  });
}

/**
 * Submits the review data for a specific row using batch operations.
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

  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
  const sheet = ss.getActiveSheet();

  return withLock_(() => {
    try {
      const headerIndices = getHeaderIndices_(sheet);
      const columns = {
        status: headerIndices[CONFIG.REVIEW_STATUS] + 1,
        reviewer: headerIndices[CONFIG.REVIEWER_EMAIL] + 1,
        timestamp: headerIndices[CONFIG.TIMESTAMP] + 1,
        notes: headerIndices[CONFIG.NOTES] + 1
      };

      // Batch read for ownership verification
      const verifyRange = sheet.getRange(rowIndex, columns.reviewer, 1, 2);
      const [currentReviewer, currentStatus] = verifyRange.getValues()[0];
      
      if (currentReviewer !== userEmail || currentStatus !== CONFIG.STATUS_IN_PROGRESS) {
        Logger.log(`Warning: Row ${rowIndex} submission ownership mismatch. Current: ${currentReviewer}, Status: ${currentStatus}`);
      }

      // Batch update all fields
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
  });
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

      // Batch update for missing headers
      const headerUpdates = missingCols.map(colName => [colName]);
      const updateRange = sheet.getRange(1, headerIndices[missingCols[0]] + 1, 1, missingCols.length);
      updateRange.setValues(headerUpdates);

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