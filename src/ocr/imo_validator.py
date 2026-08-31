import re

class IMOValidator:
    @staticmethod
    def compute_check_digit(six_digits):
        digits_str = str(six_digits).strip()
        if len(digits_str) != 6 or not digits_str.isdigit():
            return None
        weights = [7, 6, 5, 4, 3, 2]
        total_sum = sum(int(digits_str[i]) * weights[i] for i in range(6))
        return total_sum % 10

    @classmethod
    def validate_7digit_imo(cls, digits_str):
        clean_digits = re.sub(r'\D', '', str(digits_str))
        if len(clean_digits) != 7:
            return False, clean_digits, 'INVALID_LENGTH'

        six_prefix = clean_digits[:6]
        expected_check = cls.compute_check_digit(six_prefix)
        actual_check = int(clean_digits[6])

        if expected_check == actual_check:
            return True, f'IMO {clean_digits}', 'VALID'
        else:
            return False, clean_digits, f'CHECK_DIGIT_MISMATCH_EXPECTED_{expected_check}_GOT_{actual_check}'

    @classmethod
    def extract_and_validate_from_text(cls, raw_text):
        if not raw_text:
            return []

        text_upper = str(raw_text).upper()
        found_valid = []

        patterns = [
            r'IMO\s*[:#-]?\s*(\d{7})',
            r'\b(\d{7})\b'
        ]

        seen_digits = set()
        for pat in patterns:
            matches = re.finditer(pat, text_upper)
            for m in matches:
                cand_digits = m.group(1)
                if cand_digits not in seen_digits:
                    seen_digits.add(cand_digits)
                    is_valid, formatted_imo, _ = cls.validate_7digit_imo(cand_digits)
                    if is_valid:
                        found_valid.append(formatted_imo)

        return found_valid
