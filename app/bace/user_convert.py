from datetime import datetime, timezone

TOTAL_LIABILITY = 100000   # Correct yearly liability (PKR). Fixed for now.
PCT_GRAN  = 5
# Fallback only. The real exchange rate VARIES per option and arrives in the
# design as k_a / k_b (uniform 1.2-2 in user_config.py). Used only if k is
# missing from the design dict.
K_DEFAULT = 1.2

# Nearest rupee amount to round DISPLAYED bribe/final-recorded figures to.
# Display only -- the model always uses the exact continuous bribe/k values.
DISPLAY_ROUND = 100

ASSESSOR_LABEL = {
    'Human':     'An inspector visits & measures',
    'Satellite': 'A satellite checks automatically',
}

def add_to_profile(profile):
    profile['timestamp'] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return profile

def round_to_granularity(value, granularity):
    return float(granularity * round(float(value) / granularity))


def round_rupees(value, nearest=DISPLAY_ROUND):
    """DISPLAY-ONLY rounding to the nearest `nearest` rupees (default Rs 100).
    Never feed this back into the design/likelihood -- estimation always uses
    the exact continuous bribe/k values computed upstream."""
    return float(nearest * round(float(value) / nearest))


# 8-row layout (was 9): the accuracy row is removed. accuracy + measurement_error
# are now a SINGLE signed `error`, shown via the "mistake" + "bill after" rows.
# A positive error is presented as an over-assessment the respondent can SEE is a
# mistake -- that framing is what makes a bribe look corrective (m1) at high error
# and pure cheating (m0) at zero error. Assessor is shown in the header.
def choice_message(label, error, bribe, assessor, profile_liability, k=K_DEFAULT):
    try:
        L = float(profile_liability)
        k = float(k)
        assessor = str(assessor)
        is_sat = (assessor == 'Satellite')

        e = round_to_granularity(error, PCT_GRAN)
        err_amt_exact  = L * abs(e) / 100.0

        # DISPLAY ONLY: round liability + mistake amount to Rs 100, then DERIVE
        # "bill after the mistake" by adding the already-rounded pieces (rather
        # than rounding it separately) so the three numbers always add up
        # exactly as printed, whatever the exact liability value is.
        L_disp   = round_rupees(L)
        err_amt  = round_rupees(err_amt_exact)
        sign     = 1.0 if e > 0 else (-1.0 if e < 0 else 0.0)
        bill_after = L_disp + sign * err_amt

        if e < 0:
            mistake_disp = f"\u2212Rs {err_amt:,.0f} recorded too LOW (by mistake)"
        elif e > 0:
            mistake_disp = f"+Rs {err_amt:,.0f} recorded too HIGH (by mistake)"
        else:
            mistake_disp = "Correct amount (no mistake)"

        if is_sat:
            deal_disp      = "No deal \u2014 no one to bargain with"
            informal_disp  = "Rs 0"
            final_recorded = bill_after
            leaves_html    = f"Rs {bill_after:,.0f}"
        else:
            z = round_to_granularity(bribe, PCT_GRAN)
            bribe_amt_exact       = L * z / 100.0
            reduction_amt         = k * bribe_amt_exact
            # Reduction is applied to the DISPLAYED (rounded) bill-after, so
            # the "...instead of Rs X" text always matches the row above it.
            final_recorded_exact  = bill_after - reduction_amt

            # DISPLAY ONLY: round the bribe and the resulting reduced/final
            # bill to the nearest Rs 100. Computed from the exact values above
            # so the model (which uses bribe/k directly) is untouched.
            bribe_amt      = round_rupees(bribe_amt_exact)
            final_recorded = round_rupees(final_recorded_exact)

            if bribe_amt > 0:
                deal_disp = (f"&ldquo;Pay Rs {bribe_amt:,.0f} and I&rsquo;ll record "
                             f"Rs {final_recorded:,.0f} instead of Rs {bill_after:,.0f}.&rdquo;")
                informal_disp = f"Rs {bribe_amt:,.0f}"
                # Sum the ROUNDED components so the printed total matches the
                # printed addends exactly (no "18,800 + 1,200 != 20,000").
                leaves_html = (f"<span class='pocket-breakdown'>Rs {final_recorded:,.0f} + Rs {bribe_amt:,.0f}</span>"
                               f"<br>Rs {final_recorded + bribe_amt:,.0f}")
            else:
                deal_disp = "No payment offered"
                informal_disp = "Rs 0"
                leaves_html = f"Rs {bill_after:,.0f}"

    except Exception as ex:
        print(f"DEBUG: choice_message failed: {ex}")
        mistake_disp = deal_disp = informal_disp = "\u2014"
        L_disp = TOTAL_LIABILITY; bill_after = final_recorded = TOTAL_LIABILITY
        leaves_html = f"Rs {TOTAL_LIABILITY:,.0f}"
        assessor = ""

    assessor_desc = ASSESSOR_LABEL.get(assessor, assessor)

    html_table = f"""
        <table width='100%' class="bace_table">
            <tbody>
                <tr><th colspan="2">{label} \u2014 {assessor_desc}</th></tr>
                <tr><td>Your real bill</td><td>Rs {L_disp:,.0f}</td></tr>
                <tr><td>Measuring mistake (this time)</td><td>{mistake_disp}</td></tr>
                <tr><td>Bill after the mistake</td><td>Rs {bill_after:,.0f}</td></tr>
                <tr><td>The deal (chai-pani)</td><td>{deal_disp}</td></tr>
                <tr><td>Informal payment</td><td>{informal_disp}</td></tr>
                <tr><td>Final recorded bill</td><td>Rs {final_recorded:,.0f}</td></tr>
                <tr><td>What actually leaves your pocket</td><td>{leaves_html}</td></tr>
            </tbody>
        </table>
    """
    return html_table


def convert_design(design, profile, request_data):
    print(f"DEBUG: design dictionary content: {design}")
    Q = request_data.get('question_number') or len(profile.get('design_history'))
    profile_liability = profile.get('initial_liability', TOTAL_LIABILITY)
    output_design = {f'{key}_{Q}': value for key, value in design.items()}

    output_design[f'message_0_{Q}'] = choice_message(
        "Option A",
        design.get('error_a', 0),
        design.get('bribe_a', 0), design.get('assessor_a', 'Human'), profile_liability,
        design.get('k_a', K_DEFAULT))
    output_design[f'message_1_{Q}'] = choice_message(
        "Option B",
        design.get('error_b', 0),
        design.get('bribe_b', 0), design.get('assessor_b', 'Human'), profile_liability,
        design.get('k_b', K_DEFAULT))
    return output_design