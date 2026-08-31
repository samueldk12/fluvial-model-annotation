import re
from collections import defaultdict
from src.ocr.imo_validator import IMOValidator

class MultiFrameIMOConsensus:
    def __init__(self, min_confirm_confidence=1.50):
        self.min_confirm_confidence = float(min_confirm_confidence)
        self.voting_table = [defaultdict(float) for _ in range(7)]
        self.observations_count = 0
        self.confirmed_imo = None
        self.confirmed_confidence = 0.0

    def add_observation(self, raw_text, confidence=1.0):
        if self.confirmed_imo is not None:
            return self.confirmed_imo, self.confirmed_confidence, True

        clean_digits = re.sub(r'\D', '', str(raw_text))
        if len(clean_digits) != 7:
            return None, 0.0, False

        self.observations_count += 1
        conf = max(0.10, float(confidence))

        for pos in range(7):
            ch = clean_digits[pos]
            self.voting_table[pos][ch] += conf

        candidate_digits = []
        pos_confs = []
        for pos in range(7):
            if not self.voting_table[pos]:
                return None, 0.0, False
            best_char = max(self.voting_table[pos].keys(), key=lambda c: self.voting_table[pos][c])
            candidate_digits.append(best_char)
            pos_confs.append(self.voting_table[pos][best_char])

        cand_str = ''.join(candidate_digits)
        is_valid, formatted_imo, _ = IMOValidator.validate_7digit_imo(cand_str)

        mean_conf = float(sum(pos_confs) / 7.0)
        if is_valid and mean_conf >= self.min_confirm_confidence:
            self.confirmed_imo = formatted_imo
            self.confirmed_confidence = mean_conf
            return self.confirmed_imo, self.confirmed_confidence, True

        return (formatted_imo if is_valid else None), mean_conf, False

    def reset(self):
        self.voting_table = [defaultdict(float) for _ in range(7)]
        self.observations_count = 0
        self.confirmed_imo = None
        self.confirmed_confidence = 0.0
