import numpy as np
import pytest
from core.bayesian import BayesianBeliefUpdater


def test_initial_probability_equals_prior():
    updater = BayesianBeliefUpdater(prior=0.5)
    assert abs(updater.get_probability() - 0.5) < 1e-12


def test_update_with_strong_evidence_increases_belief():
    updater = BayesianBeliefUpdater(prior=0.5)
    # Likelihood > 0.5 -> posterior > prior
    updater.update(likelihood=0.9)
    assert updater.get_probability() > 0.5


def test_update_with_weak_evidence_decreases_belief():
    updater = BayesianBeliefUpdater(prior=0.5)
    updater.update(likelihood=0.1)
    assert updater.get_probability() < 0.5


def test_sequential_updates_are_cumulative():
    updater = BayesianBeliefUpdater(prior=0.5)
    updater.update(likelihood=0.8)
    p_after_one = updater.get_probability()
    updater.update(likelihood=0.8)
    p_after_two = updater.get_probability()
    assert p_after_two > p_after_one


def test_probability_stays_in_0_1():
    updater = BayesianBeliefUpdater(prior=0.5)
    for _ in range(100):
        updater.update(likelihood=0.99)
    p = updater.get_probability()
    assert 0.0 < p <= 1.0


def test_reset_restores_new_prior():
    updater = BayesianBeliefUpdater(prior=0.5)
    updater.update(likelihood=0.9)
    updater.reset(new_prior=0.3)
    assert abs(updater.get_probability() - 0.3) < 1e-12


def test_numerically_stable_with_tiny_likelihoods():
    """Should not underflow with many small likelihoods."""
    updater = BayesianBeliefUpdater(prior=0.5)
    for _ in range(1000):
        updater.update(likelihood=0.001)
    p = updater.get_probability()
    assert 0.0 <= p <= 1.0
    assert not np.isnan(p)


def test_numerically_stable_with_large_likelihoods():
    """Should not overflow with many large likelihoods."""
    updater = BayesianBeliefUpdater(prior=0.5)
    for _ in range(1000):
        updater.update(likelihood=0.999)
    p = updater.get_probability()
    assert 0.0 <= p <= 1.0
    assert not np.isnan(p)


def test_bayes_theorem_single_update():
    """
    Manual verification: P(H|D) = P(D|H)*P(H) / [P(D|H)*P(H) + P(D|~H)*P(~H)]
    prior=0.4, P(D|H)=0.7, P(D|~H)=0.3 (complement likelihood)
    posterior = (0.7*0.4) / (0.7*0.4 + 0.3*0.6) = 0.28 / 0.46 ~ 0.6087
    """
    prior = 0.4
    likelihood_h = 0.7
    likelihood_not_h = 0.3
    expected = (likelihood_h * prior) / (likelihood_h * prior + likelihood_not_h * (1 - prior))

    updater = BayesianBeliefUpdater(prior=prior)
    # Our updater takes P(D|H); complement is computed internally
    updater.update(likelihood=likelihood_h)
    assert abs(updater.get_probability() - expected) < 1e-9
