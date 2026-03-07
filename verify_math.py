"""
Cross-check LMSR and Bayesian math against known values.
Run: python verify_math.py
"""
import numpy as np
from core.lmsr import cost_function, price_function, max_loss
from core.bayesian import BayesianBeliefUpdater
from core.kelly import expected_value, position_size_usd

PASS = "PASS"
FAIL = "FAIL"


def check(name, computed, expected, tol=1e-6):
    ok = abs(computed - expected) < tol
    status = PASS if ok else FAIL
    print(f"[{status}] {name}: computed={computed:.6f}, expected={expected:.6f}")
    return ok


all_pass = True

# LMSR: C([0,0], b=100) = 100*ln(2) ~ 69.314718
all_pass &= check("C([0,0], b=100)", cost_function(np.array([0.0, 0.0]), 100.0), 100 * np.log(2))

# LMSR: price([0,0]) = [0.5, 0.5]
prices = price_function(np.array([0.0, 0.0]), 100.0)
all_pass &= check("p_0([0,0])", prices[0], 0.5)
all_pass &= check("p_1([0,0])", prices[1], 0.5)

# Max loss: b=100_000, n=2 -> 69315.08
all_pass &= check("L_max(b=100k, n=2)", max_loss(100_000, 2), 100_000 * np.log(2))

# Kelly EV: p_hat=0.6, p=0.5 -> 0.1
all_pass &= check("EV(0.6, 0.5)", expected_value(0.6, 0.5), 0.1)

# Bayesian: uniform prior, one update with likelihood=0.8
updater = BayesianBeliefUpdater(prior=0.5)
updater.update(0.8)
# P(H|D) = 0.8*0.5 / (0.8*0.5 + 0.2*0.5) = 0.4/0.5 = 0.8
all_pass &= check("Bayes(prior=0.5, L=0.8)", updater.get_probability(), 0.8)

print()
if all_pass:
    print("All math verified!")
else:
    print("Some checks failed!")
