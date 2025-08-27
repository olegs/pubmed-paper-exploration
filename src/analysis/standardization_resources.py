from src.standardization.mesh_vocabulary import is_term_in_one_of_categories


class StandardizationResources:
    def __init__(self, mesh_lookup, category_filter=None):
        if category_filter is not None:
            self.mesh_lookup = {key: entry for key, entry in mesh_lookup.items(
            ) if is_term_in_one_of_categories(key, mesh_lookup, category_filter)}
        else:
            self.mesh_lookup = mesh_lookup
        self.case_insensitive_mesh_lookup = {key.strip().lower(): entry
                                             for key, entry in self.mesh_lookup.items()}
        self.mesh_id_to_term_map = {}
        for key, entry in self.mesh_lookup.items():
            if entry.id not in self.mesh_id_to_term_map or len(key) < len(self.mesh_id_to_term_map[entry.id]):
                self.mesh_id_to_term_map[entry.id] = key.strip().lower()

        self.mesh_term_to_id_map = {
            key.strip().lower(): entry.id for key, entry in self.mesh_lookup.items()}

        self.mesh_tree_number_to_term_map = {}
        for term, entry in self.mesh_lookup.items():
            for tree_number in entry.tree_numbers:
                if tree_number not in self.mesh_tree_number_to_term_map or len(term) < len(self.mesh_tree_number_to_term_map[tree_number]):
                    self.mesh_tree_number_to_term_map[tree_number] = term
