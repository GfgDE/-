import json
import sys

import sympy as sp

x, y = sp.symbols("x y", real=True)
lam = sp.symbols("lam", real=True)


def solve_lagrange(f_str, h_str):
    ns = {"x": x, "y": y}
    f = sp.sympify(f_str, locals=ns)
    h = sp.sympify(h_str, locals=ns)
    out = []
    p = out.append

    p(f"f(x, y) = {f}")
    p(f"h(x, y) = {h} = 0")

    feas = sp.solve([h], [x, y], dict=True)
    p(f"множество {{h = 0}} непусто: {bool(feas)}")

    grad_h = [sp.diff(h, v) for v in (x, y)]
    p(f"grad h = {grad_h}")
    zero_grad = sp.solve(grad_h, [x, y], dict=True)
    on_set = [s for s in zero_grad if sp.simplify(h.subs(s)) == 0] if zero_grad else []
    p(f"точки ограничения, где grad h = 0: {on_set if on_set else 'нет'}  -> регулярность {'нарушена' if on_set else 'выполнена'}")

    L = f + lam * h
    p(f"L = f + lam*h = {sp.expand(L)}")
    eqs = [sp.diff(L, v) for v in (x, y)] + [h]
    names = ("dL/dx", "dL/dy", "h")
    for nm, e in zip(names, eqs):
        p(f"  {nm} = {sp.expand(e)} = 0")

    sols = sp.solve(eqs, [x, y, lam], dict=True)
    p(f"найдено действительных решений системы: {len(sols)}")

    hess = sp.hessian(L, (x, y))
    t = sp.Matrix([-grad_h[1], grad_h[0]])
    results = []
    for i, s in enumerate(sols, 1):
        pt = {x: s[x], y: s[y]}
        resid = sp.simplify(h.subs(pt))
        fval = sp.simplify(f.subs(pt))
        q = sp.simplify((t.T * hess.subs(s) * t)[0].subs(pt))
        kind = "строгий локальный минимум" if q > 0 else ("строгий локальный максимум" if q < 0 else "второй порядок не решает")
        p(f"решение {i}: x = {s[x]}, y = {s[y]}, lam = {s[lam]}; невязка h = {resid}; f = {fval}; t^T H t = {q} -> {kind}")
        results.append({"x": str(s[x]), "y": str(s[y]), "lam": str(s[lam]),
                        "residual": str(resid), "f": str(fval), "kind": kind})

    ysol = sp.solve(h, y)
    glob = None
    if len(ysol) == 1:
        g = sp.expand(f.subs(y, ysol[0]))
        crit = sp.solve(sp.diff(g, x), x)
        lim_p = sp.limit(g, x, sp.oo)
        lim_m = sp.limit(g, x, -sp.oo)
        p(f"подстановка y = {ysol[0]}: g(x) = {g} = {sp.factor(g)}; "
          f"g'(x) = {sp.diff(g, x)}; критические точки g: {crit}")
        p(f"  значения g в критических точках: {[sp.simplify(g.subs(x, c)) for c in crit]}")
        p(f"  lim g(x) при x -> +oo: {lim_p};  при x -> -oo: {lim_m}")
        glob = {"g": str(g), "limits": [str(lim_p), str(lim_m)]}
        if lim_p == sp.oo and lim_m == sp.oo:
            p("  g -> +oo на обоих концах, единственная критическая точка -> она даёт глобальный минимум, максимума нет")
    else:
        p("ограничение нельзя однозначно разрешить относительно y: глобальность проверять отдельно")

    return {"text": "\n".join(out), "solutions": results, "global": glob}


if __name__ == "__main__":
    if len(sys.argv) == 3:
        f_in, h_in = sys.argv[1], sys.argv[2]
    else:
        print("Метод множителей Лагранжа. Переменные: x, y. Ограничение вводить как h(x, y) = 0.")
        print("Пример: f = x**2 + y**2, h = x + y - 6")
        f_in = input("f(x, y) = ").strip()
        h_in = input("h(x, y) = ").strip()
        if not f_in or not h_in:
            sys.exit("нужны обе формулы")
    res = solve_lagrange(f_in, h_in)
    print(res["text"])
    with open("solver_result.json", "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in res.items() if k != "text"}, fh, ensure_ascii=False, indent=1)
