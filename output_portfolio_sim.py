"""""
This .py file is the powerhouse of the program. ALl logic and optimization is conducted in this 
file. This is done per portfolio, and these are called in each simulation.
The simulation stores the output, and there the aggreate information is calculated.

viaCheck is used throughout to ensure that the side efffect is constrainted by its associated
implementation.

In the abscense of the viaCheck, the realized technological maximum
is automatically the annual maximum

"""""



#helper function to be called by both pareto and lexio iterative functions
#Here, the present value of benefits and externalties are calculated
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
    #annua_gt is the annual removals for a method in gigatons, this applies the above 
    #described logic
    if viaCheck:
        annual_gt = min(float(method.maxRemove), float(method.sideEffectMax))
    else:
        annual_gt = float(method.maxRemove)

    if annual_gt <= 0 or actual_contribution <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    #for example, 2.4% is then 0.024
    r = float(SDR) / 100.0
    gt_to_t = 1e9
    net_per_ton = float(SCC) - float(method.mac)
    se = float(getattr(method, "sideEffect", 0.0))

    #climate benefit is the SCC - MAC, variable net_per_ton
    pv_net_climate_benefit = 0.0
    #this is the aggreate externality
    pv_externality = 0.0
    #below decomposes the externality 
    pv_positive_externality = 0.0
    pv_negative_externality = 0.0

    remaining_gt = float(actual_contribution)
    y = 0

    while remaining_gt > 0 and y < duration_years:
        #these are the values specified at the beginning.
        #In all simulations, start year was 2050, and current year was 2025
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

        pv_net_climate_benefit += discounted_climate
        pv_externality += discounted_externality
        #determination if positive or negative, for accounting purposes. 
        #this breakdown presents a better visualization of the externalties involved in
        #implementation.
        if discounted_externality >= 0:
            pv_positive_externality += discounted_externality
        else:
            pv_negative_externality += discounted_externality

        y += 1
    
    pv_total_social_benefit = pv_net_climate_benefit + pv_externality

    return (
        pv_net_climate_benefit,
        pv_externality,
        pv_total_social_benefit,
        pv_positive_externality,
        pv_negative_externality,
    )

#this replicates equation 37 from the thesis. 
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


#this function does the cost minimization
#done one method as a time and builds then the implemented portfolio.
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
    #geological storage counter, makes sure the limit is not transgressed.
    # in the data generation, the storage requirment is assigned based on method type

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
    #1e-9 is used for floating point error, done the same in Pareto Optimization
    #the main loop, where methods are appendend 
    while remaining_methods and installed_capacity < float(storage_target) - 1e-9 and iterations < max_iterations:        
        iterations += 1
        lg_candidate = None

        for m in remaining_methods:
            dominated = False
            for other in remaining_methods:
                if other is m:
                    continue
                #core check. prioritizes that need for a lower MAC, and sideEffect is secondary
                if other.mac < m.mac:
                    dominated = True
                    break
            if not dominated:
                lg_candidate = m
                break

        if lg_candidate is None:
            if verbose:
                print("No cost minimal method found. Stopping.")
            break
         #same logic for setting of the annual_gt, this 
         # would have been more effective as a helper function, but
         # that will be reflected in a further update   
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
        #here is the storage constraint check.
        if lg_candidate.storageType == "geological formations":
            remaining_sp = float(sp) - float(geo_store_counter)
            if remaining_sp <= 0:
                remaining_methods.remove(lg_candidate)
                continue
            actual_contribution = min(actual_contribution, remaining_sp)

        remaining_capacity = float(storage_target) - float(installed_capacity)
        if remaining_capacity <= 0:
            break
        #makes sure that the removal target is not exceeded
        actual_contribution = min(actual_contribution, remaining_capacity)

        (
            pv_net_climate_benefit,
            pv_externality,
            pv_total_social_benefit,
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
        #allows for partial implementation and marks it as so. 
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
            "pv_net_climate_benefit": pv_net_climate_benefit,
            "pv_externality": pv_externality,
            "pv_total_social_benefit": pv_total_social_benefit,
            "pv_positive_externality": pv_positive_externality,
            "pv_negative_externality": pv_negative_externality,
        })

        remaining_methods.remove(lg_candidate)

    return lg_methods

#similar to above, but with Pareto optimization 
#comments provided in areas where the logic is different than above. 
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
    verbose=False,
):
    #also the storage constraint 
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

    #1e-9 is the flotating point check
    while remaining and installed < float(storage_target) - 1e-9 and round_idx < max_rounds:
        round_idx += 1
        front = _pareto_front(remaining)
        remaining_target = float(storage_target) - float(installed)
        #this sorts the layer from least cost to high cost, relevant in the scenario when the entire layer
        #cannot be implemented
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
                pv_net_climate_benefit,
                pv_externality,
                pv_total_social_benefit,
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
                "pv_net_climate_benefit": pv_net_climate_benefit,
                "pv_externality": pv_externality,
                "pv_total_social_benefit": pv_total_social_benefit,
                "pv_positive_externality": pv_positive_externality,
                "pv_negative_externality": pv_negative_externality,
            })

            if m in remaining:
                remaining.remove(m)

            if installed >= storage_target:
                print("Storage target met.")
                break

    return portfolio