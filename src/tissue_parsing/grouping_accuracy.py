from sklearn.metrics import accuracy_score
def most_common(lst):
    return max(set(lst), key=lst.count)

def grouping_accuracy(true_group_indexes, labels):
    labels_in_group = {}
    for group_index, label in zip(true_group_indexes, labels):
        labels_in_group[group_index] = labels_in_group.get(group_index, []) + [label]
    
    group_index_for_label = {}
    for group_index in sorted(set(true_group_indexes)):
        most_common_label = most_common(labels_in_group[group_index])
        if most_common_label not in group_index_for_label:
            group_index_for_label[most_common_label] = group_index

    predicted_group_indexes = [group_index_for_label[label] if label in group_index_for_label else -1 for label in labels]
    return accuracy_score(true_group_indexes, predicted_group_indexes)


if __name__ == "__main__":
    print(
        grouping_accuracy([1, 2, 3], ["one", "two", "three"])
    )
    print(
        grouping_accuracy([1, 2, 3, 1, 2, 3], ["one", "two", "three", "one", "two", "three"])
    )
    print(
        grouping_accuracy([1, 2, 3, 1, 2, 3], ["whatever"] * 6)
    )
    print(
        grouping_accuracy([1, 2, 3, 1, 2, 3], ["whatever"] * 5 + ["three"])
    )


