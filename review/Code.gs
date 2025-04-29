// Sheet column names and values
const REVIEW_STATUS = 'review_status';
const REVIEW_NOTES = 'review_notes';
const REVIEW_USER = 'review_user';
const REVIEW_TIMESTAMP = 'review_timestamp';

// Review status values
const STATUS = {
  IN_PROGRESS: 'in_progress',
  CORRECT: 'correct',
  INCORRECT: 'incorrect',
  NOT_SURE: 'not_sure'
};

/**
 * Get the active sheet and its header row
 */
function getSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  return { sheet, headers };
}

/**
 * Find column index by name
 */
function getColumnIndex(headers, columnName) {
  const index = headers.indexOf(columnName);
  if (index === -1) throw new Error(`Column ${columnName} not found`);
  return index + 1;
}

/**
 * Returns the next available row and marks it as in_progress
 */
function getNextRow() {
  const { sheet, headers } = getSheet();
  const statusCol = getColumnIndex(headers, REVIEW_STATUS);
  
  // Get all review status values
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return null; // Only header row exists
  
  const statusRange = sheet.getRange(2, statusCol, lastRow - 1, 1);
  const statusValues = statusRange.getValues();
  
  // Find first empty status row
  for (let i = 0; i < statusValues.length; i++) {
    if (!statusValues[i][0]) {
      const row = i + 2; // Add 2 for header row and 0-based index
      
      // Mark as in_progress and return row data
      sheet.getRange(row, statusCol).setValue(STATUS.IN_PROGRESS);
      
      // Get all row data
      const rowData = sheet.getRange(row, 1, 1, headers.length).getValues()[0];
      return {
        rowIndex: row,
        headers: headers,
        data: rowData
      };
    }
  }
  
  return null; // No available rows
}

/**
 * Submit a review for a specific row
 */
function submitReview(rowIndex, decision, notes) {
  const { sheet, headers } = getSheet();
  
  // Get column indices
  const statusCol = getColumnIndex(headers, REVIEW_STATUS);
  const notesCol = getColumnIndex(headers, REVIEW_NOTES);
  const userCol = getColumnIndex(headers, REVIEW_USER);
  const timeCol = getColumnIndex(headers, REVIEW_TIMESTAMP);
  
  // Update each field individually to ensure correct column order
  sheet.getRange(rowIndex, statusCol).setValue(decision);
  sheet.getRange(rowIndex, notesCol).setValue(notes);
  sheet.getRange(rowIndex, userCol).setValue(Session.getActiveUser().getEmail());
  sheet.getRange(rowIndex, timeCol).setValue(new Date());
  
  return true;
}

/**
 * Web app entry point - serves HTML interface
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Review Interface')
    .setFaviconUrl('https://www.google.com/sheets/about/favicon.ico');
}