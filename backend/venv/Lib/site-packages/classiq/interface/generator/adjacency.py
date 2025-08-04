import numpy as np


def get_rand_adjacency_matrix(num_vertices: int) -> list[list[bool]]:
    adjacency_matrix = np.random.choice([0, 1], size=(num_vertices, num_vertices))
    for i in range(num_vertices):
        for j in range(num_vertices):
            if i > j:
                adjacency_matrix[i, j] = adjacency_matrix[j, i]
    adjacency_matrix -= np.diag(np.diag(adjacency_matrix))
    return adjacency_matrix.tolist()
