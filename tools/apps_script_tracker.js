/**
 * apps_script_tracker.js
 *
 * Google Apps Script web app that:
 *   1. Marks a job row as "Applied" in the Google Sheet
 *   2. Sets the Applied Date
 *   3. Redirects the browser to the actual job URL
 *
 * HOW TO DEPLOY (one-time setup):
 * ─────────────────────────────────
 * 1. Open your Job Tracker Google Sheet
 * 2. Click Extensions → Apps Script
 * 3. Delete any existing code in the editor
 * 4. Paste the contents of this file
 * 5. Click Save (floppy disk icon)
 * 6. Click Deploy → New deployment
 * 7. Click the gear icon next to "Type" → select Web app
 * 8. Set:
 *      Description:    Job tracker redirect
 *      Execute as:     Me
 *      Who has access: Anyone
 * 9. Click Deploy → Authorize access → Allow
 * 10. Copy the Web app URL (looks like https://script.google.com/macros/s/.../exec)
 * 11. Add to your .env file:
 *       APPS_SCRIPT_URL=https://script.google.com/macros/s/.../exec
 *
 * IMPORTANT: If you ever edit this script, you must create a NEW deployment
 * (Deploy → New deployment) — editing a deployed version doesn't update the live URL.
 */

function doGet(e) {
  var action = e.parameter.action || "mark_applied";
  var sheetId = e.parameter.sheet_id;

  if (!sheetId) {
    return HtmlService.createHtmlOutput("Missing sheet_id parameter.");
  }

  var ss, sheet;
  try {
    ss = SpreadsheetApp.openById(sheetId);
    sheet = ss.getSheetByName("Applications");
    if (!sheet) return HtmlService.createHtmlOutput("Sheet 'Applications' not found.");
  } catch (err) {
    return HtmlService.createHtmlOutput("Error opening sheet: " + err.message);
  }

  // Action: mark a single row as Applied
  if (action === "mark_applied") {
    var row = parseInt(e.parameter.row);
    var jobUrl = e.parameter.url || "";
    if (!row) return HtmlService.createHtmlOutput("Missing row parameter.");

    try {
      var currentStatus = sheet.getRange(row, 12).getValue();
      if (currentStatus !== "Applied") {
        sheet.getRange(row, 12).setValue("Applied");
        sheet.getRange(row, 13).setValue(
          Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd")
        );
      }
    } catch (err) {
      Logger.log("Sheet update error: " + err.message);
    }

    return HtmlService.createHtmlOutput(
      '<html><body style="font-family:sans-serif;padding:40px;max-width:480px;margin:0 auto;text-align:center;">' +
      '<div style="font-size:48px;">&#10003;</div>' +
      '<h2 style="color:#1a7f37;">Marked as Applied</h2>' +
      '<p style="color:#555;">Your sheet has been updated.</p>' +
      '<p><a href="' + jobUrl.replace(/[<>"\']/g, "") + '" style="color:#0969da;">Open job listing</a></p>' +
      '</body></html>'
    );
  }

  // Action: mark all specified rows as N/A (for jobs you're skipping)
  if (action === "mark_all_na") {
    var rowsParam = e.parameter.rows || "";
    var rows = rowsParam.split(",").map(function(r) { return parseInt(r.trim()); }).filter(Boolean);
    if (rows.length === 0) return HtmlService.createHtmlOutput("No rows specified.");

    var updated = 0;
    try {
      rows.forEach(function(row) {
        var currentStatus = sheet.getRange(row, 12).getValue();
        if (currentStatus !== "Applied") {
          sheet.getRange(row, 12).setValue("N/A");
          updated++;
        }
      });
    } catch (err) {
      Logger.log("Bulk update error: " + err.message);
    }

    return HtmlService.createHtmlOutput(
      '<html><body style="font-family:sans-serif;padding:40px;max-width:480px;margin:0 auto;text-align:center;">' +
      '<div style="font-size:48px;">&#10003;</div>' +
      '<h2 style="color:#555;">Marked ' + updated + ' job' + (updated !== 1 ? 's' : '') + ' as N/A</h2>' +
      '<p style="color:#aaa;">Already-applied jobs were left unchanged.</p>' +
      '</body></html>'
    );
  }

  return HtmlService.createHtmlOutput("Unknown action: " + action);
}
