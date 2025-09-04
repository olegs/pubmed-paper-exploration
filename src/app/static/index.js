const pubmedIds = [];
const emptyInputErrorMessage = "Please enter a PubMed ID.";
let errorToastBootstrap = null;

function displayError(errorElement, message) {
    errorElement.innerText = message;
    errorElement.style.display = "block";
}

function changeSubmitButtonToLoadingIndicator() {
    const submitButton = document.getElementById("submit-button");
    submitButton.disabled = true;
    const submitButtonLabel = document.getElementById("submit-button-label");
    submitButtonLabel.style.display = "none";
    const submitButtonLoadingIndicator = document.getElementById("submit-button-loading-indicator");
    submitButtonLoadingIndicator.style.display = "inline";
}

function submitQuery(event) {
    event.preventDefault();
    queryInput = document.getElementById("query-input");

    if (pubmedIds.length === 0 && queryInput.value === "") {
        const errorElement = document.getElementById("id-form-input-error");
        displayError(errorElement, emptyInputErrorMessage);
        triggerErrorToast("PubMed IDs have not been entered", "No PubMed IDs have been entered. Please enter or import PubMed IDs.")
        return;
    }

    changeSubmitButtonToLoadingIndicator();

    const pubmedIdsInput = document.querySelector('input[name="pubmed_ids"]');
    pubmedIdsInput.value = JSON.stringify(pubmedIds);

    const form = document.getElementById("id-form");
    form.submit();
}

function triggerErrorToast(shortMessage, fullMessage) {
    const shortMessageElement = document.getElementById("error-short-message");
    shortMessageElement.innerText = shortMessage;
    const fullMessageElement = document.getElementById("error-full-message");
    fullMessageElement.innerText = fullMessage;
    errorToastBootstrap.show();
}

function setUpEventsAndToasts() {
    const form = document.getElementById("id-form");
    form.addEventListener("submit",
        (event) => {
            submitQuery(event);
        }
    );

    const errorToast = document.getElementById("error-toast");
    errorToastBootstrap = bootstrap.Toast.getOrCreateInstance(errorToast);
}

setUpEventsAndToasts();