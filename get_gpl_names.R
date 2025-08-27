# A script to download the latest GEOMetaDb database,
# extract all GPL platform IDs and their corresponding names,
# and save the mapping to a JSON file.

# Install and load required packages
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
if (!require("GEOmetadb", quietly = TRUE))
    install.packages("GEOmetadb")
list.of.packages <- c("RSQLite", "jsonlite")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)

options(timeout = 3000)

library(GEOmetadb)
library(RSQLite)
library(jsonlite)

# --- 1. Download the latest GEOMetaDb database ---
# The getSQLiteFile() function downloads the latest version of the database
# from the Bioconductor server. It's a large file, so this may take some time.
# The `if` statement checks if the file already exists to avoid re-downloading.
if (!file.exists("GEOmetadb.sqlite")) {
  cat("Downloading the latest GEOMetaDb.sqlite file...\n")
  geometadbfile <- getSQLiteFile()
  cat("Download complete.\n")
} else {
  cat("GEOMetaDb.sqlite already exists. Using the local copy.\n")
  geometadbfile <- "GEOmetadb.sqlite"
}

# --- 2. Connect to the SQLite database ---
# Establish a connection to the downloaded database file.
conn <- dbConnect(SQLite(), geometadbfile)
cat("Connected to the database.\n")

# --- 3. Query the 'gpl' table for platform IDs and names ---
# The `gpl` table contains all platform information.
# We query for the `gpl` column (the ID) and the `title` column (the name).
cat("Querying the database for GPL platforms...\n")
query_result <- dbGetQuery(conn, "SELECT gpl, title FROM gpl")
cat("Query complete. Found", nrow(query_result), "platforms.\n")

print(query_result$gpl)

# --- 4. Disconnect from the database ---
# It's important to close the connection when you're done.
dbDisconnect(conn)
cat("Disconnected from the database.\n")

# --- 5. Format the data and write to a JSON file ---
# Create a named list for the JSON output.
# The keys will be the GPL IDs, and the values will be the titles.
gpl_map <- split(query_result, query_result$gpl)
gpl_map <- lapply(gpl_map, function (gpl_row) { gpl_row$title })

# Write the R list to a JSON file.
# `pretty = TRUE` makes the JSON file human-readable.
cat("Writing the GPL mapping to 'gpl_platform_map.json'...\n")
write_json(gpl_map, "gpl_platform_map.json", pretty = TRUE, auto_unbox=TRUE)
cat("Successfully created 'gpl_platform_map.json'.\n")

# Optional: Clean up by removing the database file.
# Uncomment the line below if you want to remove the large database file
# after the script has finished.
# file.remove("GEOmetadb.sqlite")

