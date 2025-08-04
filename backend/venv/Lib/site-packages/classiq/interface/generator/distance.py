import numpy as np

# Taken and modified from quantum_tsp_tutorials repository of mstechly in github.
# https://github.com/mstechly/quantum_tsp_tutorials


def _distance_between_points(point_1: np.ndarray, point_2: np.ndarray) -> float:
    return float(np.linalg.norm(point_1 - point_2))


def get_distance_matrix(cities: np.ndarray) -> list[list[float]]:
    number_of_cities = len(cities)
    matrix = np.zeros((number_of_cities, number_of_cities))
    for i in range(number_of_cities):
        for j in range(i, number_of_cities):
            matrix[i][j] = _distance_between_points(cities[i], cities[j])
            matrix[j][i] = matrix[i][j]
    return matrix.tolist()


def get_rand_euclidean_distance_matrix(num_points: int) -> list[list[float]]:
    _points_array_dim = 2
    points = np.random.rand(num_points, _points_array_dim)
    distance_matrix = get_distance_matrix(points)
    return distance_matrix


def get_rand_distance_matrix(num_points: int) -> list[list[float]]:
    distance_matrix = np.random.rand(num_points, num_points)
    distance_matrix *= 0.5
    distance_matrix += distance_matrix.T
    distance_matrix -= np.diag(np.diag(distance_matrix))
    return distance_matrix.tolist()
