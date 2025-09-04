class AnyValueInCellFilter:
    def __init__(self, column, values):
        self.column = column
        self.values = values

    def __call__(self, df):
        if not self.values:
            return df
        df = df.copy()
        condition = lambda l: any(value in l for value in self.values)
        return df.loc[df[self.column].apply(condition), :]

    def __eq__(self, other):
        return (isinstance(other, AnyValueInCellFilter)) and (self.column == other.column) and (
                set(self.values) == set(other.values))

    def __hash__(self):
        hash(self.column + self.value)
