from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

MAX_ITERATIONS_NUMBER = 1000


class GenericIQAE:
    """
    The implementation is based on Algorithm 1 & Algorithm 2 in [1], with the intent of demistifying variables names
    and simplifying the code flow.
    Moreover, we separated the algorithm flow from quantum execution to allow migrating this code to any execution
    interface and to improve its testability.

    References:
        [1]: Grinko, D., Gacon, J., Zoufal, C., & Woerner, S. (2019).
             Iterative Quantum Amplitude Estimation.
             `arXiv:1912.05559 <https://arxiv.org/abs/1912.05559>`.
    """

    def __init__(
        self,
        epsilon: float,
        alpha: float,
        num_shots: int,
        sample_callable: Callable[[int, int], int],
    ) -> None:
        """
        Parameters:
            epsilon: Target accuracy.
            alpha: Specifies the confidence level (1 - alpha).
            num_shots: The maximum number of shots in each iteration.
            sample_callable: A callable which gets k and num_shots, and returns the count of good states for $Q^kA$
                (states with 1 in the last qubit).
                This callable is responsible for the quantum execution and the results parsing.
        """
        self._epsilon = epsilon
        self._alpha = alpha
        self._num_shots = num_shots
        self._sample_callable = sample_callable

        self.iterations: list[IterationInfo] = []

        # Prepare initial values (lines 2-6, Algorithm 1, [1])
        self._new_iteration()
        self._current().k = 0
        self._current().is_upper_plane = True
        self._current().confidence_interval = np.array([0, np.pi / 2])

        self._max_rounds = np.ceil(np.log2(np.pi / (8 * self._epsilon)))

    def _new_iteration(self) -> None:
        if len(self.iterations) > MAX_ITERATIONS_NUMBER:
            raise RuntimeError(
                f"Maximum number of iterations ({MAX_ITERATIONS_NUMBER}) achieved."
            )
        self.iterations.append(IterationInfo())

    def _current(self) -> IterationInfo:
        return self.iterations[-1]

    def _prev(self) -> IterationInfo:
        return self.iterations[-2]

    def run(self) -> float:
        """
        Execute the estimation algorithm.
        See Algorithm 1, [1].
        """
        while interval_len(self._current().confidence_interval) > 2 * self._epsilon:
            self._new_iteration()
            self._find_next_K()
            self._sample()
            self._calculate_confidence_interval()

        return self.current_estimation()

    def current_estimation_confidence_interval(self) -> np.ndarray:
        return np.sin(self._current().confidence_interval) ** 2

    def current_estimation(self) -> float:
        return self.current_estimation_confidence_interval().mean()

    def _find_next_K(self, r: int = 2) -> None:  # noqa: N802
        self._current().K, self._current().is_upper_plane = self.find_next_K(
            K=self._prev().K,
            is_upper_plane=self._prev().is_upper_plane,
            confidence_interval=self._prev().confidence_interval,
            r=r,
        )

    @staticmethod
    def find_next_K(  # noqa: N802
        K: int,  # noqa: N803
        is_upper_plane: bool,
        confidence_interval: np.ndarray,
        r: int = 2,
    ) -> tuple[int, bool]:
        """
        We want to find the largest K (with some lower and upper bounds) such that the K-scaled confidence interval
        lies completely in the upper or lower half planes.
        See Algorithm 2, [1].
        """
        K_max = int(np.pi // interval_len(confidence_interval))  # noqa: N806
        K_max = K_max - (K_max - 2) % 4  # noqa: N806
        K_min = r * K  # noqa: N806

        for K_cand in range(K_max, K_min - 1, -4):  # noqa: N806
            scaled_confidence_interval = (K_cand * confidence_interval) % (2 * np.pi)

            if all(scaled_confidence_interval <= np.pi):
                return K_cand, True
            if all(scaled_confidence_interval >= np.pi):
                return K_cand, False

        return K, is_upper_plane

    def _sample(self) -> None:
        """
        Use the external sample callable to get the count of good states for $Q^kA$ (states with 1 in the last qubit).
        Effectively implements line 16, Algorithm 1, [1].
        """
        # To optimize results, the paper's algorithm applies the "no-overshooting condition" which limits
        # the number of shots in each iteration (lines 12-15, Algorithm 1, [1]). As the calculation is not very
        # simple, we currently don't support this and use constant number of shots.
        self._current().num_shots = self._num_shots

        self._current().good_counts = self._sample_callable(
            self._current().k, self._current().num_shots
        )

    def _calculate_confidence_interval(self) -> None:
        """
        Calculate the next confidence interval based on the last sample's results.
        Effectively implements lines 17-28, Algorithm 1, [1].
        """
        prob = self._current().good_counts / self._current().num_shots

        # The paper specifies two possibles confidence interval methods: Clopper-Perason or Chernoff-Hoeffding.
        # We currently support only the latter.
        prob_min, prob_max = self._chernoff_hoeffding(prob)

        if self._current().is_upper_plane:
            theta = np.arccos(1 - 2 * np.array([prob_min, prob_max]))
        else:
            theta = 2 * np.pi - np.arccos(1 - 2 * np.array([prob_max, prob_min]))

        scaled_confidence_interval = (
            self._current().K * self._prev().confidence_interval
        )
        number_of_wraps = scaled_confidence_interval // (2 * np.pi)

        # Sometimes we have edge cases where the lower or upper bound of the scaled interval fall exactly
        # on 2pi*T for some integer T, and the number of wraps might be rounded up or down wrongfuly.
        # To fix it, use the number of wraps of the middle point in the scaled interval.
        if number_of_wraps[0] + 1 == number_of_wraps[1]:
            number_of_wraps_of_middle = np.mean(scaled_confidence_interval) // (
                2 * np.pi
            )
            number_of_wraps = np.array(
                [number_of_wraps_of_middle, number_of_wraps_of_middle]
            )

        if number_of_wraps[0] != number_of_wraps[1]:
            raise RuntimeError(
                f"Number of wraps of the lower and upper bounds should be equal, got {number_of_wraps}"
            )

        self._current().confidence_interval = (
            2 * np.pi * number_of_wraps + theta
        ) / self._current().K

    def _chernoff_hoeffding(self, prob: float) -> tuple[float, float]:
        """
        The Chernoff-Hoeffding confidence interval method.
        Effectively implements lines 20-22, Algorithm 1, [1].
        """
        epsilon = np.sqrt(
            np.log(2 * self._max_rounds / self._alpha)
            / (2 * self._accumulated_num_shots())
        )
        return max(0, prob - epsilon), min(1, prob + epsilon)

    def _accumulated_num_shots(self) -> int:
        num_shots = 0
        for iteration in reversed(self.iterations):
            if iteration.K == self._current().K:
                num_shots += iteration.num_shots
            else:
                break
        return num_shots


@dataclass(init=False, repr=False, eq=False)
class IterationInfo:
    """
    The information stored on each iteration of IQAE.
    """

    K: int  # K = 4k + 2 where k is the power of Q on each iteration
    is_upper_plane: bool  # Wheter the scaled confidence interval is in the upper or lower half plane (in the paper: "up")
    confidence_interval: (
        np.ndarray
    )  # The current confidence interval (in the paper: "(theta_l, theta_u)")

    good_counts: int
    num_shots: int = 0

    @property
    def k(self) -> int:
        return (self.K - 2) // 4

    @k.setter
    def k(self, k: int) -> None:
        self.K = 4 * k + 2


def interval_len(interval: np.ndarray) -> float:
    return interval[1] - interval[0]
