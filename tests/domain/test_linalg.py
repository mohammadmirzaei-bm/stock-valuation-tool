"""تست‌های واحد جبر خطی خالص.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain._linalg import dot, mat_vec, solve, submatrix
from stock_valuation.domain.errors import CalculationError, ValidationError


class TestDotAndMatVec(unittest.TestCase):
    """ضرب داخلی و ضرب ماتریس در بردار با مقادیر دستی"""

    def test_dot_hand_computed(self):
        self.assertEqual(dot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]), 32.0)

    def test_mat_vec_hand_computed(self):
        # [[1, 2], [3, 4]] @ [5, 6] = [17, 39]
        self.assertEqual(mat_vec([[1.0, 2.0], [3.0, 4.0]], [5.0, 6.0]), [17.0, 39.0])

    def test_mat_vec_rectangular(self):
        self.assertEqual(
            mat_vec([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], [1.0, 1.0, 1.0]),
            [6.0, 15.0],
        )

    def test_inputs_not_mutated(self):
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        vector = [5.0, 6.0]
        other = [1.0, 1.0]
        matrix_snapshot = [row[:] for row in matrix]
        vector_snapshot = vector[:]
        other_snapshot = other[:]
        mat_vec(matrix, vector)
        dot(vector, other)
        self.assertEqual(matrix, matrix_snapshot)
        self.assertEqual(vector, vector_snapshot)
        self.assertEqual(other, other_snapshot)

    def test_dimension_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            dot([1.0, 2.0], [1.0])
        with self.assertRaises(ValidationError):
            mat_vec([[1.0, 2.0]], [1.0])

    def test_non_finite_rejected(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    dot([bad, 1.0], [1.0, 1.0])
                with self.assertRaises(ValidationError):
                    mat_vec([[bad]], [1.0])


class TestSubmatrix(unittest.TestCase):
    """زیرماتریس اصلی؛ ترتیب اندیس‌ها حفظ می‌شود و ورودی تغییر نمی‌کند"""

    def test_preserves_index_order(self):
        matrix = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ]
        snapshot = [row[:] for row in matrix]
        self.assertEqual(submatrix(matrix, [2, 0]), [[9.0, 7.0], [3.0, 1.0]])
        self.assertEqual(submatrix(matrix, [0, 2]), [[1.0, 3.0], [7.0, 9.0]])
        self.assertEqual(matrix, snapshot)

    def test_invalid_indices_rejected(self):
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        for indices in ([], [0, 0], [2], [-1], [True], [1.5]):
            with self.subTest(indices=indices):
                with self.assertRaises(ValidationError):
                    submatrix(matrix, indices)


class TestSolve(unittest.TestCase):
    """حذف گاوسی با محورگیری جزئی روی دستگاه‌های دستی"""

    def test_two_by_two(self):
        # 2x + y = 5 و x + 3y = 10 ⇒ x = 1، y = 3
        solution = solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0])
        self.assertEqual(solution, [1.0, 3.0])

    def test_three_by_three_with_partial_pivot(self):
        # بزرگ‌ترین درایه ستون اول در سطر دوم است، پس جابه‌جایی لازم است.
        # جواب دستی [1, 1, 1] است.
        matrix = [
            [2.0, 1.0, 1.0],
            [4.0, -6.0, 0.0],
            [-2.0, 7.0, 2.0],
        ]
        solution = solve(matrix, [4.0, -2.0, 7.0])
        self.assertEqual(solution, [1.0, 1.0, 1.0])

    def test_zero_on_diagonal_requires_row_swap(self):
        # بدون جابه‌جایی سطر، محور اول صفر است.
        # y = 2 و x = 3
        solution = solve([[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0])
        self.assertEqual(solution, [3.0, 2.0])

    def test_one_by_one(self):
        self.assertEqual(solve([[2.0]], [4.0]), [2.0])

    def test_singular_matrix(self):
        with self.assertRaises(CalculationError) as caught:
            solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])
        self.assertEqual(str(caught.exception), "نتیجه محاسبه نامعتبر است")

    def test_pivot_below_tolerance_rejected(self):
        with self.assertRaises(CalculationError):
            solve([[1e-13, 0.0], [0.0, 1.0]], [1e-13, 2.0])

    def test_pivot_above_tolerance_accepted(self):
        solution = solve([[1e-10, 0.0], [0.0, 1.0]], [1e-10, 2.0])
        self.assertAlmostEqual(solution[0], 1.0)
        self.assertAlmostEqual(solution[1], 2.0)

    def test_non_square_and_mismatched_rhs_rejected(self):
        with self.assertRaises(ValidationError):
            solve([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], [1.0, 2.0, 3.0])
        with self.assertRaises(ValidationError):
            solve([[1.0, 0.0], [0.0, 1.0]], [1.0])

    def test_non_finite_rejected(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    solve([[bad, 0.0], [0.0, 1.0]], [1.0, 1.0])

    def test_inputs_not_mutated_and_deterministic(self):
        matrix = [[2.0, 1.0], [1.0, 3.0]]
        rhs = [5.0, 10.0]
        matrix_snapshot = [row[:] for row in matrix]
        rhs_snapshot = rhs[:]
        first = solve(matrix, rhs)
        second = solve(matrix, rhs)
        self.assertEqual(first, second)
        self.assertEqual(first, [1.0, 3.0])
        self.assertEqual(matrix, matrix_snapshot)
        self.assertEqual(rhs, rhs_snapshot)


if __name__ == "__main__":
    unittest.main()
