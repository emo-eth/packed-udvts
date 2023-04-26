def to_camel_case(snake_str):
    components = snake_str.split("_")
    # capitalize the first component and join the rest capitalized
    return components[0] + "".join(x.title() for x in components[1:])


def to_title_case(snake_str):
    components = snake_str.split("_")
    # capitalize the first component and join the rest capitalized
    return "".join(x.title() for x in components)
