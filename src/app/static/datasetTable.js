let datasetTable = null;

function get_fields_html(dataset) {
    let no_tissue = dataset.tissue_standardized.every(value => value === null);
    let no_disease = dataset.disease_standardized.every(value => value === null);
    let no_cell_type = dataset.cell_type_standardized.every(value => value === null);

    if (no_tissue && no_cell_type && no_disease) {
        return "";
    }

    let fields_html = "<p>";
    if (!no_disease) {
        fields_html += `<strong>(Inferred) Diseases: </strong> ${dataset.disease_standardized.join(", ")}<br/>`;
    }
    if (!no_tissue) {
        fields_html += `<strong>(Inferred) Tissues: </strong> ${dataset.tissue_standardized.join(", ")}<br/>`;
    }
    if (!no_cell_type) {
        fields_html += `<strong>(Inferred) Cell types: </strong> ${dataset.cell_type_standardized.join(", ")}<br/>`;
    }
    fields_html += "</p>"

    return fields_html
}

// Formatting function for row details
function get_expanded_html(dataset) {
    let fields_html = get_fields_html(dataset);
    return (
        `<strong class="emphasized-field">Summary</strong>` +
        `<p>${dataset.summary}</p>` +
        `<strong class="emphasized-field">Overall design</strong>` +
        `<p>${dataset.overall_design}</p>` +
        fields_html +
        `<strong>Platform${dataset.platforms.length > 1 ? "s" : ""}:</strong> ` +
        `${dataset.platforms.join(",")}<br/>` +
        `<strong>Contact:</strong> ` +
        `${dataset.contact_name} <a href="mailto:${dataset.contact_email}">${dataset.contact_email}</a><br/>`
    );
}


function expandRowClickHandler(e) {
    let tr = e.target.closest('tr');
    let row = datasetTable.row(tr);

    if (row.child.isShown()) {
        // This row is already open - close it
        row.child.hide();
    }
    else {
        // Open this row
        row.child(get_expanded_html(row.data())).show();
    }
}

// Add event listener for opening and closing details

function downloadURI(uri, name) {
    var link = document.createElement("a");
    link.download = name;
    link.href = uri;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    delete link;
}

function downloadSupplementaryFilesClickHandler(e) {
    let tr = e.target.closest('tr');
    let dataset = datasetTable.row(tr).data();
    let files = dataset.supplementary_files;
    let fileanmes = dataset.supplementary_filenames;
    for (let i = 0; i < files.length; i++) {
        downloadURI(files[i], fileanmes[i]);
    }

}

// Download button event listener


document.addEventListener("DOMContentLoaded", function () {
    datasetTable = new DataTable('#datasets-table', {
        data: geo_datasets,
        columns: [
            { data: 'id' },
            { data: 'title' },
            { data: 'organisms' },
            { data: 'experiment_type' },
            { data: 'sample_count' },
            {
                className: "dt-download",
                orderable: false,
                data: null,
                defaultContent: '<button role="button" title="Download supplementary files" aria-label="Download supplementary files"><i class="fa-solid fa-download"></i></button>'
            },
        ]
    });
    datasetTable.on('click', 'tr:not([data-dt-row]) td:not(.dt-download)', expandRowClickHandler);
    datasetTable.on('click', 'tbody td.dt-download', downloadSupplementaryFilesClickHandler);
});