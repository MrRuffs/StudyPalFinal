document.addEventListener("DOMContentLoaded", function () {
    const access_token = localStorage.getItem("token");

    if (!access_token) {
        console.error("Token is missing!");
        window.location.href = "/login";
        return;
    }

    // Fetch and display the username
    fetchUsername();

    // Add event listener for the Sign Out button
    const signOutButton = document.getElementById("sign-out-button");
    if (signOutButton) {
        signOutButton.addEventListener("click", function () {
            localStorage.removeItem("token");
            window.location.href = "/login";
        });
    }

    // Fetch and display subjects
    fetchSubjects();
});

// Function to fetch and display the username
async function fetchUsername() {
    try {
        const response = await fetch("/get-username", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            }
        });

        const responseData = await response.json();

        if (response.ok) {
            document.getElementById("username").textContent = responseData.username;
        } else {
            console.error("Error:", responseData);
            window.location.href = "/login";
        }
    } catch (error) {
        console.error("Error fetching username:", error);
        document.getElementById("username").textContent = "User";
    }
}

// Function to fetch and display subjects
async function fetchSubjects() {
    const access_token = localStorage.getItem("token");
    try {
        const response = await fetch("/get-subjects", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${access_token}`
            }
        });

        const responseData = await response.json();

        if (response.ok) {
            const subjectCardsContainer = document.getElementById("subjectCards");
            subjectCardsContainer.innerHTML = "";

            if (responseData.length > 0) {
                responseData.forEach(subject => {
                    const subjectCard = document.createElement("div");
                    subjectCard.className = "col-md-4 mb-4";
                    subjectCard.innerHTML = `
                        <div class="card subject-card">
                            <div class="card-body">
                                <h5 class="card-title">${subject.name}</h5>
                                <p class="card-text">Click to manage decks.</p>
                                <button style="margin: 5px" class="btn btn-primary btn-sm" onclick="openViewDecksModal(${subject.id}, '${subject.name}')">Edit Decks</button>
                                <button style="margin: 5px" class="btn btn-danger btn-sm" onclick="openConfirmationModal('Are you sure you want to delete this subject and all its decks?', ${subject.id})">Delete Subject</button>
                            </div>
                        </div>
                    `;
                    subjectCardsContainer.appendChild(subjectCard);
                });
            } else {
                subjectCardsContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <p>No subjects found. Create a new subject to get started!</p>
                    </div>
                `;
            }
        } else {
            console.error("Error:", responseData);
        }
    } catch (error) {
        console.error("Error fetching subjects:", error);
    }
}

// Function to open the View Decks modal
async function openViewDecksModal(subjectId, subjectName) {
    document.getElementById("subjectNameInModal").textContent = subjectName;
    document.getElementById("subjectNameInModal").setAttribute("data-subject-id", subjectId);

    const decks = await fetchDecks(subjectId);
    const decksList = document.getElementById("decksList");
    decksList.innerHTML = "";

    decks.forEach(deck => {
        // Truncate the deck name if it exceeds 30 characters
        const truncatedDeckName = deck.name.length > 30 ? deck.name.substring(0, 30) + "..." : deck.name;

        const deckItem = document.createElement("div");
        deckItem.className = "deck-item";
        deckItem.innerHTML = `
            <div class="deck-content">
                <h6 class="deck-name">${truncatedDeckName}</h6>
                <p class="deck-description">Click to study this deck.</p>
            </div>
            <div class="deck-actions">
                <button class="btn btn-success btn-sm" onclick="addFlashcards(event, ${deck.id})">Add Flashcards</button>
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); openConfirmationModal('Are you sure you want to delete this deck?', null, ${deck.id})">Delete Deck</button>
            </div>
        `;

        deckItem.addEventListener("click", () => {
            window.location.href = `/open-deck/${deck.id}`;
        });

        decksList.appendChild(deckItem);
    });

    const viewDecksModal = new bootstrap.Modal(document.getElementById("viewDecksModal"));
    viewDecksModal.show();
}
// Function to fetch decks for a subject
async function fetchDecks(subjectId) {
    const access_token = localStorage.getItem("token");
    try {
        const response = await fetch(`/get-decks?subject_id=${subjectId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${access_token}`
            }
        });

        const responseData = await response.json();

        if (response.ok) {
            return responseData.decks;
        } else {
            console.error("Error:", responseData);
            return [];
        }
    } catch (error) {
        console.error("Error fetching decks:", error);
        return [];
    }
}

