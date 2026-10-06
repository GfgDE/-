from fractions import Fraction as F

def fmt(x: F) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def print_table(T, note=""):
    names = T["names"]
    basis = T["basis"]
    rows = T["rows"]
    obj = T["obj"]

    width = 8
    header = "баз.".ljust(width) + "".join(n.rjust(width) for n in names) + "RHS".rjust(width)
    print(header)
    print("-" * len(header))
    for i, row in enumerate(rows):
        line = names[basis[i]].ljust(width)
        line += "".join(fmt(v).rjust(width) for v in row[:-1])
        line += fmt(row[-1]).rjust(width)
        print(line)
    print("-" * len(header))
    line = "Z/W".ljust(width) + "".join(fmt(v).rjust(width) for v in obj[:-1])
    line += fmt(obj[-1]).rjust(width)
    print(line)
    if note:
        print(f"  ({note})")
    print()

def canon(c, A, signs, b, var_prefix="x"):
    A = [row[:] for row in A]
    b = b[:]
    signs = signs[:]
    m, n = len(A), len(c)

    for i in range(m):
        if b[i] < 0:
            A[i] = [-a for a in A[i]]
            b[i] = -b[i]
            if signs[i] == "<=":
                signs[i] = ">="
            elif signs[i] == ">=":
                signs[i] = "<="

    names = [f"{var_prefix}{j+1}" for j in range(n)]
    basis0 = [None] * m
    slack_count = 0

    for i in range(m):
        col = [F(0)] * m
        if signs[i] == "<=":
            slack_count += 1
            col[i] = F(1)
            names.append(f"s{slack_count}")
            for r in range(m):
                A[r].append(col[r])
            basis0[i] = len(names) - 1
        elif signs[i] == ">=":
            slack_count += 1
            col[i] = F(-1)
            names.append(f"s{slack_count}")
            for r in range(m):
                A[r].append(col[r])
    return A, b, names, basis0

def start_aux(A, b, names, basis0):
    m = len(A)
    A = [row[:] for row in A]
    names = names[:]
    basis = basis0[:]
    art_idx = []

    for i in range(m):
        if basis[i] is None:
            col = [F(0)] * m
            col[i] = F(1)
            for r in range(m):
                A[r].append(col[r])
            names.append(f"a{len(art_idx)+1}")
            basis[i] = len(names) - 1
            art_idx.append(len(names) - 1)

    n_total = len(names)
    rows = [A[i] + [b[i]] for i in range(m)]

    obj = [F(0)] * n_total + [F(0)]
    for j in art_idx:
        obj[j] = F(-1)

    T = {"names": names, "basis": basis, "rows": rows, "obj": obj}

    for i in range(m):
        if basis[i] in art_idx:
            factor = T["obj"][basis[i]]
            if factor != 0:
                T["obj"] = [T["obj"][k] - factor * T["rows"][i][k]
                            for k in range(n_total + 1)]

    return T, art_idx


def step(T, forbidden_cols=frozenset()):
    n = len(T["names"])
    obj = T["obj"]

    candidates = [j for j in range(n)
                  if j not in forbidden_cols and obj[j] > 0]
    if not candidates:
        return ("optimal", None, None, None)

    enter = min(candidates)
    ratios = []
    for i, row in enumerate(T["rows"]):
        a = row[enter]
        if a > 0:
            ratios.append((row[-1] / a, T["basis"][i], i))

    if not ratios:
        return ("unbounded", enter, None, None)

    min_ratio = min(r[0] for r in ratios)
    tied = [r for r in ratios if r[0] == min_ratio]
    leave_row = min(tied, key=lambda r: r[1])[2]
    leaving_var = T["basis"][leave_row]

    full = T["rows"] + [T["obj"]]
    pr = full[leave_row]
    pv = pr[enter]
    full[leave_row] = [v / pv for v in pr]
    for i in range(len(full)):
        if i != leave_row:
            f = full[i][enter]
            if f != 0:
                full[i] = [full[i][k] - f * full[leave_row][k]
                           for k in range(len(full[i]))]

    T["rows"] = full[:-1]
    T["obj"] = full[-1]
    T["basis"][leave_row] = enter
    return ("pivot", enter, leave_row, leaving_var)

