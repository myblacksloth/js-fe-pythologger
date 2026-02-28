/*
 * js-fe-pythologger
 * Copyright (C) 2026 Antonio Maulucci
 *
 * Licensed under GNU AGPL v3
 */

function log(source, severity, message) {
  try {
    var devLoggerBody = {
      message: message || "",
      source: source || "",
      level: severity || "info"
    };

    var devLoggerUri = "http://localhost:5000/logger";

    fetch(devLoggerUri, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(devLoggerBody)
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error("HTTP error! Status: " + response.status);
      }
      return response.json().catch(() => null);
    })
    .catch(function(err) {
      console.error("dev Logger error:", err);
    });

  } catch (e) {
    console.error("dev Logger exception:", e);
  }
}



function logVeryold(source, severity, message) {
  try {
    var devLoggerBody = JSON.stringify({
      message: message || "",
      source: source || "",
      level: severity || "info"
    });

    var devLoggerUri = "http://localhost:5000/logger";

    var xhr = new XMLHttpRequest();
    xhr.open("POST", devLoggerUri, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4 && xhr.status >= 400) {
        console.error("dev Logger error:", xhr.statusText);
      }
    };

    xhr.onerror = function () {
      console.error("dev Logger network error");
    };

    xhr.send(devLoggerBody);

  } catch (e) {
    console.error("dev Logger exception:", e);
  }
}




async function logg(source = "", severity = "info", message = "") {
  try {
    const response = await fetch("http://localhost:5000/logger", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        source,
        level: severity,
        message
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

  } catch (error) {
    console.error("dev Logger error:", error);
  }
}


