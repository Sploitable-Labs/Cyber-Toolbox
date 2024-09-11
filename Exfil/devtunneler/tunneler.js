function doPost(e) {
    try {
      var data = JSON.parse(e.postData.contents);
    

      
      
      // Check if the data contains 'code' (for device code) or 'url' (for tunnel URL)
      if (data.code) {
        var recipient = data.email;
        var deviceCode = data.code;
        
        // Define the subject and body of the email for the device code
        var subject = "Received Device Code";
        var body = "https://github.com/login/device : " + deviceCode;
        
        // Send the email for the device code
        MailApp.sendEmail(recipient, subject, body);
        
        // Return a success response for the device code
        return ContentService.createTextOutput("")
                             .setMimeType(ContentService.MimeType.TEXT);
        
      } else if (data.url) {
        var recipient = data.email;
        var extractedUrl = data.url;
        
        // Define the subject and body of the email for the tunnel URL
        var subject = "Tunnel URL Received";
        var body = "The extracted tunnel URL is: " + extractedUrl;
        
        // Send the email for the tunnel URL
        MailApp.sendEmail(recipient, subject, body);
        
        // Return a success response for the tunnel URL
        return ContentService.createTextOutput("")
                             .setMimeType(ContentService.MimeType.TEXT);      
        
      } else {
        // If neither 'code' nor 'url' are present in the POST data, return an error response
        return ContentService.createTextOutput("")
                             .setMimeType(ContentService.MimeType.TEXT);
      }
      
    } catch (error) {
      // Handle any errors that occur during processing
      return ContentService.createTextOutput("")
                           .setMimeType(ContentService.MimeType.TEXT);
    }
  }  