def phase(T, title, forbidden_cols=frozenset()):
    print(f"\n===== {title}: начальная таблица =====")
    print_table(T)
    it = 1
    while True:
        status, enter, leave_row, leaving_var = step(T, forbidden_cols)
        if status == "optimal":
            print(f"Коэффициенты >= 0 у всех небазисных - оптимум достигнут.\n")
            return "optimal"
        if status == "unbounded":
            print(f"У столбца {T['names'][enter]} положительный коэффициент, "
                  f"но нет ограничивающей строки - задача неограничена.\n")
            return "unbounded"
        note = f"итерация {it}: вход {T['names'][enter]}, выход {T['names'][leaving_var]}"
        print(f"----- {title}: {note} -----")
        print_table(T)
        it += 1

def to_main(T, c, names_orig_count, art_idx):
    keep = [j for j in range(len(T["names"])) if j not in art_idx]
    index_map = {old: new for new, old in enumerate(keep)}

    names = [T["names"][j] for j in keep]
    rows = [[row[j] for j in keep] + [row[-1]] for row in T["rows"]]
    basis = [index_map[b] for b in T["basis"]]

    n_total = len(names)
    c_full = list(c) + [F(0)] * (n_total - names_orig_count)

    obj = [-c_full[j] for j in range(n_total)] + [F(0)]
    T2 = {"names": names, "basis": basis, "rows": rows, "obj": obj}

    for i in range(len(rows)):
        j = basis[i]
        factor = T2["obj"][j]
        if factor != 0:
            T2["obj"] = [T2["obj"][k] - factor * T2["rows"][i][k]
                         for k in range(n_total + 1)]

    return T2

def read(T, n_orig):
    x = [F(0)] * n_orig
    for i, j in enumerate(T["basis"]):
        if j < n_orig:
            x[j] = T["rows"][i][-1]
    Z = T["obj"][-1]
    return x, Z

def solve_variant_8():
    c = [F(1), F(3), F(2), F(1)]
    A = [
        [F(1), F(1), F(0), F(2)],
        [F(0), F(1), F(1), F(1)],
        [F(2), F(0), F(1), F(0)],
    ]
    signs = ["<=", "=", ">="]
    b = [F(8), F(6), F(2)]

    print("#" * 70)
    print("ВАРИАНТ 8")
    print(f"Минимизировать Z = x1 + 3x2 + 2x3 + x4")
    for row, s, rhs in zip(A, signs, b):
        print("  " + " + ".join(f"{fmt(v)}x{j+1}" for j, v in enumerate(row) if v != 0)
              + f" {s} {fmt(rhs)}")
    print("#" * 70)

    A2, b2, names, basis0 = canon(c, A, signs, b)
    print("\nКанонический вид. Переменные:", names)

    T, art_idx = start_aux(A2, b2, names, basis0)
    status1 = phase(T, "ФАЗА I (вспомогательная задача, W = сумма искусственных)")

    W = T["obj"][-1]
    print(f"Итог фазы I: W = {fmt(W)}")
    if W != 0:
        print("W > 0  =>  область допустимых решений ПУСТА. Решений нет.")
        return
    print("W = 0  =>  найдено допустимое базисное решение исходной задачи.\n")

    T2 = to_main(T, c, len(c), set(art_idx))
    status2 = phase(T2, "ФАЗА II (основная задача, минимизация Z)")

    if status2 == "unbounded":
        print("Целевая функция не ограничена снизу на допустимом множестве.")
        return

    x, Z = read(T2, len(c))
    print("=" * 70)
    print("ОТВЕТ")
    print("=" * 70)
    for j, v in enumerate(x):
        print(f"  x{j+1} = {fmt(v)}")
    print(f"  Z(min) = {fmt(Z)}")

    print("\nПроверка допустимости:")
    checks = [
        ("x1 + x2 + 2x4", x[0] + x[1] + 2 * x[3], "<=", F(8)),
        ("x2 + x3 + x4", x[1] + x[2] + x[3], "=", F(6)),
        ("2x1 + x3", 2 * x[0] + x[2], ">=", F(2)),
    ]
    for label, val, s, rhs in checks:
        ok = {"<=": val <= rhs, "=": val == rhs, ">=": val >= rhs}[s]
        print(f"  {label} = {fmt(val)} {s} {fmt(rhs)}  ->  {'OK' if ok else 'НАРУШЕНО'}")


if __name__ == "__main__":
    solve_variant_8()
