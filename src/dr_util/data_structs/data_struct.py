import os
import numpy as np

import dr_utils.file_utils as fu

# TODO: Test everything, update to use pathlib

def is_int_or_castable(value):
    if isinstance(value, int):
        return True
    elif isinstance(value, float):
        return value.is_integer()
    elif isinstance(value, str):
        if value.strip().isdigit() or (value[0] == '-' and value[1:].isdigit()):
            return True
    return False


def is_simple(obj):
    if isinstance(obj, (str, int, float)):
        return True
    return False


def is_collection(obj):
    if isinstance(obj, (list, tuple, set, dict)):
        return True
    if is_simple(obj):
        return False
    return True

class DataStruct:
    def __init__(
        self,
        data_dir,
        name,
        always_save_attrs={},
        building=False,
    ):
        self.name = name
        self.data_dir = data_dir
        self.always_save_attrs = always_save_attrs
        self.building = building
        self.create_args = {
            'data_dir': data_dir,
            'name': name,
            'always_save_attrs': always_save_attrs,
        }
        self._metadata_path = self.get_path('metadata.pkl')
        self.load()

    def __len__(self):
        return 0

    def __str__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(name={self.name}, len={len(self)})"

    def get_dir(self):
        return f"{self.data_dir}{self.name}/"

    def get_path(self, data_name, ending):
        save_dir = self.get_dir()
        return f"{save_dir}{data_name}.{ending}"

    def _get_simple_attrs(self):
        simple_attrs = {}
        for attr_name in self.always_save_attrs:
            attr_val = getattr(self, attr_name, None)
            if attr_val is not None and is_simple(attr_val):
                simple_attrs[attr_name] = attr_val
        return simple_attrs

    def _save_data(self, name, data):
        if issubclass(data, DataStruct):
            data.save()
            return {'create_args': data.create_args}

        ending = 'npy' if isinstance(data, np.ndarray) else 'pkl'
        path = self.get_path(name, ending)
        fu.dump_file(data, path)
        return {'path': path}

    def _load_data(self, name, load_info):
        attr_path = load_info.get('attr_path', None)
        create_args = load_info.get('create_args', None)
        assert attr_path is not None or create_args is not None
        if attr_path is not None:
            setattr(self, name, fu.load_file(attr_path))
        else:
            assert False, "loading sub DataStruct isn't impld"

    # All datastructs will save a save_dir/metadata.json
    # that will contain:
    # {
    #   'simple_attrs':...,
    #   'load_info': {
    #       attr_name: {
    #           'attr_path': path,
    #           - or -
    #           'create_args': None,
    #       },
    #   },
    # }
    def _save_attrs(self):
        metadata = {}

        # Group simple_attrs as a single dict
        simple_attrs = self._get_simple_attrs()
        metadata['simple_attrs'] = simple_attrs

        # Save everything else individually
        for attr_name in self.always_save_attrs:
            if attr_name in simple_attrs:
                continue
            attr_val = getattr(self, attr_name, None)
            metadata['load_info'][attr_name].append(
                self._save_data(attr_name, attr_val)
            )

        # And finally save the metadata with the simple attrs
        fu.dump_file(metadata, self._metadata_path)

    def load(self):
        if self.building:
            return
        assert os.path.exists(self.get_dir())

        # First load the metadata
        metadata = fu.load_file(self._metadata_path)

        # Then load simple attrs
        for sa_name, sa_val in metadata['simple_attrs'].items():
            setattr(self, sa_name, sa_val)

        # Then load the rest
        for attr_name, load_info in metadata['load_info'].items():
            self._load_data(attr_name, load_info)

    def save(self):
        assert self.building
        os.makedirs(self.get_dir(), exist_ok=True)
        self._save_attrs()

    def save_extra_data(self, name):
        data = getattr(self, name)
        new_metadata = self._save_data(name, data)
        metadata = fu.load_file(self._metadata_path)
        metadata['extra_load_info'][name] = new_metadata
        fu.dump_file(metadata, self._metadata_path)

    def load_extra_data(self, name):
        extra_load_info = fu.load_file(self._metadata_path)['extra_load_info']
        self._load_data(name, extra_load_info[name])
