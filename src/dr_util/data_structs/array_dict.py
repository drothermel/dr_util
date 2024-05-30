from dr_util.datastructs.data_struct import DataStruct
from dr_util.datastructs.int_to_ints import Int2IntsDict

class ArrayDict(DataStruct):
    def __init__(
        self,
        data_dir,
        name,
        building=False,
        value_shape=None,
        dtype=None,
        drop_empty=False,
    ):
        self.id2data_arr = None
        self.data2id_int2ints = None
        self.null_value = None

        # Only used for building
        self._id2data_dict = {}
        self._value_shape = value_shape
        self._dtype = dtype
        self._drop_empty = drop_empty

        super().__init__(
            data_dir,
            name,
            always_save_attrs=[
                'id2data_arr',
                'null_value',
            ],
            building=building,
        )

    def __contains__(self, item):
        if self.building:
            return item in self._id2data_dict
        else:
            id2data_shape = self._id2data_arr.shape
            return item < id2data_shape[0]

    def get_id2data_elem(self, key):
        if self.building:
            return self._id2data_dict[key]
        else:
            return self.id2data_arr[key]

    def get_id2data_range(self, key_start, key_end):
        return self.id2data_arr[key_start:key_end]

    def get_id2data_batch(self, keys):
        all_out = [self.id2data_arr[k] for k in keys]
        return all_out

    def add_key_val(self, key, val, allow_repeats=False):
        assert self.building
        assert key not in self._id2data_dict or allow_repeats
        self._id2data_dict[key] = val

    # Only makes sense for data that is one column
    def build_data2id_from_id2data(self):
        # squeeze before converting to check ndim
        id2data = self.id2data_arr
        id2data = np.squeeze(id2data)
        assert id2data.ndim == 1
        self.data2id_int2ints = Int2IntsDict(
            data_dir=self.get_dir(),
            name='data2id_int2ints',
            building=True,
        )
        for i, data in enumerate(id2data):
            self.data2id_int2ints.add_key_val(
                key=data,
                val=i,
                allow_repeats=True,
            )
        self.data2id_int2ints = dict(self.data2id_int2ints)
        self.data2id_int2ints.building = False

    def _dict2array(self):
        assert self.building
        self.id2data_arr, self.null_value = fixed_len_int_dict_to_np_array(
            self._id2data_dict,
            self._value_shape,
            self._dtype,
            drop_empty=self._drop_empty,
        )
