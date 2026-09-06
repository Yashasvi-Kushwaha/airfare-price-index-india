document.getElementById("login-form").addEventListener("submit", function(e) {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    // Demo-only check — not real authentication.
    // Replace with real auth if this ever moves beyond prototype stage.
    if (username && password) {
        sessionStorage.setItem("loggedIn", "true");
        window.location.href = "index.html";
    } else {
        document.getElementById("login-error").textContent = "Please enter both fields.";
    }
});