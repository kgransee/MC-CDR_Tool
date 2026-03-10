
#helper function to be called by both pareto and lexio iterative functions
def _compute_pv_net(
    viaCheck,
    method,
    actual_contribution,
    SDR,
    SCC,
    start_year,
    current_year,
    duration_years,
):
    if viaCheck:
        annual_gt = min(float(method.maxRemove), float(method.sideEffectMax))
    else:
        annual_gt = float(method.maxRemove)

    if annual_gt <= 0 or actual_contribution <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    r = float(SDR) / 100.0
    gt_to_t = 1e9
    net_per_ton = float(SCC) - float(method.mac)
    se = float(getattr(method, "sideEffect", 0.0))

    pv_climate_benefit = 0.0
    pv_externality = 0.0
    pv_positive_externality = 0.0
    pv_negative_externality = 0.0

    remaining_gt = float(actual_contribution)
    y = 0

    while remaining_gt > 0 and y < duration_years:
        year = start_year + y
        t = year - current_year

        if t < 0:
            y += 1
            continue

        implemented_gt = min(annual_gt, remaining_gt)
        remaining_gt -= implemented_gt

        tons = implemented_gt * gt_to_t
        annual_climate_benefit = tons * net_per_ton
        annual_externality = annual_climate_benefit * se

        discount_factor = (1 + r) ** t

        discounted_climate = annual_climate_benefit / discount_factor
        discounted_externality = annual_externality / discount_factor

        pv_climate_benefit += discounted_climate
        pv_externality += discounted_externality

        if discounted_externality >= 0:
            pv_positive_externality += discounted_externality
        else:
            pv_negative_externality += discounted_externality

        y += 1

    pv_social_net_benefit = pv_climate_benefit + pv_externality

    return (
        pv_climate_benefit,
        pv_externality,
        pv_social_net_benefit,
        pv_positive_externality,
        pv_negative_externality,
    )


def _pareto_front(methods):
    front = []

    for m in methods:
        dominated = False

        for o in methods:
            if o is m:
                continue

            if (
                o.mac <= m.mac and
                o.sideEffect >= m.sideEffect and
                (o.mac < m.mac or o.sideEffect > m.sideEffect)
            ):
                dominated = True
                break

        if not dominated:
            front.append(m)

    return front

#helper function, called here within to sort the Pareto layer by MAC from least to highest
def _allocate_by_increasing_mac(viaCheck, front_methods, remaining_target, duration_years, sp, geo_used):
    """
    Sort current Pareto front by MAC and allocate capacity in that order.
    """
    remaining_target = float(remaining_target)
    sorted_front = sorted(front_methods, key=lambda m: float(m.mac))

    allocations = [0.0] * len(sorted_front)

    for i, m in enumerate(sorted_front):
        if remaining_target <= 0:
            break

        if viaCheck:
            annual_gt = min(float(m.maxRemove), float(m.sideEffectMax))
        else:
            annual_gt = float(m.maxRemove)
        
        cap = annual_gt * float(duration_years)

        if getattr(m, "storageType", None) == "geological formations":
            cap = min(cap, max(0.0, float(sp) - float(geo_used)))

        cap = max(0.0, cap)
        if cap <= 0:
            continue

        take = min(cap, remaining_target)
        allocations[i] = take
        remaining_target -= take

        if getattr(m, "storageType", None) == "geological formations":
            geo_used += take

    return sorted_front, allocations, geo_used

