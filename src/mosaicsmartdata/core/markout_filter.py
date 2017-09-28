def filter_markouts(mkmsg, bps_tol = 3.0):
    if mkmsg.nonpaper_legs_count > 1:
        # filter on factor_bps_markout
        if abs(mkmsg.factor_bps_markout) > bps_tol:
            return True
    else:
        # multi_leg- assume delta_neutral
        if abs(mkmsg.bps_markout) > bps_tol:
            return True

    return False
