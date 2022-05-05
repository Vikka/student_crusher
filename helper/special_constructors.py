from helper.inserts import list_ as custom_list


def list_(it):
    tmp = list(it) + [...]
    return custom_list(tmp)