// Function to handle the Create Deck form submission
document.getElementById("createDeckFormInModal").addEventListener("submit", async function (event) {
    event.preventDefault();

    const deckName = document.getElementById("deckNameInModal").value;
    const subjectId = document.getElementById("subjectNameInModal").getAttribute("data-subject-id");

    if (!deckName || !subjectId) {
        alert("Deck name is required!");
        return;
    }

    try {
        const response = await fetch("/create-deck-api", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: deckName,
                subjectId: subjectId
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            // alert("Deck created successfully!");
            document.getElementById("deckNameInModal").value = ""; // Clear the input field

            // Close the modal
            const viewDecksModal = bootstrap.Modal.getInstance(document.getElementById("viewDecksModal"));
            viewDecksModal.hide();

            // Refresh the decks list
            await fetchDecks(subjectId);
            openViewDecksModal(subjectId, document.getElementById("subjectNameInModal").textContent);
        } else {
            // alert(`Error: ${responseData.message}`);
        }
    } catch (error) {
        console.error("Error creating deck:", error);
        // alert("An error occurred while creating the deck. Please try again.");
    }
});

// Function to open the confirmation modal
function openConfirmationModal(message, subjectId = null, deckId = null) {
    document.getElementById("confirmationMessage").textContent = message;
    currentSubjectIdToDelete = subjectId;
    currentDeckIdToDelete = deckId;

    const confirmationModal = new bootstrap.Modal(document.getElementById("confirmationModal"));
    confirmationModal.show();
}

// Function to handle confirmed deletion
document.getElementById("confirmDeleteButton").addEventListener("click", async function () {
    if (currentSubjectIdToDelete !== null) {
        await deleteSubject(currentSubjectIdToDelete);
        currentSubjectIdToDelete = null;
    } else if (currentDeckIdToDelete !== null) {
        await deleteDeck(currentDeckIdToDelete);
        currentDeckIdToDelete = null;
    }

    const confirmationModal = bootstrap.Modal.getInstance(document.getElementById("confirmationModal"));
    confirmationModal.hide();
});

// Function to delete a subject
async function deleteSubject(subjectId) {
    try {
        const response = await fetch("/delete-subject-api", {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                subjectId: subjectId
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            //alert("Subject deleted successfully!");
            fetchSubjects(); // Refresh the subjects list
        } else {
            //alert(`Error: ${responseData.message}`);
        }
    } catch (error) {
        console.error("Error deleting subject:", error);
        //alert("An error occurred while deleting the subject. Please try again.");
    }
}

// Function to delete a deck
async function deleteDeck(deckId) {
    try {
        const response = await fetch("/delete-deck-api", {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                deckId: deckId
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            //alert("Deck deleted successfully!");
            const subjectId = document.getElementById("subjectNameInModal").getAttribute("data-subject-id");
            await fetchDecks(subjectId); // Refresh the decks list
            openViewDecksModal(subjectId, document.getElementById("subjectNameInModal").textContent); // Reopen the modal with updated decks
            const confirmationModal = bootstrap.Modal.getInstance(document.getElementById("confirmationModal"));
            confirmationModal.hide(); // Hide the confirmation modal
            document.querySelector(".modal-backdrop").remove(); // Manually remove the backdrop (if necessary)
        } else {
            //alert(`Error: ${responseData.message}`);
        }
    } catch (error) {
        console.error("Error deleting deck:", error);
        //alert("An error occurred while deleting the deck. Please try again.");
    }
}

// Function to handle the Create Subject form submission
document.getElementById("createSubjectForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const access_token = localStorage.getItem("token");
    const subjectName = document.getElementById("subjectName").value;

    try {
        const response = await fetch("/create-subject-api", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${access_token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: subjectName
            })
        });

        const responseData = await response.json();
        if (response.ok) {
            //alert("Subject created successfully!");
            document.getElementById("subjectName").value = "";
            fetchSubjects(); // Refresh the subjects list
        }
    } catch (error) {
        console.error("Error creating subject", error);
    }
});

// Function to handle adding flashcards
function addFlashcards(event, deckId) {
    event.stopPropagation();
    window.location.href = `/create-flashcards-page/${deckId}`;
}

