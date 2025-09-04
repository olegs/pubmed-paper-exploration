class ContainsNameAtLevelFilter:
    def __init__(self, name, level, entity_column):
        self.name = name
        self.level = level
        self.entity_column = entity_column

    def __call__(self, df):
        hierarchy_passes_filter = lambda hierarchy: (len(hierarchy) >= self.level) and (
                hierarchy[self.level - 1] == self.name)
        condition = lambda hierarchies: any(hierarchy_passes_filter(hierarchy) for hierarchy in hierarchies)
        df = df.loc[df[self.entity_column].apply(condition)]
        df.loc[:, self.entity_column] = df.loc[:, self.entity_column].apply(
            lambda x: list(filter(hierarchy_passes_filter, x)))
        return df
