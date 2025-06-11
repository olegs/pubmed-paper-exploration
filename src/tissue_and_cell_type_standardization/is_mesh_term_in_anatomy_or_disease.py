import xml.etree.ElementTree as ET
from typing import Dict, Set

def get_all_synonyms_for_mesh_entry(record: ET.Element) -> Set[str]:
    """
    Gets all the synonyms for a term in MeSH.
    
    :param descriptor_record: <DescritporRecord> XML element for the term.
    :return: A set containing all the synonyms for the MeSH entry.
    """
    descriptor_name_element = record.find('DescriptorName/String')
    if descriptor_name_element is None:
        return {}
    all_terms_for_entry = {descriptor_name_element.text.strip().lower()}

    for term in record.findall('.//TermList/Term'):
        term_name_element = term.find('String')
        if term_name_element is not None:
            all_terms_for_entry.add(term_name_element.text.strip().lower())
    return all_terms_for_entry

def build_mesh_lookup(xml_file_path: str) -> Dict[str, Set[str]]:
    """
    Parses a MeSH XML descriptor file to build a lookup table.

    The function reads the XML file and creates a dictionary that maps each
    MeSH term (including entry terms/synonyms) to a set of its
    corresponding MeSH tree numbers.

    :param xml_file_path: The full path to the MeSH descriptor XML file
                       (e.g., 'path/to/desc2024.xml').

    :return: A dictionary where keys are lowercased MeSH terms and values are
        sets of tree numbers. Returns an empty dictionary if the file
        cannot be parsed.
    """
    print(f"Building MeSH lookup from '{xml_file_path}'...")
    mesh_lookup = {}
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for record in root.findall('DescriptorRecord'):
            tree_numbers = {
                tn.text.strip() for tn in record.findall('.//TreeNumber') if tn.text
            }
            if not tree_numbers:
                continue

            all_terms_for_record = get_all_synonyms_for_mesh_entry(record) 
            
            for term_str in all_terms_for_record:
                if term_str not in mesh_lookup:
                    mesh_lookup[term_str] = set()
                mesh_lookup[term_str].update(tree_numbers)

        print(f"Lookup built successfully. Found {len(mesh_lookup)} unique terms.")
        return mesh_lookup

    except FileNotFoundError:
        print(f"Error: The file was not found at '{xml_file_path}'")
        return {}
    except ET.ParseError as e:
        print(f"Error: Failed to parse the XML file. {e}")
        return {}


def is_mesh_term_in_anatomy_or_disease(term: str, mesh_lookup: Dict[str, Set[str]]) -> bool:
    """
    Checks if a MeSH term is in the Anatomy or Disease category using a lookup table.

    :param term: The MeSH term to check (e.g., "Heart", "Lung").
    :param mesh_lookup: A pre-built dictionary mapping terms to tree numbers.

    :return: True if the term is in the Anatomy or Disease categories, False otherwise.
    """
    if not term:
        return False
        
    search_term = term.strip().lower()

    tree_numbers = mesh_lookup.get(search_term)

    if not tree_numbers:
        return False

    # Check if any tree number starts with 'A' or 'C' which are the first
    # letters in tree numbers for anatomy and disease terms
    # We check whether a term is a  disease because cancer samples end up being
    # classified as diseases in MeSH
    for tn in tree_numbers:
        if tn.startswith("A") or tn.startswith("C"):
            return True
            
    return False


if __name__ == "__main__":
    mesh_xml_file = "desc2025.xml"

    # This might take a few seconds.
    local_mesh_db = build_mesh_lookup(mesh_xml_file)

    if local_mesh_db:
        print("-" * 30)

        # Example 1: A term that IS in the Anatomy category
        anatomy_term = "Femur"
        is_anatomy = is_mesh_term_in_anatomy_or_disease(anatomy_term, local_mesh_db)
        print(f"Is '{anatomy_term}' an anatomy or disease term? {'Yes' if is_anatomy else 'No'}\n")

        # Example 2: A synonym that IS in the Anatomy category
        anatomy_term_2 = "Blood" # A synonym for Cornea
        is_anatomy_2 = is_mesh_term_in_anatomy_or_disease(anatomy_term_2, local_mesh_db)
        print(f"Is '{anatomy_term_2}' an anatomy term? {'Yes' if is_anatomy_2 else 'No'}\n")

        # Example 3: A term that IS NEITHER in the Anatomy category nor Disease category
        non_anatomy_term = "Aspirin"
        is_anatomy_3 = is_mesh_term_in_anatomy_or_disease(non_anatomy_term, local_mesh_db)
        print(f"Is '{non_anatomy_term}' an anatomy term? {'Yes' if is_anatomy_3 else 'No'}\n")

        # Example 4: A term that IS in the Disease category
        non_anatomy_term = "Breast Cancer"
        is_anatomy_4 = is_mesh_term_in_anatomy_or_disease(non_anatomy_term, local_mesh_db)
        print(f"Is '{non_anatomy_term}' an anatomy term? {'Yes' if is_anatomy_4 else 'No'}\n")
