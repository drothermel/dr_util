from dataclasses import MISSING, fields


def lenient_validate(cls):
    """
    A decorator that wraps a dataclass __init__ so that extra keyword arguments
    are silently ignored.
    """
    original_init = cls.__init__

    # Collect the field names defined in the dataclass.
    valid_field_names = {f.name for f in fields(cls)}

    def __init__(self, *args, **kwargs):  # noqa: N807
        self.missing_or_invalid_keys = set()

        # Drop extra keys and add missing keys
        updated_kwargs = {}
        for k in valid_field_names:
            if k not in kwargs:
                self.missing_or_invalid_keys.add(k)
            updated_kwargs[k] = kwargs.get(k)

        # Execute original init function
        original_init(self, *args, **updated_kwargs)

        # Nested initialization & finding of missing keys
        for name in valid_field_names:
            # Default can be three things:
            #   1. Missing
            #   2. A nested config schema name to be initialized with data
            #   3. An immutable value
            default = self.__dataclass_fields__[name].default
            curr_val = getattr(self, name)

            # 1. Missing
            #   If default was missing curr_val must be set before now
            if default is MISSING:
                # curr_val should be set to None at the latest in
                # update_kwargs so this is a bug if not
                assert curr_val is not MISSING, "There's a bug"

            # 2. Nested Config Schema
            #   If the default was a dataclass schema, the current
            #   value should be passed in to initialize the schema
            if isinstance(default, type):
                assert isinstance(curr_val, dict | None)
                if curr_val is None:
                    nested_dataclass = default(class_name=name)
                else:
                    nested_dataclass = default(**curr_val, class_name=name)
                setattr(self, name, nested_dataclass)
                self.missing_or_invalid_keys.update(
                    [f"{name}.{k}" for k in nested_dataclass.missing_or_invalid_keys]
                )

            # 3. Immutable value
            #   If a non-missing, non-nested config was assigned to default
            #   it should be immutable and shouldn't have changed during init
            if default is not MISSING and not isinstance(default, type):  # noqa
                if curr_val != default:
                    self.missing_or_invalid_keys.add(name)

    cls.__init__ = __init__
    return cls
