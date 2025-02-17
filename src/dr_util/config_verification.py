from omegaconf import OmegaConf
from dr_util.schema_utils import print_dict, print_dataclass

    
def validate_config(cfg, config_type, schema_fxn):
    # Select the schema to validate with
    schema_cls = schema_fxn(config_type)
    if schema_cls is None:
        print(f">> Invalid config schema type: {config_type}")
        return False

    # Get the missing keys
    bad_keys = get_bad_keys_by_schema(cfg, schema_cls)
    if len(bad_keys) > 0:
        print(f">> Invalid config, missing or invalid keys: {bad_keys}")
        return False
    return True
            

def get_bad_keys_by_schema(cfg, schema_cls):
    input_dict = OmegaConf.to_container(cfg, resolve=True)
    print_dict(input_dict)
    print()
    
    print(">> Convert dict into dataclass")
    input_data_class = schema_cls(**input_dict, class_name="Top Level Config")
    return input_data_class.missing_or_invalid_keys

