"""GARET is Generic Average Reward Environment Testbed.

It is a special case of Bhatnagar et al.'s GARNET:
https://era.library.ualberta.ca/items/8fc4a1f6-95c9-4da8-aecd-96867babdf4c

The current implementation does not support online, sample-based operation.

Instead, it is appropriate for value/policy iteration algorithm research.
"""
import functools
import jax
import jax.numpy as jnp
import numpy as np
from differential_value_iteration.environments import structure


def create(seed: int, num_states: int, num_actions: int,
    branching_factor: int, dtype: np.dtype) -> structure.MarkovDecisionProcess:
  """Creates transition and reward matrices for GARET instance."""
  rng_key = jax.random.PRNGKey(seed=seed)
  garet_final_shape = (num_states, num_actions, num_states)
  # Keys for branching_factor next state transitions for all (s, a) pairs.
  new_keys = jax.random.split(rng_key, num_states * num_actions + 1)
  new_state_keys = new_keys[1:]
  rng_key = new_keys[0]

  # For each (s,a) pair, determine next states using jax.random.choice.
  # Use jax.vmap to calculate this in parallel for all (s,a) pairs.
  next_state_fn = jax.vmap(jax.random.choice, in_axes=(0, None, None, None))

  # Array of the indices of resulting states.
  next_states_flat = next_state_fn(new_state_keys, num_states,
                                   (branching_factor,), False)

  # Generate transition probabilities for all branches.
  rng_key, next_state_probs_key = jax.random.split(rng_key)
  # Initial probabilities shape (|S| x |A|, b). Probabilities NOT normalized.
  next_state_probs_flat_unnormalized = jax.random.uniform(
      key=next_state_probs_key,
      shape=(num_states * num_actions, branching_factor))

  # Calculate sums per (s, a) and reshape conveniently for normalizing.
  next_state_prob_sums = jnp.sum(next_state_probs_flat_unnormalized, axis=-1)
  next_state_prob_sums = jnp.repeat(next_state_prob_sums, branching_factor)
  next_state_prob_sums = next_state_prob_sums.reshape((-1, branching_factor))

  # Normalize transition probabilities.
  next_state_probs_flat = next_state_probs_flat_unnormalized / next_state_prob_sums

  # Generate expected rewards for all branches.
  rng_key, transition_reward_key = jax.random.split(rng_key)
  transition_expected_rewards_flat = jax.random.normal(
      key=transition_reward_key,
      shape=(num_states * num_actions, branching_factor))

  # Create the transition and reward matrices.
  transition_matrix_flat = jnp.zeros(
      shape=(num_states * num_actions, num_states),
      dtype=jnp.float32)
  reward_matrix_flat = jnp.zeros(
      shape=(num_states * num_actions, num_states),
      dtype=jnp.float32)

  first_dim_indices = jnp.arange(num_states * num_actions)
  first_dim_indices = first_dim_indices.repeat(branching_factor)
  transition_matrix_flat = transition_matrix_flat.at[
    first_dim_indices, next_states_flat.ravel()].set(
      next_state_probs_flat.ravel())

  reward_matrix_flat = reward_matrix_flat.at[
    first_dim_indices, next_states_flat.ravel()].set(
      transition_expected_rewards_flat.ravel())

  transition_matrix = transition_matrix_flat.reshape(garet_final_shape)
  reward_matrix = reward_matrix_flat.reshape(garet_final_shape)

  # Marginalize rewards matrix for structure.MarkovDecisionProcess.
  reward_matrix_marginalized = jax.vmap(jax.vmap(jnp.dot))(transition_matrix,
                                                           reward_matrix)

  # Restructure for structure.MarkovDecisionProcess (A, S, S') vs (S, A, S').
  transition_matrix = jnp.swapaxes(transition_matrix, 0, 1)
  # Restructure for structure.MarkovDecisionProcess (A, S) vs (S, A).
  reward_matrix_marginalized = jnp.swapaxes(reward_matrix_marginalized, 0, 1)
  return structure.MarkovDecisionProcess(
      transitions=np.array(transition_matrix, dtype=dtype),
      rewards=np.array(reward_matrix_marginalized, dtype=dtype),
      name=f'GARET S:{num_states} A:{num_actions} B:{branching_factor} K:{rng_key} D:{dtype.__name__}')

GARET1 = functools.partial(create,
                           seed=42,
                           num_states=4,
                           num_actions=4,
                           branching_factor=3)
GARET2 = functools.partial(create,
                           seed=42,
                           num_states=4,
                           num_actions=20,
                           branching_factor=3)
GARET3 = functools.partial(create,
                           seed=42,
                           num_states=10,
                           num_actions=2,
                           branching_factor=3)
GARET_100 = functools.partial(create,
                           seed=42,
                           num_states=100,
                           num_actions=2,
                           branching_factor=3)