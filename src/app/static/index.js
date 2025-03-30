class ParsingError extends Error {
    constructor (message, badData) {
        super(message);
        this.badData = badData;
    }
}

var pubmedIds = [];
var emptyInputErrorMessage = "Please enter a PubMed ID.";
var successToastBootstrap = null;
var errorToastBootstrap = null;

function displayError(errorElement, message) {
    errorElement.innerText = message;
    errorElement.style.display = "block";
}

function parsePubmedIds(idsString, delimiter) {
    // Returns list of integers or throws exception if one of the PubMed IDs is not valid.
    idsString = idsString.trim();
    if (idsString.length === 0) {
        displayError(errorElement, emptyInputErrorMessage);
        return null;
    }

    let splitIds = idsString.split(delimiter);
    let parsedIds = splitIds.map((x) => Number(x));

    const invalidIdIndex = parsedIds.findIndex(Number.isNaN);
    if (invalidIdIndex != -1) {
        throw new ParsingError("Invalid PubMed ID", splitIds[invalidIdIndex].trim());
    }
    return parsedIds;
}

function addPubmedIds(ids) {
    ids = ids.filter((x) => !pubmedIds.includes(x));
    pubmedIds = pubmedIds.concat(ids);
    ids.map(addIdToTable);
}

function onClickAddPumbedIds() {
    const input = document.getElementById("add-ids-input");
    const errorElement = document.getElementById("id-form-input-error");
    errorElement.style.display = "none";
    if (input.value.trim().length === 0) {
        displayError(errorElement, emptyInputErrorMessage);
        return;
    }
    try {
        const ids = parsePubmedIds(input.value, ",", "id-form-input-error");
        input.value = "";
        addPubmedIds(ids);
    } catch (e) {
        displayError(errorElement, `${e.badData} is not a valid PubMed id.`);
        return;
    }
}

function removeItemOnce(arr, value) {
    var index = arr.indexOf(value);
    if (index > -1) {
      arr.splice(index, 1);
    }
    return arr;
  }

function deletePubmedId(pubmedId) {
    const idIndex = pubmedIds.indexOf(pubmedId);
    removeItemOnce(pubmedIds, pubmedId);
    const tbody = document.querySelector("table.table > tbody");
    tbody.removeChild(tbody.childNodes[idIndex+1]);
}

function addIdToTable(pubmedId) {
    const tbody = document.querySelector("table.table > tbody");
    const newRow = document.createElement("tr");
    const idCell = document.createElement("td");
    idCell.innerText = pubmedId.toString();

    const buttonCell = document.createElement("td");
    const button = document.createElement("button");
    button.type = "button";
    button.classList.add("btn");
    button.classList.add("btn-danger");
    button.innerText = "Delete";
    buttonCell.appendChild(button);
    button.addEventListener("click", () => {
        deletePubmedId(pubmedId);
    });

    newRow.appendChild(idCell);
    newRow.appendChild(buttonCell);
    tbody.appendChild(newRow);
}

function onFileUpload(event) {
    const errorElement = document.getElementById("id-form-file-error");
    errorElement.style.display = "none";

    let files = event.target.files;
    let file = files[0];

    let fileReader = new FileReader();

    fileReader.onload = function(){
        try {
            ids = parsePubmedIds(fileReader.result, "\n", "id-form-file-error");
            addPubmedIds(ids);
            triggerImportSuccessToast(ids.length, file.name);
        } catch (e) {
            console.log(e);
            displayError(errorElement, `${e.badData} is not a valid PubMed id.`);
        }
    }

   fileReader.readAsText(file);
}

function triggerImportSuccessToast(nPmids, filename) {
    const toastMessage = document.getElementById("toast-full-message");
    toastMessage.innerText = `Successfully imported ${nPmids} PubMed IDs from ${filename}.`
    successToastBootstrap.show();
}

function changeSubmitButtonToLoadingIndicator() {
    const submitButton = document.getElementById("submit-button");
    submitButton.disabled = true;
    const submitButtonLabel = document.getElementById("submit-button-label");
    submitButtonLabel.style.display = "none";
    const submitButtonLoadingIndicator = document.getElementById("submit-button-loading-indicator");
    submitButtonLoadingIndicator.style.display = "inline";
}

function submitPubmedIds(event) {
    event.preventDefault();

    if (pubmedIds.length === 0) {
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

function deleteAllIds() {
    const tbody = document.querySelector("table.table > tbody");
    tbody.innerHTML = "";
    pubmedIds = [];
}

function setUpEventsAndToasts() {
    const addButton = document.getElementById("id-form-add-btn");
    const addIdInput = document.getElementById("add-ids-input");
    const form = document.getElementById("id-form");
    const deleteAllButton = document.getElementById("delete-all-btn")
    addButton.addEventListener("click",
        (event) => {
            onClickAddPumbedIds();
        }
    );

    form.addEventListener("submit",
        (event) => {
            submitPubmedIds(event);
        }
    );

    addIdInput.addEventListener("keypress", 
        (event) => {
            if (event.keyCode == 13) {
                event.preventDefault();
                onClickAddPumbedIds();
            }
        }
    );

    deleteAllButton.addEventListener("click",
        (event) => {
            deleteAllIds();
        }
    );

    const sucessToast = document.getElementById("import-success-toast");
    successToastBootstrap = bootstrap.Toast.getOrCreateInstance(sucessToast);

    const errorToast = document.getElementById("error-toast");
    errorToastBootstrap = bootstrap.Toast.getOrCreateInstance(errorToast);
}

setUpEventsAndToasts();