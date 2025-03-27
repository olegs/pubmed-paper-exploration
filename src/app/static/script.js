var pubmedIds = [];
var emptyInputErrorMessage = "Please enter a PubMedId.";

function displayError(errorElement, message) {
    errorElement.innerText = message;
    errorElement.style.display = "block";
}

function parsePubmedIds(idsString, delimiter, errorElementId) {
    const errorElement = document.getElementById(errorElementId);
    errorElement.style.display = "none";

    idsString = idsString.trim()
    if (idsString.length === 0) {
        displayError(errorElement, emptyInputErrorMessage);
        return null;
    }

    let split_ids = idsString.split(delimiter);
    let parsed_ids = split_ids.map((x) => Number(x));
    parsed_ids = parsed_ids.filter((x) => !pubmedIds.includes(x));

    const invalid_id_index = parsed_ids.findIndex(Number.isNaN);
    if (invalid_id_index != -1) {
        displayError(errorElement, `${split_ids[invalid_id_index]} is not a valid PubMedId.`);
        return null;
    }
    return parsed_ids;
}

function onAddPumbedIds() {
    const input = document.getElementById("id-form-input");
    const ids = parsePubmedIds(input.value, ",", "id-form-input-error");
    if (ids != null) {
        input.value = "";
    }
    pubmedIds = pubmedIds.concat(ids);
    ids.map(addIdToTable);
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

window.onload = () => {
    const addButton = document.getElementById("id-form-add-btn");
    addButton.addEventListener("click",
        (event) => {
            onAddPumbedIds();
        }
    )
}