def lexicographic_opt_iterative(
    viaCheck,
    SDR,
    SCC,
    start_year,
    current_year,
    viable_methods,
    storage_target,
    duration_years,
    pass_storage_potential,
    max_iterations=1000,
    verbose=False,
):
    sp = float(pass_storage_potential)
    geo_store_counter = 0.0
    partial = None

    if not viable_methods:
        if verbose:
            print("No viable methods provided.")
        return []

    remaining_methods = viable_methods.copy()
    lg_methods = []
    installed_capacity = 0.0
    iterations = 0

    while remaining_methods and installed_capacity < float(storage_target) - 1e-9 and iterations < max_iterations:        
        iterations += 1
        lg_candidate = None

        for m in remaining_methods:
            dominated = False
            for other in remaining_methods:
                if other is m:
                    continue
                if other.mac < m.mac or (other.mac == m.mac and other.sideEffect > m.sideEffect):
                    dominated = True
                    break
            if not dominated:
                lg_candidate = m
                break

        if lg_candidate is None:
            if verbose:
                print("No lexicographic-dominant method found. Stopping.")
            break

        if viaCheck:
            annual_gt = min(float(lg_candidate.maxRemove), float(lg_candidate.sideEffectMax))
        else:
            annual_gt = float(lg_candidate.maxRemove)
        if annual_gt <= 0:
            remaining_methods.remove(lg_candidate)
            continue

        contribution = annual_gt * float(duration_years)
        actual_contribution = contribution
        partial = False

        if lg_candidate.storageType == "geological formations":
            remaining_sp = float(sp) - float(geo_store_counter)
            if remaining_sp <= 0:
                remaining_methods.remove(lg_candidate)
                continue
            actual_contribution = min(actual_contribution, remaining_sp)

        remaining_capacity = float(storage_target) - float(installed_capacity)
        if remaining_capacity <= 0:
            break

        actual_contribution = min(actual_contribution, remaining_capacity)

        (
            pv_climate_benefit,
            pv_externality,
            pv_social_net_benefit,
            pv_positive_externality,
            pv_negative_externality,
        ) = _compute_pv_net(
        viaCheck=viaCheck,
        method=lg_candidate,
        actual_contribution=actual_contribution,
        SDR=SDR,
        SCC=SCC,
        start_year=start_year,
        current_year=current_year,
        duration_years=duration_years,
    )

        if actual_contribution < contribution:
            partial = True

        installed_capacity = min(float(storage_target), installed_capacity + actual_contribution)

        if lg_candidate.storageType == "geological formations":
            geo_store_counter += actual_contribution

        lg_methods.append({
            "method": lg_candidate,
            "actual_contribution": actual_contribution,
            "mac": float(lg_candidate.mac),
            "partial": partial,
            "pv_climate_benefit": pv_climate_benefit,
            "pv_externality": pv_externality,
            "pv_social_net_benefit": pv_social_net_benefit,
            "pv_positive_externality": pv_positive_externality,
            "pv_negative_externality": pv_negative_externality,
        })

        remaining_methods.remove(lg_candidate)

    return lg_methods


def pareto_portfolio_iterative_layers(
    viaCheck,
    SDR,
    SCC,
    start_year,
    current_year,
    viable_methods,
    storage_target,
    duration_years,
    pass_storage_potential,
    max_rounds=10_000,
    plot=False,   # kept only for compatibility with existing calls
    plot_rounds_limit=8,  # kept only for compatibility
    verbose=False,
):
    sp = float(pass_storage_potential)
    geo_used = 0.0

    if not viable_methods:
        if verbose:
            print("No viable methods provided.")
        return []

    remaining = viable_methods.copy()
    portfolio = []
    installed = 0.0
    round_idx = 0

    while remaining and installed < float(storage_target) - 1e-9 and round_idx < max_rounds:
        round_idx += 1
        front = _pareto_front(remaining)
        remaining_target = float(storage_target) - float(installed)

        sorted_front, allocs, geo_used = _allocate_by_increasing_mac(
            viaCheck=viaCheck,
            front_methods=front,
            remaining_target=remaining_target,
            duration_years=duration_years,
            sp=sp,
            geo_used=geo_used,
        )

        for idx, m in enumerate(sorted_front):
            actual = max(0.0, float(allocs[idx]))

            remaining_capacity = max(0.0, float(storage_target) - float(installed))
            actual = min(actual, remaining_capacity)

            if actual == 0.0:
                continue

            installed = min(float(storage_target), installed + actual)
            if viaCheck:
                contribution =min(float(m.maxRemove), float(m.sideEffectMax)) * float(duration_years)
            else:
                contribution = float(m.maxRemove) * float(duration_years)
            partial = actual < contribution or installed >= storage_target

            (
                pv_climate_benefit,
                pv_externality,
                pv_social_net_benefit,
                pv_positive_externality,
                pv_negative_externality,
            ) = _compute_pv_net(
            viaCheck=viaCheck,
            method=m,
            actual_contribution=actual,
            SDR=SDR,
            SCC=SCC,
            start_year=start_year,
            current_year=current_year,
            duration_years=duration_years,
        )

            portfolio.append({
                "method": m,
                "actual_contribution": actual,
                "mac": float(m.mac),
                "partial": partial,
                "round": round_idx,
                "pv_climate_benefit": pv_climate_benefit,
                "pv_externality": pv_externality,
                "pv_social_net_benefit": pv_social_net_benefit,
                "pv_positive_externality": pv_positive_externality,
                "pv_negative_externality": pv_negative_externality,
            })

            if m in remaining:
                remaining.remove(m)

            if installed >= storage_target:
                print("Storage target met.")
                break

    return portfolio