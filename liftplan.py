import sys
from collections import namedtuple
from lark import Lark, Token
from lark.visitors import Interpreter

ERR = "error"
NUMERIC = ("int", "float")
Entry = namedtuple("Entry", "type kind cv")   # kind: var | const | builtin | exercise

class Env:
    """Symbol table: a stack of scopes (static, nested scoping)."""
    def __init__(self):
        self.scopes = [{}]
    def push(self):
        self.scopes.append({})
    def pop(self):
        self.scopes.pop()
    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    def declared_here(self, name):
        return name in self.scopes[-1]
    def insert(self, name, entry):
        self.scopes[-1][name] = entry

def compat(target, t):
    return t == target or t == ERR or (target == "float" and t == "int")

def arith(t1, t2):
    if ERR in (t1, t2):
        return ERR
    if t1 in NUMERIC and t2 in NUMERIC:
        return "int" if t1 == t2 == "int" else "float"
    return ERR

class Checker(Interpreter):
    """Top-down traversal; method names are the rule / alias names."""

    def __init__(self):
        super().__init__()
        self.env = Env()
        self.env.insert("last_rpe", Entry("float", "builtin", None))
        self.env.insert("fatigue", Entry("int", "builtin", None))
        self.errors = []
        self.sessions = {}            # (week, session name) -> guaranteed volume
        self.expected_week = 1
        self.current_week = 0
        self.session_names = set()

    # ---- helpers --------------------------------------------------------
    def err(self, node, msg):
        line = node.line if isinstance(node, Token) else getattr(node.meta, "line", "?")
        self.errors.append(f"line {line}: {msg}")

    def expect_numeric(self, node, t, what):
        if t not in NUMERIC and t != ERR:
            self.err(node, f"{what} must be numeric")

    # ---- program and declarations --------------------------------------
    def start(self, tree):
        self.env.push()
        total = 0
        for child in tree.children[1:]:                 # children[0] is the program ID
            total += self.visit(child) or 0
        return total

    def var_decl(self, tree):
        name, typ, expr = tree.children
        t, _ = self.visit(expr)                         # new name NOT yet visible
        if self.env.declared_here(name):
            self.err(name, f"'{name}' already declared in this scope")
        if not compat(str(typ), t):
            self.err(name, f"cannot initialise {typ} '{name}' with {t}")
        self.env.insert(str(name), Entry(str(typ), "var", None))
        return 0

    def const_decl(self, tree):
        name, typ, expr = tree.children
        t, cv = self.visit(expr)
        if self.env.declared_here(name):
            self.err(name, f"'{name}' already declared in this scope")
        if not compat(str(typ), t):
            self.err(name, f"cannot initialise {typ} '{name}' with {t}")
            cv = None
        self.env.insert(str(name), Entry(str(typ), "const", cv))
        return 0

    def exercise_decl(self, tree):
        name, *attrs = tree.children
        for a in attrs:
            self.visit(a)
        if self.env.declared_here(name):
            self.err(name, f"'{name}' already declared in this scope")
        self.env.insert(str(name), Entry(None, "exercise", None))
        return 0

    def attr(self, tree):
        key, expr = tree.children
        t, _ = self.visit(expr)
        if t not in ("string", ERR):
            self.err(key, f"attribute '{key}' must be a string")

    # ---- routine / week / session --------------------------------------
    def routine_decl(self, tree):
        self.expected_week = 1
        return sum(self.visit(w) for w in tree.children[1:])

    def week(self, tree):
        num = int(tree.children[0])
        if num != self.expected_week:
            self.err(tree.children[0],
                     f"week {num} out of sequence (expected {self.expected_week})")
        self.expected_week = num + 1
        self.current_week = num
        self.session_names = set()
        self.env.push()
        vol = sum(self.visit(s) for s in tree.children[1:])
        self.env.pop()
        return vol

    def session(self, tree):
        name_tok, block = tree.children
        name = str(name_tok).strip('"')
        if name in self.session_names:
            self.err(name_tok, f"duplicate session {name_tok} in week {self.current_week}")
        self.session_names.add(name)
        vol = self.visit(block)
        self.sessions[(self.current_week, name)] = vol
        return vol

    # ---- statements (return the guaranteed volume) ----------------------
    def block(self, tree):
        self.env.push()
        vol = sum(self.visit(s) or 0 for s in tree.children)
        self.env.pop()
        return vol

    def assign(self, tree):
        name, expr = tree.children
        t, _ = self.visit(expr)
        e = self.env.lookup(name)
        if e is None:
            self.err(name, f"'{name}' is not declared")
        elif e.kind != "var":
            self.err(name, f"'{name}' is a {e.kind} and cannot be assigned")
        elif not compat(e.type, t):
            self.err(name, f"cannot assign {t} to {e.type} '{name}'")
        return 0

    def perform(self, tree):
        name, sets_e, reps_e, *opts = tree.children
        e = self.env.lookup(name)
        if e is None or e.kind != "exercise":
            self.err(name, f"'{name}' is not a declared exercise")
        st, scv = self.visit(sets_e)
        rt, rcv = self.visit(reps_e)
        for t in (st, rt):
            if t not in ("int", ERR):
                self.err(name, "sets and reps must be integers")
                break
        load_cv, rpe_cv = 1, None                       # no load = bodyweight, factor 1
        for opt in opts:
            t, cv = self.visit(opt.children[0])
            self.expect_numeric(opt, t, opt.data)
            if opt.data == "load":
                load_cv = cv
            else:
                rpe_cv = cv
        if rpe_cv is not None and not 1 <= rpe_cv <= 10:
            self.err(name, f"rpe {rpe_cv} out of range [1, 10]")
        if None in (scv, rcv, load_cv):
            return 0
        return scv * rcv * load_cv

    def rest(self, tree):
        t, _ = self.visit(tree.children[0])
        self.expect_numeric(tree, t, "rest duration")
        return 0

    def if_stmt(self, tree):
        t, _ = self.visit(tree.children[0])
        if t not in ("bool", ERR):
            self.err(tree, "condition must be boolean")
        branches = [self.visit(b) for b in tree.children[1:]]
        return min(branches) if len(branches) == 2 else 0

    def repeat(self, tree):
        t, cv = self.visit(tree.children[0])
        if t not in ("int", ERR):
            self.err(tree, "repetition count must be an integer")
        vol = self.visit(tree.children[1])
        return cv * vol if t == "int" and cv is not None else 0

    circuit = repeat                                    # same equations as repeat

    # ---- expressions (return (type, cv)) --------------------------------
    def int_lit(self, tree):
        return "int", int(tree.children[0])

    def float_lit(self, tree):
        return "float", float(tree.children[0])

    def str_lit(self, tree):
        return "string", None

    def true(self, tree):
        return "bool", None

    false = true

    def var(self, tree):
        name = tree.children[0]
        e = self.env.lookup(name)
        if e is None:
            self.err(name, f"'{name}' is not declared")
            return ERR, None
        if e.kind == "exercise":
            self.err(name, f"exercise '{name}' used as a value")
            return ERR, None
        return e.type, (e.cv if e.kind == "const" else None)

    def _arith(self, tree, op):
        a, _operator_token, b = tree.children          # binary nodes keep the operator token
        t1, c1 = self.visit(a)
        t2, c2 = self.visit(b)
        t = arith(t1, t2)
        if t == ERR and ERR not in (t1, t2):
            self.err(tree, f"operator needs numeric operands, got {t1} and {t2}")
        cv = None
        if t != ERR and c1 is not None and c2 is not None:
            cv = op(c1, c2, t)
        return t, cv, c2

    def plus(self, tree):
        t, cv, _ = self._arith(tree, lambda a, b, t: a + b)
        return t, cv

    def minus(self, tree):
        t, cv, _ = self._arith(tree, lambda a, b, t: a - b)
        return t, cv

    def times(self, tree):
        t, cv, _ = self._arith(tree, lambda a, b, t: a * b)
        return t, cv

    def divide(self, tree):
        t, cv, c2 = self._arith(
            tree, lambda a, b, t: None if b == 0 else (a // b if t == "int" else a / b))
        if c2 == 0:
            self.err(tree, "division by zero")
        return t, cv

    def neg(self, tree):
        t, cv = self.visit(tree.children[1])             # children[0] is the MINUS token
        if t not in NUMERIC and t != ERR:
            self.err(tree, "unary minus needs a numeric operand")
            return ERR, None
        return t, (-cv if cv is not None else None)

    def rel(self, tree):
        a, op, b = tree.children
        (t1, _), (t2, _) = self.visit(a), self.visit(b)
        both_num = t1 in NUMERIC and t2 in NUMERIC
        ok = both_num or (op in ("==", "!=") and t1 == t2)
        if not ok and ERR not in (t1, t2):
            self.err(tree, f"cannot compare {t1} with {t2}")
        return (ERR if not ok else "bool"), None

    def _logic(self, tree):
        types = [self.visit(c)[0] for c in tree.children]
        if any(t not in ("bool", ERR) for t in types):
            self.err(tree, "logical operators need boolean operands")
            return ERR, None
        return "bool", None

    or_ = and_ = not_ = _logic


# ---------------------------------------------------------------------
parser = Lark.open("liftplan.lark", parser="lalr", propagate_positions=True, debug=True)


def check(source):
    tree = parser.parse(source)
    checker = Checker()
    total = checker.visit(tree)
    return checker.errors, total, checker.sessions


if __name__ == "__main__":
    path = sys.argv[1]
    errors, total, sessions = check(open(path).read())
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print("OK - no semantic errors")
    for (week, name), vol in sessions.items():
        print(f"  week {week}, session {name!r}: guaranteed volume {vol}")
    print(f"  program total: {total}")
