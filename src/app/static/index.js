var pubmedIds = [];
var emptyInputErrorMessage = "Please enter a PubMedId.";

function displayError(errorElement, message) {
    errorElement.innerText = message;
    errorElement.style.display = "block";
}

function parsePubmedIds(idsString, delimiter, errorElementId) {
    const errorElement = document.getElementById(errorElementId);
    errorElement.style.display = "none";

    idsString = idsString.trim();
    if (idsString.length === 0) {
        displayError(errorElement, emptyInputErrorMessage);
        return null;
    }

    let split_ids = idsString.split(delimiter);
    let parsed_ids = split_ids.map((x) => Number(x));

    const invalid_id_index = parsed_ids.findIndex(Number.isNaN);
    if (invalid_id_index != -1) {
        displayError(errorElement, `${split_ids[invalid_id_index].trim()} is not a valid PubMed id.`);
        return null;
    }
    return parsed_ids;
}

function addPubmedIds(ids) {
    ids = ids.filter((x) => !pubmedIds.includes(x));
    pubmedIds = pubmedIds.concat(ids);
    ids.map(addIdToTable);
}

function onClickAddPumbedIds() {
    const input = document.getElementById("add-ids-input");
    const ids = parsePubmedIds(input.value, ",", "id-form-input-error");
    if (ids != null) {
        input.value = "";
    }
    addPubmedIds(ids);
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
    let files = event.target.files;
    let file = files[0];
    console.log(file.name);

    let fileReader = new FileReader();

    fileReader.onload = function(){
        console.log("Content:");
        console.log(fileReader.result);
        ids = parsePubmedIds(fileReader.result, "\n", "id-form-file-error");
        addPubmedIds(ids);
    }

   fileReader.readAsText(file);
}

function submitPubmedIds(event) {
    event.preventDefault();

    if (pubmedIds.length === 0) {
        errorElement = document.getElementById("id-form-input-error");
        const errorElement = document.getElementById(errorElementId);
        displayError(errorElement, emptyInputErrorMessage);
        return;
    }

    const pubmedIdsInput = document.querySelector('input[name="pubmed_ids"]');
    pubmedIdsInput.value = JSON.stringify(pubmedIds);

    const form = document.getElementById("id-form");
    form.submit();
}

window.onload = () => {
    const addButton = document.getElementById("id-form-add-btn");
    const addIdInput = document.getElementById("add-ids-input");
    const form = document.getElementById("id-form");
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
}