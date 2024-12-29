import math

class StreamingStatistics:
    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0  # Sum of squared differences from the mean
        self.last_value = 0.0

    def add(self, value: float):
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2
        self.last_value = value

    def get_last_added(self) -> float:
        return self.last_value

    def get_mean(self) -> float:
        return self.mean

    def get_variance(self) -> float:
        if self.count < 2:
            return float('nan')
        return self.m2 / self.count

    def get_sample_variance(self) -> float:
        if self.count < 2:
            return float('nan')
        return self.m2 / (self.count - 1)

    def get_standard_deviation(self) -> float:
        return math.sqrt(self.get_variance())

    def get_sample_standard_deviation(self) -> float:
        return math.sqrt(self.get_sample_variance())