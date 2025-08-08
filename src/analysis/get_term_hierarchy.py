from src.analysis.standardization_resources import StandardizationResources

def get_hierarchy_for_experiment_type(experiment_type: str):
    return experiment_type.split(" by ")

def get_tree_number(term, mesh_lookup):
    tree_numbers = mesh_lookup[term].tree_numbers
    priority_prefixes = [
        "A11.118",
        "A15.145",
        "C08.381",
        "C19.246",
        "C06.552",
        "C01.920"
    ]
    for prefix in priority_prefixes:
        parent_tree_number = next((tn for tn in tree_numbers if tn.startswith(prefix)), None)
        if parent_tree_number:
            return parent_tree_number
    
    return next(iter(tree_numbers))

def get_hierarchy(term: str, standardization_resources: StandardizationResources):
    if term is None:
        return None
    term_not_in_mesh = term not in standardization_resources.mesh_lookup
    if term_not_in_mesh:
        return get_hierarchy_for_experiment_type(term)
    
    tree_number = get_tree_number(term, standardization_resources.mesh_lookup)
    tree_number_separator = "."
    segments = tree_number.split(tree_number_separator)
    hierarhchy = []
    for i in range(len(segments)):
        current_tree_number = tree_number_separator.join(segments[:i+1])
        hierarhchy.append(standardization_resources.mesh_tree_number_to_term_map[current_tree_number])
    
    return hierarhchy


if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    standardization_resources = StandardizationResources(mesh_lookup)

    experiment_type_hierarchy = get_hierarchy("Non-coding RNA profiling by high throughput sequencing", standardization_resources)
    disease_hierarchy = get_hierarchy("lung cancer", standardization_resources) 

    print(experiment_type_hierarchy)
    print(disease_hierarchy)


