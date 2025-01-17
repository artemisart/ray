import unittest
import torch
import numpy as np
import tensorflow as tf

from ray.rllib.utils.test_utils import check
from ray.rllib.models.specs.specs_torch import TorchSpecs
from ray.rllib.models.specs.specs_np import NPSpecs
from ray.rllib.models.specs.specs_tf import TFSpecs

# TODO: add jax tests

SPEC_CLASSES = {"torch": TorchSpecs, "np": NPSpecs, "tf": TFSpecs}
DOUBLE_TYPE = {
    "torch": torch.float64,
    "np": np.float64,
    "tf": tf.float64,
}
FLOAT_TYPE = {
    "torch": torch.float32,
    "np": np.float32,
    "tf": tf.float32,
}


class TestSpecs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def test_fill(self):

        for fw in SPEC_CLASSES.keys():
            spec_class = SPEC_CLASSES[fw]
            double_type = DOUBLE_TYPE[fw]

            # if un-specified dims should be 1, dtype is not important
            x = spec_class("b,h").fill(float(2.0))

            # check the shape
            self.assertEqual(x.shape, (1, 1))
            # check the value
            check(x, np.array([[2.0]]))

            x = spec_class("b,h", b=2, h=3).fill(2.0)
            self.assertEqual(x.shape, (2, 3))

            x = spec_class("b,h1,h2,h3", h1=2, h2=3, h3=3, dtype=double_type).fill(2)
            self.assertEqual(x.shape, (1, 2, 3, 3))
            self.assertEqual(x.dtype, double_type)

    def test_validation(self):

        b, h = 2, 3

        for fw in SPEC_CLASSES.keys():
            spec_class = SPEC_CLASSES[fw]
            double_type = DOUBLE_TYPE[fw]
            float_type = FLOAT_TYPE[fw]

            tensor_2d = spec_class("b,h", b=b, h=h, dtype=double_type).fill()

            matching_specs = [
                spec_class("b,h"),
                spec_class("b,h", h=h),
                spec_class("b,h", h=h, b=b),
                spec_class("b,h", b=b, dtype=double_type),
            ]

            # check if get_shape returns a tuple of ints
            shape = matching_specs[0].get_shape(tensor_2d)
            self.assertIsInstance(shape, tuple)
            self.assertTrue(all(isinstance(x, int) for x in shape))

            # check matching
            for spec in matching_specs:
                spec.validate(tensor_2d)

            non_matching_specs = [
                spec_class("b"),
                spec_class("b,h1,h2"),
                spec_class("b,h", h=h + 1),
            ]
            if fw != "jax":
                non_matching_specs.append(spec_class("b,h", dtype=float_type))

            for spec in non_matching_specs:
                self.assertRaises(ValueError, lambda: spec.validate(tensor_2d))

            # non unique dimensions
            self.assertRaises(ValueError, lambda: spec_class("b,b"))
            # unknown dimensions
            self.assertRaises(ValueError, lambda: spec_class("b,h", b=1, h=2, c=3))
            self.assertRaises(ValueError, lambda: spec_class("b1", b2=1))
            # zero dimensions
            self.assertRaises(ValueError, lambda: spec_class("b,h", b=1, h=0))
            # non-integer dimension
            self.assertRaises(ValueError, lambda: spec_class("b,h", b=1, h="h"))

    def test_equal(self):

        for fw in SPEC_CLASSES.keys():
            spec_class = SPEC_CLASSES[fw]
            spec_eq_1 = spec_class("b,h", b=2, h=3)
            spec_eq_2 = spec_class("b, h", b=2, h=3)
            spec_eq_3 = spec_class(" b,  h", b=2, h=3)
            spec_neq_1 = spec_class("b, h", h=3, b=3)
            spec_neq_2 = spec_class("b, h", h=3, b=3, dtype=DOUBLE_TYPE[fw])

            self.assertTrue(spec_eq_1 == spec_eq_2)
            self.assertTrue(spec_eq_2 == spec_eq_3)
            self.assertTrue(spec_eq_1 != spec_neq_1)
            self.assertTrue(spec_eq_1 != spec_neq_2)


if __name__ == "__main__":
    import pytest
    import sys

    sys.exit(pytest.main(["-v", __file__]))
