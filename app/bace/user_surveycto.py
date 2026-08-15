import re

# --- CONSTANTS ---
TOTAL_LIABILITY = 100000   # Default liability (PKR)
PCT_GRAN  = 5
# Fallback only. The real exchange rate VARIES per option and arrives in the
# design as k_a / k_b (uniform 1.2-2 in user_config.py). Used only if k is
# missing from the design dict.
K_DEFAULT = 1.2

# Nearest rupee amount to round DISPLAYED bribe/final-recorded figures to.
# Display only -- the model always uses the exact continuous bribe/k values.
DISPLAY_ROUND = 100

# NOTE: values must NOT contain ':' or '|' (the SurveyCTO delimiters).
# The final "leaves your pocket" cell may carry a two-line breakdown using the
# marker '~~' : "<breakdown>~~<total>". script.js splits on '~~'.
# ROW COUNT CHANGED: 8 rows now (was 9) -- the "Gets the size right for" row is
# gone. Update the SurveyCTO field / script.js row parser to expect 8 rows.


def round_to_granularity(value, granularity):
    return float(granularity * round(float(value) / granularity))


def round_rupees(value, nearest=DISPLAY_ROUND):
    """DISPLAY-ONLY rounding to the nearest `nearest` rupees (default Rs 100).
    Never feed this back into the design/likelihood -- estimation always uses
    the exact continuous bribe/k values computed upstream."""
    return float(nearest * round(float(value) / nearest))


def convert_design_surveycto(design, profile, request_data, split_to_rows="|", split_to_vars=":"):
    output = ""

    # --- 1. EXTRACT RAW INPUTS ---
    try:
        err_a = float(design.get('error_a', 0))   # signed %; replaces accuracy + measurement_error
        err_b = float(design.get('error_b', 0))
        bribe_a = float(design.get('bribe_a', 0))
        bribe_b = float(design.get('bribe_b', 0))
        assessor_a = str(design.get('assessor_a', 'Human'))
        assessor_b = str(design.get('assessor_b', 'Human'))
        k_a = float(design.get('k_a', K_DEFAULT))             # per-option exchange rate
        k_b = float(design.get('k_b', K_DEFAULT))
    except Exception as e:
        print(f"Error parsing design: {e}")
        return {'output': "Error"}

    liability = TOTAL_LIABILITY
    try:
        if profile:
            liability = float(profile.get('initial_liability', TOTAL_LIABILITY))
    except Exception:
        liability = TOTAL_LIABILITY

    # --- 2. PER-OPTION DISPLAY VALUES (8-row layout; accuracy row removed) ---
    def option_display(error, bribe, assessor, k):
        L = liability
        is_sat = (assessor == 'Satellite')

        e = round_to_granularity(error, PCT_GRAN)
        err_amt_exact = L * abs(e) / 100.0

        # DISPLAY ONLY: round liability + mistake amount to Rs 100, then DERIVE
        # "bill after the mistake" by adding the already-rounded pieces (rather
        # than rounding it separately) so the three numbers always add up
        # exactly as printed, whatever the exact liability value is.
        L_disp  = round_rupees(L)
        err_amt = round_rupees(err_amt_exact)
        sign    = 1.0 if e > 0 else (-1.0 if e < 0 else 0.0)
        bill_after = L_disp + sign * err_amt

        if e < 0:
            mistake_disp = f"- Rs {err_amt:,.0f} recorded too LOW (by mistake)"
        elif e > 0:
            mistake_disp = f"+ Rs {err_amt:,.0f} recorded too HIGH (by mistake)"
        else:
            mistake_disp = "Correct amount (no mistake)"

        if is_sat:
            deal_disp      = "No deal, no one to bargain with"
            informal_disp  = "Rs 0"
            final_recorded = bill_after
            leaves_total   = bill_after
            leaves_breakdown = ""
        else:
            z = round_to_granularity(bribe, PCT_GRAN)
            bribe_amt_exact      = L * z / 100.0
            reduction_amt        = k * bribe_amt_exact
            # Reduction is applied to the DISPLAYED (rounded) bill-after, so
            # the "...instead of Rs X" text always matches the row above it.
            final_recorded_exact = bill_after - reduction_amt

            # DISPLAY ONLY: round the bribe and the resulting reduced/final
            # bill to the nearest Rs 100. Computed from the exact values above
            # so the model (which uses bribe/k directly) is untouched.
            bribe_amt      = round_rupees(bribe_amt_exact)
            final_recorded = round_rupees(final_recorded_exact)

            if bribe_amt > 0:
                deal_disp = (f"Pay Rs {bribe_amt:,.0f} and the inspector records "
                             f"Rs {final_recorded:,.0f} instead of Rs {bill_after:,.0f}")
                informal_disp = f"Rs {bribe_amt:,.0f}"
                # Sum the ROUNDED components so the printed total matches the
                # printed addends exactly (no "18,800 + 1,200 != 20,000").
                leaves_breakdown = f"Rs {final_recorded:,.0f} + Rs {bribe_amt:,.0f}"
            else:
                deal_disp = "No payment offered"
                informal_disp = "Rs 0"
                leaves_breakdown = ""
            leaves_total = final_recorded + bribe_amt

        if leaves_breakdown:
            leaves_field = f"{leaves_breakdown}~~Rs {leaves_total:,.0f}"
        else:
            leaves_field = f"Rs {leaves_total:,.0f}"

        assessor_disp = "A satellite checks automatically" if is_sat else "An inspector visits & measures"

        return {
            'assessor':       assessor_disp,
            'real_bill':      f"Rs {L_disp:,.0f}",
            'mistake':        mistake_disp,
            'bill_after':     f"Rs {bill_after:,.0f}",
            'deal':           deal_disp,
            'informal':       informal_disp,
            'final_recorded': f"Rs {final_recorded:,.0f}",
            'leaves':         leaves_field,
        }

    A = option_display(err_a, bribe_a, assessor_a, k_a)
    B = option_display(err_b, bribe_b, assessor_b, k_b)

    # --- 3. BUILD OUTPUT STRING (label : optionA : optionB |) ---
    def row(label, key):
        return f"{label}{split_to_vars}{A[key]}{split_to_vars}{B[key]}{split_to_rows}"

    output += row("Your real bill", 'real_bill')
    output += row("Who checks your house", 'assessor')
    output += row("Measuring mistake (this time)", 'mistake')
    output += row("Bill after the mistake", 'bill_after')
    output += row("The deal (chai-pani)", 'deal')
    output += row("Informal payment", 'informal')
    output += row("Final recorded bill", 'final_recorded')
    output += row("What actually leaves your pocket", 'leaves')

    print(output)
    return {'output': output}


def convert_dict_to_string(obj, parent_key='', split_to_rows='|', split_to_vars=':'):
    output = []
    for key, val in obj.items():
        new_key = f"{parent_key}_{key}" if parent_key else key
        if isinstance(val, dict):
            nested_output = convert_dict_to_string(val, new_key, split_to_rows, split_to_vars)
            output.append(nested_output)
        else:
            output.append(f"{new_key}{split_to_vars}{val}")
    return split_to_rows.join(output)