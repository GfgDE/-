from math import inf
from itertools import product


def allocate(income, total, lo, hi):
    if not isinstance(total, int) or total < 0:
        raise ValueError("Объем средств должен быть неотрицательным целым.")
    if not income:
        raise ValueError("Необходимо задать хотя бы один стартап.")
    if any(len(row) != total + 1 for row in income):
        raise ValueError("Для каждого стартапа нужны доходы для 0..total.")
    n = len(income)
    V = [[-inf] * (total + 1) for _ in range(n + 1)]
    A = [[[] for _ in range(total + 1)] for _ in range(n)]
    V[n][0] = 0
    for k in range(n - 1, -1, -1):
        for s in range(total + 1):
            for u in range(lo[k], min(hi[k], s) + 1):
                f = V[k + 1][s - u]
                if f == -inf:
                    continue
                c = income[k][u] + f
                if c > V[k][s]:
                    V[k][s], A[k][s] = c, [u]
                elif c == V[k][s]:
                    A[k][s].append(u)
    if V[0][total] == -inf:
        raise ValueError("Допустимого плана не существует.")
    plan, s = [], total
    for k in range(n):
        u = A[k][s][0]
        plan.append(u)
        s -= u
    assert s == 0 and sum(plan) == total
    assert all(lo[k] <= plan[k] <= hi[k] for k in range(n))
    assert sum(income[k][plan[k]] for k in range(n)) == V[0][total]
    return V[0][total], plan, V, A


def brute(income, total, lo, hi):
    n = len(income)
    best, plans = -inf, []
    for p in product(range(total + 1), repeat=n):
        if sum(p) != total or any(not lo[k] <= p[k] <= hi[k] for k in range(n)):
            continue
        v = sum(income[k][p[k]] for k in range(n))
        if v > best:
            best, plans = v, [p]
        elif v == best:
            plans.append(p)
    return best, plans


if __name__ == "__main__":
    pad = lambda row: [0] + row + [0] * (9 - len(row))
    income = [pad([5, 9, 12, 14, 15, 16, 17]),
              pad([8, 14, 18, 21, 30, 34, 36]),
              pad([4, 7, 11, 16, 18, 19, 20])]
    total, lo, hi = 9, [1, 1, 1], [7, 4, 7]

    opt, plan, V, A = allocate(income, total, lo, hi)
    print("Максимальный доход:", opt)
    print("Оптимальный план:", plan)
    for k in (2, 1, 0):
        print(f"V_{k+1}:", {s: V[k][s] for s in range(total + 1) if V[k][s] > -inf})
        print(f"A_{k+1}:", {s: A[k][s] for s in range(total + 1) if A[k][s]})
    bv, bp = brute(income, total, lo, hi)
    assert opt == bv and tuple(plan) in bp
    print("Проверка перебором:", bv, bp)

    print("\n--- Дополнительные тесты ---")

    print("T1:", allocate([[0], [0]], 0, [0, 0], [0, 0])[:2])

    print("T2:", allocate([[0, 3, 5, 9]], 3, [1], [3])[:2])

    print("T3:", allocate([[0] * 5] * 3, 4, [1, 1, 1], [4, 4, 4])[:2])

    inc = [[0, 1, 2, 3, 4]] * 2
    o, p, V4, A4 = allocate(inc, 4, [0, 0], [4, 4])
    print("T4:", o, p, brute(inc, 4, [0, 0], [4, 4]))

    inc = [[0, 1, 2, 3, 20], [0, 1, 1, 1, 1], [0, 0, 0, 0, 0]]
    print("T5:", allocate(inc, 4, [0, 0, 0], [4, 4, 4])[:2])

    for name, args in [("ресурс<0", ([[0, 1]], -1, [0], [1])),
                       ("неполная таблица", ([[0, 1, 2]], 3, [0], [3]))]:
        try:
            allocate(*args)
        except ValueError as e:
            print("T6", name, "->", e)

    try:
        allocate([[0, 1, 2]] * 3, 2, [1, 1, 1], [2, 2, 2])
    except ValueError as e:
        print("T7:", e)

    g = [1, 1, 1]
    print("Жадно: первый=7 (доход 17), второй=1 (8), третий=1 (4) -> 29 < 43")
