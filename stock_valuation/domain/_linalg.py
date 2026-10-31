"""جبر خطی خالص روی فهرست‌های تو در تو — فقط کتابخانه استاندارد.

کمک‌کننده‌های خصوصی برای بهینه‌سازی سبد. هیچ وابستگی‌ای به numpy یا scipy
ندارند، ورودی‌ها را تغییر نمی‌دهند و ترتیب عملیات ثابت است تا خروجی قطعی بماند.

قرارداد خطا:
    ValidationError: شکل، نوع یا مقدار ورودی نامعتبر
    CalculationError: ماتریس منفرد یا بدشرط، یا نتیجه غیرمتناهی
"""

import math
from typing import List, Sequence

from .errors import CalculationError, ValidationError
from .validators import LINEAR_PIVOT_TOLERANCE

_INVALID_RESULT = "نتیجه محاسبه نامعتبر است"


def _as_finite_number(value: float, field_name: str) -> float:
    """عدد متناهی (نه bool) را برمی‌گرداند؛ در غیر این صورت ValidationError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"❌ {field_name} باید عدد باشد!")
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
    return float(value)


def _rows(matrix: Sequence[Sequence[float]], field_name: str) -> List[List[float]]:
    """کپی سطری یک ماتریس مستطیلی با درایه‌های متناهی.

    Args:
        matrix: ماتریس ورودی؛ دست‌نخورده می‌ماند
        field_name: نام فیلد برای پیام خطا

    Returns:
        List[List[float]]: کپی مستقل با همان ترتیب سطرها و ستون‌ها

    Raises:
        ValidationError: اگر ماتریس خالی، نامستطیل یا دارای درایه نامعتبر باشد
    """
    if not isinstance(matrix, (list, tuple)) or len(matrix) == 0:
        raise ValidationError(f"❌ {field_name} باید ماتریس غیرخالی باشد!")
    copied: List[List[float]] = []
    width: int = -1
    for row_index, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) == 0:
            raise ValidationError(f"❌ سطرهای {field_name} باید غیرخالی باشند!")
        if width < 0:
            width = len(row)
        elif len(row) != width:
            raise ValidationError(f"❌ سطرهای {field_name} باید هم‌طول باشند!")
        copied.append(
            [
                _as_finite_number(value, f"درایه ({row_index}, {col_index}) {field_name}")
                for col_index, value in enumerate(row)
            ]
        )
    return copied


def _vector(values: Sequence[float], field_name: str) -> List[float]:
    """کپی یک بردار غیرخالی با درایه‌های متناهی."""
    if not isinstance(values, (list, tuple)) or len(values) == 0:
        raise ValidationError(f"❌ {field_name} باید بردار غیرخالی باشد!")
    return [
        _as_finite_number(value, f"درایه {index} {field_name}")
        for index, value in enumerate(values)
    ]


def _require_finite_result(value: float) -> float:
    """نتیجه نامتناهی یا NaN را به خطای محاسباتی تبدیل می‌کند."""
    if not math.isfinite(value):
        raise CalculationError(_INVALID_RESULT)
    return value


def dot(x: Sequence[float], y: Sequence[float]) -> float:
    """
    ضرب داخلی دو بردار هم‌طول

    Args:
        x: بردار اول
        y: بردار دوم

    Returns:
        float: مجموع حاصل‌ضرب درایه‌های متناظر

    Raises:
        ValidationError: اگر بردارها خالی، ناهم‌طول یا دارای مقدار نامعتبر باشند
        CalculationError: اگر حاصل ضرب داخلی متناهی نباشد
    """
    left = _vector(x, "بردار")
    right = _vector(y, "بردار")
    if len(left) != len(right):
        raise ValidationError("❌ طول دو بردار ضرب داخلی باید برابر باشد!")
    total = 0.0
    for left_value, right_value in zip(left, right):
        total += left_value * right_value
    return _require_finite_result(total)


def mat_vec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    """
    ضرب ماتریس در بردار

    Args:
        matrix: ماتریس مستطیلی
        vector: برداری به طول تعداد ستون‌های ماتریس

    Returns:
        List[float]: بردار حاصل، به ترتیب سطرهای ماتریس

    Raises:
        ValidationError: اگر ابعاد ناسازگار یا درایه‌ها نامعتبر باشند
        CalculationError: اگر مؤلفه‌ای از حاصل متناهی نباشد
    """
    rows = _rows(matrix, "ماتریس")
    values = _vector(vector, "بردار")
    if len(values) != len(rows[0]):
        raise ValidationError("❌ طول بردار باید برابر تعداد ستون‌های ماتریس باشد!")
    result: List[float] = []
    for row in rows:
        total = 0.0
        for column, value in enumerate(row):
            total += value * values[column]
        result.append(_require_finite_result(total))
    return result


def submatrix(matrix: Sequence[Sequence[float]], indices: Sequence[int]) -> List[List[float]]:
    """
    زیرماتریس اصلی با حفظ ترتیب اندیس‌ها

    سطرها و ستون‌های ``indices`` به همان ترتیب داده‌شده (نه مرتب‌شده) انتخاب
    می‌شوند. ماتریس ورودی کپی نمی‌شود و تغییر نمی‌کند؛ خروجی ماتریس تازه‌ای است.

    Args:
        matrix: ماتریس مستطیلی
        indices: اندیس‌های یکتا و معتبر برای سطر و ستون

    Returns:
        List[List[float]]: زیرماتریس به ترتیب ``indices``

    Raises:
        ValidationError: اگر اندیس‌ها خالی، تکراری یا خارج از ابعاد باشند
    """
    rows = _rows(matrix, "ماتریس")
    if not isinstance(indices, (list, tuple)) or len(indices) == 0:
        raise ValidationError("❌ اندیس‌های زیرماتریس باید غیرخالی باشند!")
    row_count = len(rows)
    column_count = len(rows[0])
    chosen: List[int] = []
    for index in indices:
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValidationError("❌ اندیس زیرماتریس باید عدد صحیح باشد!")
        if not 0 <= index < row_count or not 0 <= index < column_count:
            raise ValidationError(f"❌ اندیس {index} خارج از ابعاد ماتریس است!")
        if index in chosen:
            raise ValidationError("❌ اندیس‌های زیرماتریس باید یکتا باشند!")
        chosen.append(index)
    return [[rows[row_index][column_index] for column_index in chosen] for row_index in chosen]


def solve(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    """
    حل دستگاه خطی Ax = b با حذف گاوسی و محورگیری جزئی

    ماتریس باید مربعی باشد. در هر ستون، سطر دارای بزرگ‌ترین قدر مطلق در
    زیر (و روی) قطر انتخاب می‌شود؛ اگر چند سطر قدر مطلق برابر داشته باشند،
    سطر با اندیس کوچک‌تر می‌ماند (مقایسه اکید). اگر قدر مطلق محور از
    ``LINEAR_PIVOT_TOLERANCE`` (مقدار مطلق ``1e-12``) کمتر باشد، ماتریس
    منفرد یا بدشرط است و حل رد می‌شود. ورودی‌ها کپی می‌شوند و تغییر نمی‌کنند.

    Args:
        matrix: ماتریس ضرایب مربعی
        vector: بردار سمت راست، هم‌طول با تعداد سطرها

    Returns:
        List[float]: جواب دستگاه به ترتیب مجهول‌ها

    Raises:
        ValidationError: اگر ماتریس مربعی نباشد یا ابعاد و درایه‌ها نامعتبر باشند
        CalculationError: اگر ماتریس منفرد یا بدشرط باشد یا جواب متناهی نباشد
    """
    rows = _rows(matrix, "ماتریس")
    rhs = _vector(vector, "بردار سمت راست")
    size = len(rows)
    if len(rows[0]) != size:
        raise ValidationError("❌ ماتریس دستگاه باید مربعی باشد!")
    if len(rhs) != size:
        raise ValidationError("❌ طول بردار سمت راست باید برابر تعداد سطرهای ماتریس باشد!")

    for column in range(size):
        pivot_row = column
        pivot_abs = abs(rows[column][column])
        for row in range(column + 1, size):
            candidate = abs(rows[row][column])
            if candidate > pivot_abs:
                pivot_abs = candidate
                pivot_row = row
        if pivot_abs < LINEAR_PIVOT_TOLERANCE:
            raise CalculationError(_INVALID_RESULT)
        if pivot_row != column:
            rows[column], rows[pivot_row] = rows[pivot_row], rows[column]
            rhs[column], rhs[pivot_row] = rhs[pivot_row], rhs[column]
        pivot = rows[column][column]
        for row in range(column + 1, size):
            factor = rows[row][column] / pivot
            if not math.isfinite(factor):
                raise CalculationError(_INVALID_RESULT)
            for trailing in range(column, size):
                rows[row][trailing] -= factor * rows[column][trailing]
            rhs[row] -= factor * rhs[column]

    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        diagonal = rows[row][row]
        if abs(diagonal) < LINEAR_PIVOT_TOLERANCE:
            raise CalculationError(_INVALID_RESULT)
        total = rhs[row]
        for column in range(row + 1, size):
            total -= rows[row][column] * solution[column]
        solution[row] = _require_finite_result(total / diagonal)
    return solution
