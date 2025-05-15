var FetchMsgId;
var lastMessageTime = 0;

function showAlert(errorCode){
  if (errorCode === 404){
    alert("Resourse does not exist");
  } else if (errorCode === 401){
    alert("User not logged in");
  } else if(errorCode === 500){
    alert("Server Error, Closing and reopening the website recommended");
  }else if(errorCode === 405){
    alert("Request Not allowed to server");
  } else {
    alert("Unknown Error, Closing and reopening the website recommended");
  }
};

function addMessage(text) {
  // Select the message window container
  const messageWindow = document.getElementById("messageWindow");

  // Create a new div element for the message
  const newMessage = document.createElement("div");

  // Add the "message" class to apply the styling
  newMessage.classList.add("message");

  // Set the text content of the new message
  newMessage.textContent = text;

  // Append the new message to the message window
  messageWindow.appendChild(newMessage);


  const div = document.getElementById("messageWindow");
  div.scrollTop = div.scrollHeight;
}

sendMessage = function () {
  const message = document.getElementById("messageInput").value.trim();
  const url = "http://" + server_host + ":8642/api/message";
  if (message !== "") {
    document.getElementById("messageInput").value = "";
    const api = new XMLHttpRequest();
    api.open("POST", url, true);
    api.withCredentials = true;
    api.setRequestHeader("Content-Type", "application/json");
    api.onload = () => {
      if (api.readyState == 4 && api.status == 201) {
        console.log(api.responseText);
      } else {
        showAlert(api.status);
      }
    };

    const body = JSON.stringify({
      msg: message,
    });
    console.log(body);
    api.send(body);

    // Handle network errors
    api.onerror = function () {
      console.error("Request failed.");
    };
  }
};

var sendButton = document.getElementById("sendButton");
sendButton.addEventListener("click", function (event) {
  event.preventDefault(); // Prevent default form submission (if inside a form)
  sendMessage(); // Call the processLogin function
  const div = document.getElementById("messageWindow");
  div.scrollTop = div.scrollHeight;
});

processLogout = function () {
  const xhr = new XMLHttpRequest();

  const url = "http://" + server_host + ":8642/api/login";
  xhr.open("DELETE", url, true);
  xhr.withCredentials = true;

  xhr.onload = function () {
    if (xhr.status >= 200 && xhr.status < 300) {
      // Successfully received response, now insert the new HTML content
      document.open(); // Open the document for writing
      document.write(xhr.responseText); // Overwrite the entire document with new content
      document.close();
      console.log("response text recieved");
      clearInterval(FetchMsgId);
      FetchMsgId = null;
    } else {
      showAlert(xhr.status);
    }
  };

  xhr.send();
};

var loButton = document.getElementById("logoutButton");
loButton.addEventListener("click", function (event) {
  event.preventDefault(); // Prevent default form submission (if inside a form)
  processLogout(); // Call the processLogin function
});

getPrevMsg = function () {
  const xhr = new XMLHttpRequest();
  const url = "http://" + server_host + ":8642/api/message";

  xhr.open("GET", url, true);
  xhr.withCredentials = true;
  xhr.responseType = "json";
  xhr.send();

  xhr.onload = function () {
    if ((xhr.status >= 200) & (xhr.status < 300)) {
      let msg_arr;

      if (xhr.responseType === "json") {
        console.log("json type received");
        msg_arr = xhr.response;
      } else {
        console.log("parshing response into JSON");
        msg_arr = JSON.parse(xhr.responseText);
      }

      for (const msg of msg_arr) {
        addMessage(msg.username + ": " + msg.msg);
        lastMessageTime = Math.max(lastMessageTime, msg.send_time);
      }
    } else {
      showAlert(xhr.status);
    }
  };
};

fetchNewMsg = function () {
  const xhr = new XMLHttpRequest();
  const url =
    "http://" + server_host + ":8642/api/message?time=" + lastMessageTime;
  xhr.open("GET", url, true);
  xhr.withCredentials = true;
  xhr.send();

  xhr.onload = function () {
    if ((xhr.status >= 200) & (xhr.status < 300)) {
      let msg_arr;

      if (xhr.responseType === "json") {
        console.log("json type received");
        msg_arr = xhr.response;
      } else {
        console.log("parshing response into JSON");
        msg_arr = JSON.parse(xhr.responseText);
      }

      for (const msg of msg_arr) {
        // if(msg.msg_id != lastMessageId){
        addMessage(msg.username + ": " + msg.msg);
        // } else {
        // console.log('msg.msg_is == lastMessageId')
        // }
        lastMessageTime = Math.max(lastMessageTime, msg.send_time);
      }
    } else {
      showAlert(xhr.status);
    }
  };
};

setup = function () {
  FetchMsgId = setInterval(fetchNewMsg, 1000);
};

setup();

// Delete code below this comment
