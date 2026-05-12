class TokenBudget:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens

    def fits(self, used: int, additional: int) -> bool:
        return used + additional <= self.max_tokens

    def remaining(self, used: int) -> int:
        return max(0, self.max_tokens - used)
