var server_host = "nebula.local";

processLogin = function () {
  const username = document.getElementById("usernameInput").value.trim();
  const errorMessage = document.getElementById("errorMessage");

  if (username === "") {
    errorMessage.classList.remove("hidden"); // Show the error message
    usernameInput.style.borderColor = "red";
  } else {
    errorMessage.classList.add("hidden"); // Hide the error message
    // Proceed with login functionality
    // console.log("Logging in as:", username);
    const api = new XMLHttpRequest();
    usernameInput.style.borderColor = "";
    const url = "http://" + server_host + ":8642/api/login?username=" + username;
    api.open("POST", url, true);
    api.withCredentials = true;

    api.onload = function () {
      if (api.status >= 200 && api.status < 300) {
        // Successfully received response, now insert the new HTML content
        document.open(); // Open the document for writing
        document.write(api.responseText); // Overwrite the entire document with new content
        document.close();
        console.log("response text recieved");
      } else {
        showAlert(api.status);
      }
    };

    // Handle network errors
    api.onerror = function () {
      console.error("Request failed.");
    };

    // Send the request
    api.send();
    // Attach the click event listener to the login button
  }
};

loginBtn.addEventListener("click", function (event) {
  event.preventDefault(); // Prevent default form submission (if inside a form)
  processLogin(); // Call the processLogin function
});
