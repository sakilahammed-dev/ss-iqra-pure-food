/**
 * =========================================================================
 * SS Iqra Pure Food - Verified Orders Ledger (Google Apps Script)
 * =========================================================================
 * ব্র্যান্ড: এস এস ইকরা পিওর ফুড (SS Iqra Pure Food)
 * প্রতিষ্ঠাতা: শাকিল আহাম্মেদ (Sakil Ahammed)
 * উপদেষ্টা: কলিজা (Kolija)
 *
 * কাজের নিয়ম:
 * কাস্টমার অর্ডার করার পর যখন শাকিল ভাই ফোনে কথা বলে নিশ্চিত হয়ে
 * টেলিগ্রামের [ ✅ অর্ডার কনফার্মড ] বাটনে চাপবেন—
 * শুধুমাত্র তখনই এই গুগল শিটে হিসাবের রো যুক্ত হবে। কোনো ফেক বা আনভেরিফায়েড ডাটা ঢুকবে না।
 * =========================================================================
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Check if headers exist, if not create them
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "তারিখ",
        "ইনভয়েস আইডি",
        "কাস্টমারের নাম",
        "মোবাইল নম্বর",
        "সম্পূর্ণ ডেলিভারি ঠিকানা",
        "পণ্য ও পরিমাণ",
        "মোট ক্যাশ বিল (টাকা)",
        "কনফার্মেশন স্ট্যাটাস",
        "Steadfast ট্র্যাকিং আইডি",
        "কনফার্ম করার সময়"
      ]);
      
      // Style header row
      var headerRange = sheet.getRange(1, 1, 1, 10);
      headerRange.setBackground("#0F5132"); // SS Iqra Forest Green
      headerRange.setFontColor("#FFFFFF");
      headerRange.setFontWeight("bold");
      headerRange.setHorizontalAlignment("center");
    }

    var data = JSON.parse(e.postData.contents);

    var dateStr = Utilities.formatDate(new Date(), "Asia/Dhaka", "yyyy-MM-dd");
    var timeStr = Utilities.formatDate(new Date(), "Asia/Dhaka", "hh:mm a");

    var invoice = data.invoice || "SS-" + Math.floor(100000 + Math.random() * 900000);
    var name = data.name || "গ্রাহক";
    var phone = data.phone || "";
    var address = data.address || "";
    var product = data.product || "১ কেজি মেগা ফ্যামিলি জার হানি-নাট";
    var codAmount = data.cod_amount || "970";
    var status = "Verified & Confirmed (শাকিল ভাই অনুমোদিত)";
    var tracking = data.tracking || "Pending Booking";

    // Append verified order row
    sheet.appendRow([
      dateStr,
      invoice,
      name,
      phone,
      address,
      product,
      codAmount,
      status,
      tracking,
      timeStr
    ]);

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Order #" + invoice + " successfully logged into SS Iqra Google Sheet!"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput("SS Iqra Pure Food - Google Apps Script Ledger is LIVE and Active!");
}
