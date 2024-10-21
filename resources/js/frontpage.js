document.addEventListener('DOMContentLoaded', function () {
    jQuery("#speakerForm").on("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        // Collect form data
        let formData = {
            fs: jQuery("#fs").val(),
            qts: jQuery("#qts").val(),
            vas: jQuery("#vas").val(),
            re: jQuery("#re").val(),
            _token: jQuery('input[name="_token"]').val() // CSRF token
        };

        // Send data to server via AJAX
        jQuery.ajax({
            url: jQuery(this).attr("action"), // URL is dynamically taken from the form's action attribute
            type: "POST",
            data: formData,
            success: function (response) {
                 // Replace newlines with <br> for proper line breaks in HTML
                 let formattedResponse = response.response.replace(/\n/g, "<br>");
                
                 // Display response on the page
                 jQuery("#content").html('<h3>Response:</h3><p>' + formattedResponse + '</p>');
            },
            error: function (xhr, status, error) {
                console.error("Error: " + error);
                console.log(xhr.responseText);
                jQuery("#content").html('<h3>An error occurred. Please try again.</h3>');
            }
        });
    });
});
