import dataclasses

import numpy as np

_TRANSITION_SUM_TOLERANCE = 1e-5


@dataclasses.dataclass(frozen=True)
class MarkovRewardProcess:
  # |S| x |S| array of state to state transition probabilities.
  transitions: np.ndarray
  # |S| vector of rewards for entering each state.
  rewards: np.ndarray
  name: str

  def __post_init__(self):
    """Raises error if transition or reward matrices malformed."""
    # Check basic shapes.
    if self.transitions.ndim != 2:
      raise ValueError(
          f'mrp transitions should be 2 dimensional, not: {self.transitions.shape}')
    if self.transitions.shape[0] != self.transitions.shape[1]:
      raise ValueError(
          f'mrp transitions should be SxS, not: {self.transitions.shape}')
    if self.rewards.ndim != 1:
      raise ValueError(
          f'mrp rewards should be 1 dimensional, not: {self.rewards.shape}')
    if self.transitions.shape[0] != self.rewards.shape[0]:
      raise ValueError(
          f'mrp transition and reward states do not match: {self.transitions.shape} vs. {self.rewards.shape}')
    if self.transitions.dtype != self.rewards.dtype:
      raise ValueError(
          f'mrp transition and reward dtypes do not match: {self.transitions.dtype.__name__} vs {self.rewards.dtype.__name__}')

    # Ensure transition probabilities sum to 1 for all states.
    state_probability_sums = self.transitions.sum(axis=-1)
    failed_unity = np.where(state_probability_sums != 1., True, False)
    num_invalid_states = np.sum(failed_unity)
    if num_invalid_states:
      bad_states = np.argwhere(failed_unity)
      raise ValueError(
          f'Invalid Reward Process, some states do not have transitions that sum to 1: {bad_states}')

  @property
  def num_states(self):
    return len(self.transitions)


@dataclasses.dataclass(frozen=True)
class MarkovDecisionProcess:
  # |A| x |S| x |S| array of (state, action) -> state transition probabilities.
  transitions: np.ndarray
  # |A| x |S| vector of rewards for each action.
  rewards: np.ndarray
  name: str

  def __post_init__(self):
    """Raises error if transition or reward matrices malformed."""
    # Check basic shapes.
    if self.transitions.ndim != 3:
      raise ValueError(
          f'mdp transitions should be 3 dimensional, not: {self.transitions.shape}')
    if self.transitions.shape[1] != self.transitions.shape[2]:
      raise ValueError(
          f'mdp transitions should be AxSxS, not: {self.transitions.shape}')
    if self.rewards.ndim != 2:
      raise ValueError(
          f'mdp rewards should be 2 dimensional, not: {self.rewards.shape}')
    if self.transitions.shape[0] != self.rewards.shape[0]:
      raise ValueError(
          f'mdp transition and reward actions do not match: {self.transitions.shape} vs. {self.rewards.shape}')
    if self.transitions.shape[1] != self.rewards.shape[1]:
      raise ValueError(
          f'mdp transition and reward states do not match: {self.transitions.shape} vs. {self.rewards.shape}')
    if self.transitions.dtype != self.rewards.dtype:
      raise ValueError(
          f'mdp transition and reward dtypes do not match: {self.transitions.dtype.__name__} vs {self.rewards.dtype.__name__}')

    # Ensure transition probabilities sum to 1 for all actions and states.
    for action_idx, transitions in enumerate(self.transitions):
      state_probability_sums = transitions.sum(axis=-1)
      state_probability_errors = np.abs(1 - state_probability_sums)
      failed_unity = np.where(
          state_probability_errors > _TRANSITION_SUM_TOLERANCE,
          True,
          False)
      num_invalid_states = np.sum(failed_unity)
      if num_invalid_states:
        bad_states = np.argwhere(failed_unity)
        raise ValueError(
            f'Invalid Decision Process, action:{action_idx}, some states do not have transitions that sum to 1: {bad_states}')

  @property
  def num_states(self):
    return self.transitions.shape[1]

  @property
  def num_actions(self):
    return len(self.transitions)
