let datasetTable = null;

// Formatting function for row details
function format(d) {
    // `d` is the original data object for the row
    return (
        `<strong class="emphasized-field">Summary</strong>` +
        `<p>${d.summary}</p>` +
        `<strong class="emphasized-field">Overall design</strong>` +
        `<p>${d.overall_design}</p>` +
        `<strong>Platform${d.platforms.length > 1 ? "s" : ""}:</strong> ` +
        `${d.platforms.join(",")}<br/>` +
        `<strong>Contact:</strong> ` +
        `${d.contact_name} <a href="mailto:${d.contact_email}">${d.contact_email}</a><br/>`
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
        row.child(format(row.data())).show();
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