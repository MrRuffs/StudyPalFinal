document.getElementById("login-form").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevents form submission and page reload

    // Get input values
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/login-api", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            console.log(responseData)
            localStorage.setItem('token', responseData.access_token);   
            window.location.href = "/home"
        } else {
            console.error("Error:", responseData);
            showAlertModal(responseData.message)
        }
    } catch (error) {
        console.error("Error signing in:", error);
        showAlertModal(error)
    }
});



function showAlertModal(message) {
    // Set the message in the modal
    document.getElementById('alertMessage').innerText = message;

    // Show the modal
    const alertModal = new bootstrap.Modal(document.getElementById('alertModal'));
    alertModal.show();
}