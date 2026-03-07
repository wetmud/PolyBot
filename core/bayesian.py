"""
Real-Time Bayesian Signal Processing.
Always operates in log-space for numerical stability.
Update cycle target: < 828ms total.
"""
import numpy as np


class BayesianBeliefUpdater:
    """
    Sequential Bayesian updater operating in log-space.
    Maintains log P(H | D1, ..., Dt) via incremental updates.

    The complement hypothesis ~H has likelihood (1 - likelihood).
    We track log-odds: log[P(H|D) / P(~H|D)] for stability.
    """

    def __init__(self, prior: float):
        if not (0.0 < prior < 1.0):
            raise ValueError(f"Prior must be in (0, 1), got {prior}")
        # Work in log-odds space: log[p / (1-p)]
        self._log_odds = np.log(prior) - np.log(1.0 - prior)

    def update(self, likelihood: float) -> float:
        """
        Sequential update in log-space (eq. 3):
        log_odds += log(P(D|H)) - log(P(D|~H))
        Returns updated probability.
        """
        if not (0.0 < likelihood < 1.0):
            raise ValueError(f"Likelihood must be in (0, 1), got {likelihood}")
        complement = 1.0 - likelihood
        self._log_odds += np.log(likelihood) - np.log(complement)
        return self.get_probability()

    def get_probability(self) -> float:
        """Convert log-odds back to probability: sigmoid(log_odds)."""
        return float(1.0 / (1.0 + np.exp(-self._log_odds)))

    def reset(self, new_prior: float):
        """Reset beliefs to a new prior (e.g., when market resolves)."""
        if not (0.0 < new_prior < 1.0):
            raise ValueError(f"Prior must be in (0, 1), got {new_prior}")
        self._log_odds = np.log(new_prior) - np.log(1.0 - new_prior)
