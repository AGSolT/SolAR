"""Implements the DynaMOSA preference sorting algorithm(s)."""


def preference_sorting(test_cases, updated_targets, pop_size):
    """
    Identify non-dominated Pareto fronts from the current generation of \
    test-cases. The 0-th non-dominated Pareto front is found using the \
    preference criterion.

    Inputs:
        - test_cases: The current generation of test cases.
        - updated_targets: The currently relevant targets.
        - pop_size: The population size, the function can stop if enough \
          non-dominated Pareto fronts have been identified to form the next \
          generation.
    Outputs:
        - Fs: An ordered list containing sets F, each F is a non-dominated \
              Pareto front.
    """
    P = set(test_cases)
    F = set()
    Fs = []
    for i, relevant in enumerate(updated_targets):
        if relevant:
            t_best = prefered(test_cases, i)
            t_best.rank = 0
            F.add(t_best)
    P = P - F
    Fs = Fs + [F]
    if len(F) > pop_size:
        F = P
        Fs = Fs + [F]
    else:
        Fs = Fs + fast_non_dominated_sort(P, updated_targets)
    return Fs


def prefered(test_cases, i):
    """
    Identify the "best test-case" for a given target in accordance with the \
    preference criterion.

    Inputs:
        - test_cases: The current generation of test cases.
        - i: The index of the target to cover.
    Outputs:
        - best_test: the best test-case for the given target in accordance \
          with the preference criterion.
    """
    test_cases = list(test_cases)
    best_test = test_cases[0]
    for tCase in test_cases[1:]:
        if tCase.distance_vector[i] < best_test.distance_vector[i]:
            best_test = tCase
        elif (tCase.distance_vector[i] == best_test.distance_vector[i]) & \
                (len(tCase.methodCalls) < len(best_test.methodCalls)):
            best_test = tCase
    return best_test


def fast_non_dominated_sort(test_cases, updated_targets):
    """
    Identify non-dominated Pareto fronts.

    Inputs:
        - test_cases: the current generation of test-cases that are not in \
                      the 0-th non-dominated Pareto front.
        - updated_targets: The targets that are reached but not have not yet \
                           been covered.
    Outputs:
        - Fs: An ordered list containing sets F, each F is a non-dominated \
              Pareto front.
    """
    Fs = []
    F = set()
    for p in test_cases:
        S = []
        n = 0
        for q in test_cases:
            if p != q:
                dominates = dominance_comparator(p, q, updated_targets)
                if dominates == 1:
                    S = S + [q]
                elif dominates == 0:
                    n += 1

        p.S = S
        p.n = n
        if n == 0:
            p.rank = 1
            F.add(p)

    Fs = Fs + [F]
    i = 1
    while len(F) > 0:
        Q = set()
        for p in F:
            for q in p.S:
                q.n = q.n - 1
                if q.n == 0:
                    q.rank = i + 1
                    Q.add(q)
        i += 1
        F = Q
        Fs.append(F)
    return Fs


def dominance_comparator(p, q, updated_targets):
    """
    Determine whether one test-case dominates the other or no, given two test \
    cases with their respected distance_vectors and the list of targets that \
    are reached but have not yet been covered .

    Inputs:
        - p, q: Two test cases to compare
        - updated_targets: The targets on which p and q should be compared \
        for domination.
    Outputs:
        - 2 if p dominates q
        - 1 if q dominates p
        - 0 otherwise
    """
    dom1 = False
    dom2 = False
    for i, b in enumerate(updated_targets):
        if b:
            if p.distance_vector[i] < q.distance_vector[i]:
                dom1 = True
            elif q.distance_vector[i] < p.distance_vector[i]:
                dom2 = True
            if dom1 & dom2:
                break

    if dom1 == dom2:
        return 2
    elif dom1:
        return 1
    else:
        return 0


def subvector_dist(F, updated_targets):
    """
    Calculate and set the subvector distance for a given non-dominated front.

    Inputs:
        - F: A non-dominated set of test-cases.
        - updated_targets: The list of targets on which to compare the \
                           test-cases.
    """
    for p in F:
        dist = 0
        for q in F:
            if p == q:
                pass
            else:
                cnt = 0
                for i, b in enumerate(updated_targets):
                    if b:
                        if q.distance_vector[i] < p.distance_vector[i]:
                            cnt += 1
                if cnt > dist:
                    dist = cnt
        p.subvector_dist = dist
