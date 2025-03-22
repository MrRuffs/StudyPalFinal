let generated_flashcards = null
let deck_id = null
let subject_id = null

async function addGeneratedFlashcardsToDeck(deck_id, subject_id, flashcards) {
    const access_token = localStorage.getItem("token");

    if (!access_token) {
        console.error("No access token found. Please log in.");
        return;
    }

    // Transform flashcards into the correct format
    const formattedFlashcards = flashcards.map(([question, answer]) => ({
        question,
        answer
    }));

    try {
        const response = await fetch(`/add-generated-flashcards-to-deck/${deck_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({
                flashcards: formattedFlashcards,
                subject_id
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            // alert(responseData.message);
        } else {
            console.error("Error:", responseData);
        }
    } catch (error) {
        console.error("Error adding flashcards to deck:", error);
    }
}


function displayFlashcards(flashcards) {
    const flashcardContainer = document.getElementById("flashcard-container");
    flashcardContainer.innerHTML = "<h3 class='text-primary mb-4'>Generated Flashcards:</h3>";

    // Create a container with Bootstrap grid and custom classes
    const flashcardDeck = document.createElement("div");
    flashcardDeck.className = "row row-cols-1 row-cols-md-2 g-4 flashcard-row";

    flashcards.forEach(([question, answer], index) => {
        const col = document.createElement("div");
        col.className = "col flashcard-col";  // Added flashcard-col class
        
        const card = document.createElement("div");
        card.className = "card shadow-sm equal-height-card";  // Added equal-height-class
        
        card.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">Flashcard ${index + 1}</h5>
                <div class="card-text">
                    <p class="mb-3"><strong>Q:</strong> ${question}</p>
                    <p class="mb-0"><strong>A:</strong> ${answer}</p>
                </div>
            </div>
        `;

        col.appendChild(card);
        flashcardDeck.appendChild(col);
    });

    flashcardContainer.appendChild(flashcardDeck);
    // Show the approval buttons
    const approvalButtons = document.getElementById("approval-buttons");
    if (approvalButtons) {
        approvalButtons.style.display = "block";

        // Remove existing event listeners to prevent duplicates
        document.getElementById("approve-button").removeEventListener("click", handleApprove);
        document.getElementById("discard-button").removeEventListener("click", handleDiscard);

        // Add new event listeners
        document.getElementById("approve-button").addEventListener("click", handleApprove);
        document.getElementById("discard-button").addEventListener("click", handleDiscard);
    } else {
        console.error("Approval buttons not found in the DOM.");
    }
}

function showAlertModal(message) {
    // Set the message in the modal
    document.getElementById('alertMessage').innerText = message;

    // Show the modal
    const alertModal = new bootstrap.Modal(document.getElementById('alertModal'));
    alertModal.show();

    // Listen for the modal's hidden event
    document.getElementById('alertModal').addEventListener('hidden.bs.modal', function () {
        // Redirect to the home page
        window.location.href = "/home";
    });
}

// Example usage
document.addEventListener("DOMContentLoaded", async function () {
    const access_token = localStorage.getItem("token");

    if (!access_token) {
        // If the user is not logged in, redirect to the login page
        window.location.href = "/login";
        return;
    }

    try {
        // Call the backend to check if decks exist
        const response = await fetch("/check-deck-exists", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${access_token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();

        if (!responseData.decks_exist) {
            // If no decks exist, show the alert modal
            showAlertModal("No decks found. Please create a deck first.");
        }
    } catch (error) {
        console.error("Error checking decks:", error);
        // alert("An error occurred while checking decks. Please try again.");
    }

    try {
        // Fetch the user's decks
        const response = await fetch("/fetch-all-decks", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${access_token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        const decks = responseData.decks;

        console.log(decks);

        if (!decks || decks.length === 0) {
            // If no decks exist, show the alert modal
            showAlertModal("No decks found. Please create a deck first.");
            return;
        }

        // Populate the deck dropdown
        const deckSelect = document.getElementById("deck");
        const deckSubjectName = document.getElementById("deck-subject-name");

        decks.forEach(deck => {
            const option = document.createElement("option");
            option.value = deck.id; // Use the deck ID as the value
            option.textContent = deck.name; // Use the deck name as the display text
            deckSelect.appendChild(option);
        });

        // Update the subject when a deck is selected
        deckSelect.addEventListener("change", async function () {
            const selectedDeck = decks.find(deck => deck.id === parseInt(this.value));

            if (selectedDeck) {
                // Use await to get the resolved subject name
                const subjectName = await getSubjectName(selectedDeck.subject_id);
                deck_id = selectedDeck.id
                subject_id = selectedDeck.subject_id
                deckSubjectName.textContent = subjectName || "No subject";
            } else {
                deckSubjectName.textContent = "Loading...";
            }
        });

        // Trigger the change event to update the subject for the first deck
        deckSelect.dispatchEvent(new Event("change"));

        // Manually handle the first deck's subject
        const firstDeck = decks[0];
        if (firstDeck) {
            const subjectName = await getSubjectName(firstDeck.subject_id);
            deckSubjectName.textContent = subjectName || "No subject";
        }
    } catch (error) {
        console.error("Error fetching decks:", error);
        // alert("An error occurred while fetching decks. Please try again.");
    }
});

async function getSubjectName(subject_id) {
    const access_token = localStorage.getItem("token");

    if (!access_token) {
        // If the user is not logged in, redirect to the login page
        window.location.href = "/login";
        return;
    }

    try {
        // Fetch the subject name
        const response = await fetch(`/get-subject-name/${subject_id}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${access_token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        return responseData.subject_name;
    } catch (error) {
        console.error("Error fetching subject name:", error);
        return "Error fetching subject";
    }
}

document.getElementById("flashcard-form").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevents form submission and page reload

    // Show loading spinner
    document.getElementById("loading-spinner").style.display = "block";

    // Get input values
    const topic = document.getElementById("topic").value.trim();
    const amount = document.getElementById("amount").value.trim();
    const exam_board = document.getElementById("exam_board").value.trim() || "";

    try {
        const response = await fetch("/generate-flashcards", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic,
                exam_board,
                amount
            })
        });

        const responseData = await response.json();
        const flashcards = responseData.flashcards;
        generated_flashcards = flashcards;

        if (response.ok) {
            console.log("Generated flashcards:", flashcards);
            
            displayFlashcards(flashcards);
        } else {
            console.error("Error from API:", responseData);
        }
    } catch (error) {
        console.error("Error fetching flashcards:", error);
    } finally {
        // Hide loading spinner
        document.getElementById("loading-spinner").style.display = "none";
    }
});



async function handleApprove() {
    try {
        await addGeneratedFlashcardsToDeck(deck_id, subject_id, generated_flashcards);
        showAlertModal("Flashcards added to the deck successfully!");
    } catch (error) {
        console.error("Error adding flashcards to deck:", error);
        showAlertModal("Failed to add flashcards to the deck.");
    }
}

function handleDiscard() {
    const approvalButtons = document.getElementById("approval-buttons");
    if (approvalButtons) {
        approvalButtons.style.display = "none";
    }
    alert("Flashcards discarded.");
}