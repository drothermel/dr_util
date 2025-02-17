from dataclasses import dataclass, fields, asdict, MISSING

## Useful for debugging....
def print_dict(dt, indent=2):
    for k, v in dt.items():
        ind_str = " " * indent + "- "
        if isinstance(v, dict):
            print(f"{ind_str}{k}:")
            print_dict(v, indent + 2)
        else:
            print(f"{ind_str}{k}:", v)

## Useful for debugging....
def print_dataclass(dc):
    print("=========== Data Class ============")
    print_dict(asdict(dc))
    print("===================================")


def lenient_validate(cls):
    """
    A decorator that wraps a dataclass __init__ so that extra keyword arguments
    are silently ignored.
    """
    original_init = cls.__init__

    # Collect the field names defined in the dataclass.
    valid_field_names = {f.name for f in fields(cls)}
    print(">> Wrapping Data Class")
    print("     Expected field names:", valid_field_names)
    
    def __init__(self, *args, **kwargs):
        self.missing_keys = set()

        # Filter kwargs: keep only those that are valid field names.
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_field_names}
        # Note the keys that are missing and add them
        missing_keys = [n for n in valid_field_names if n not in filtered_kwargs]
        self.missing_keys.update(missing_keys)
        filtered_kwargs.update({k: None for k in missing_keys})

        # Execute original init function
        original_init(self, *args, **filtered_kwargs)

        # Initialize any sub-dataclasses with passed in value
        for k in valid_field_names:
            if is_key_default_a_schema(k, self):
                initialize_key_schema_with_input_val(k, self)

        # Identify any missing required keys after 
        for name in valid_field_names:
            default = self.__dataclass_fields__[name].default
            curr_val = getattr(self, name)

            # Verify the fields against the defaults
            field_missing = get_field_missing_keys(name, default, curr_val)

            # Add any missing keys to the list
            self.missing_keys.update(field_missing)


    cls.__init__ = __init__
    return cls

def is_key_default_a_schema(key, cls):
    default = cls.__dataclass_fields__[key].default
    return isinstance(default, type)

def initialize_key_schema_with_input_val(key, cls):
    default = cls.__dataclass_fields__[key].default
    curr_val = getattr(cls, key)
    setattr(cls, key, default(**curr_val, class_name=key))

def get_field_missing_keys(name, default, curr_val):
    # All missing values should be filled in
    if default is MISSING:
        if curr_val is MISSING:
            print(f">> {name} | never initialized, still missing")
            return [name]
        return []

    # Add the missing keys from children into own missing keys
    if isinstance(default, type):
        child_missing = [
            f'{name}.{k}' for k in curr_val.missing_keys
        ]
        if len(child_missing) > 0:
            print(f">> {name} | child missing: {child_missing}")
            return child_missing
        return[]

    # If the default value is defined, the config val should match
    if default != curr_val:
        print(">> {name} | default doesn't equal current val")
        return [name]
    return []
