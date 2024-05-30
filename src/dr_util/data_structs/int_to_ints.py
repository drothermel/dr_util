from collections import defaultdict

from dr_util.datastructs.data_struct import DataStruct

class Int2IntsDict(DataStruct):
    def __init__(
        self,
        data_dir,
        name,
        building=False,
    ):
        self.int2ints_dict = defaultdict(set)
        super().__init__(
            data_dir,
            name,
            always_save_attrs=[
                'int2ints_dict',
            ],
            building=building,
        )

    def __contains__(self, key):
        return key in self.int2ints_dict

    def __iter__(self):
        return iter(self.int2ints_dict)

    def __len__(self):
        return len(self.int2ints_dict)

    def add_key_val(self, key, val, allow_repeats=False):
        assert self.building
        assert key not in self.int2ints_dict or allow_repeats
        self.int2ints_dict[int(key)].add(val)

    # Save dict not defaultdict
    def save(self):
        self.int2ints_dict = dict(self.int2ints_dict)
        super().save()

