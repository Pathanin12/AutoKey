import unittest

from services.windows_input_service import text_is_ascii_keys


class WindowsInputTests(unittest.TestCase):
    def test_account_codes_and_dates_are_ascii(self) -> None:
        self.assertTrue(text_is_ascii_keys("5330-05"))
        self.assertTrue(text_is_ascii_keys("01/08/69"))
        self.assertTrue(text_is_ascii_keys("3,200.00"))

    def test_thai_is_not_ascii(self) -> None:
        self.assertFalse(text_is_ascii_keys("ค่าบริการ"))


if __name__ == "__main__":
    unittest.main()
