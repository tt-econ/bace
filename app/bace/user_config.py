import scipy.stats
import numpy as np
import csv
import os

author       = 'Citizens Choice Experiment'
size_thetas  = 2500
max_opt_time = 5

conf_dict = dict(
    domain_size    = 1500,
    initial_random = 1,
    num_iteration  = 15,
)

answers = [0, 1]   # 0 = chose A, 1 = chose B

# ============================================================================
# WHAT CHANGED vs the previous config
# ----------------------------------------------------------------------------
# * accuracy + measurement_error are COLLAPSED into ONE design attribute: a
#   signed `error` (% of liability). It moves the displayed bill (money), and
#   the OVER-assessment part of it is what makes a bribe look corrective. One
#   variable, one consequence, no inert "score", no collinear twin.
# * `beta_accuracy` is dropped. "Do citizens value accuracy?" is now answered
#   honestly: disliking inaccuracy = disliking being over-assessed, which the
#   money term (-1 numeraire) already prices, plus `beta_satellite` (taste for
#   the accurate machine over the human).
# * flat `m` is replaced by `m0` + `m1`:
#       moral cost of bribing = m0 - m1 * (share you were OVER-assessed)
#   m0 = cost of bribing when the bill was FAIR (pure cheating; real morality)
#   m1 = how much each unit of over-assessment ERODES that ("I'm owed it")
#   low m0 -> rent-seeker | high m0 + high m1 -> corrector | high m0, low m1 -> rigidly honest
# * loader keys off a `variable` NAME column (robust), not row index.
# ============================================================================

# Bill reduction = K x bribe; K > 1 makes every deal cash-positive, so refusing
# reveals morality, not arithmetic. K varies per option (continuous) to sweep the
# net saving finely across each respondent's accept/refuse threshold. K is shown
# via the on-screen deal numbers, enters utility ONLY through the -1 money term,
# and is NOT estimated -> it cannot confound m0/m1 or beta_satellite.
K_MIN = 1.2
K_MAX = 2.5

# Respondent's own current bill, shown as a constant anchor on every screen.
# It is identical across options A and B, so it CANCELS in the A-vs-B utility
# difference and does not affect estimation; kept only so "money out of pocket"
# reads as a realistic on-screen total. Money variation comes entirely from
# `error` (the new bill) and the bribe deal.
LIABILITY_BASE = 100.0

# -----------------------------------------------------------------------------
# 1. LOAD PARAMETER RANGES / PRIORS FROM CSV  (keyed by `variable` name)
# -----------------------------------------------------------------------------
def load_bace_parameters(filename='bace_parameters_citizen.csv'):
    params = {}
    try:
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('Population') != 'citizen':
                    continue
                params[row['variable']] = {
                    'min':        float(row['range_min']),
                    'max':        float(row['range_max']),
                    'mean':       float(row['range_mean']),
                    'theta_mean': float(row['theta_mean']),
                    'theta_sd':   float(row['theta_sd']),
                    'granularity':float(row['granularity']),
                }
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None
    return params

BACE_CONFIG = load_bace_parameters()
if BACE_CONFIG is None:
    raise ValueError("Could not load 'bace_parameters_citizen.csv'. Keep it in the same folder.")

ERROR_MAX = BACE_CONFIG['error']['max']   # used to normalise the over-assessment share to [0,1]

# Discrete grids (round numbers on screen). K stays continuous.
def grid(lo, hi, gran):
    vals = np.arange(lo, hi + gran, gran)
    return [float(v) for v in vals if v <= hi + 1e-9]

ERROR_VALUES = grid(BACE_CONFIG['error']['min'], BACE_CONFIG['error']['max'], BACE_CONFIG['error']['granularity'])
BRIBE_VALUES = grid(BACE_CONFIG['bribe']['min'], BACE_CONFIG['bribe']['max'], BACE_CONFIG['bribe']['granularity'])  # includes 0




# -----------------------------------------------------------------------------
# 2. PRIORS (THETAS)  — money is the numeraire (coef -1); all in % of liability
#      beta_satellite : intrinsic taste for satellite vs human (>0 = prefers satellite)
#      m0             : moral cost of bribing when the bill is FAIR (sign free)
#      m1             : erosion of that cost at FULL over-assessment (sign free; +>0 expected)
#      mu             : logit choice-consistency scale
# -----------------------------------------------------------------------------
theta_params = dict(
    beta_satellite = scipy.stats.norm(loc=BACE_CONFIG['satellite']['theta_mean'], scale=BACE_CONFIG['satellite']['theta_sd']),
    m0             = scipy.stats.norm(loc=BACE_CONFIG['m0']['theta_mean'],        scale=BACE_CONFIG['m0']['theta_sd']),
    m1             = scipy.stats.norm(loc=BACE_CONFIG['m1']['theta_mean'],        scale=BACE_CONFIG['m1']['theta_sd']),
    mu             = scipy.stats.uniform(loc=0.65, scale=1),   # [0.05, 2.0]; tuned to %-of-liability utils
)

# -----------------------------------------------------------------------------
# 3. DESIGN PARAMETERS
#      error : signed assessment error (% of liability). + = OVER-assessed.
#              Drawn INDEPENDENTLY of the bribe (orthogonal) -> no collinearity.
#      bribe : % of liability, discrete grid INCLUDING 0 (clean inspector).
#              The 0 cell is what isolates m0/m1 from beta_satellite:
#                Human-clean vs Human-corrupt -> moral params (satellite cancels)
#                Satellite   vs Human-clean   -> beta_satellite (no bribe present)
#      k     : exchange rate, continuous; matters only on Human+bribe options.
# -----------------------------------------------------------------------------
design_params = dict(
    error_a    = list(ERROR_VALUES),
    error_b    = list(ERROR_VALUES),
    bribe_a    = list(BRIBE_VALUES),
    bribe_b    = list(BRIBE_VALUES),
    k_a        = scipy.stats.uniform(K_MIN, K_MAX - K_MIN),
    k_b        = scipy.stats.uniform(K_MIN, K_MAX - K_MIN),
    assessor_a = ['Human', 'Satellite'],
    assessor_b = ['Human', 'Satellite'],
)


# ---------------------------------------------------------------------------
# SEED ANCHORS — served as the first 3 questions, before adaptive BACE.
# Each cancels two of the three structural terms in the A-vs-B difference,
# leaving exactly one parameter. Verified: P(B) moves only with the target.
# (Isolation is exact algebra — it does NOT depend on the bribe/K magnitudes,
#  only on the structure — so you can retune the money numbers freely.)
# ---------------------------------------------------------------------------
SEED_DESIGNS = [

    # (1) beta_satellite: satellite vs CLEAN human, identical correct bill, no
    #     bribe either side. Money cancels (both Rs 20,000), no moral term.
    #     "Both report your correct bill. One's a satellite, one's an inspector.
    #      Same Rs 20,000 out of pocket. Which do you prefer?"
    dict(assessor_a='Satellite', error_a=0.0, bribe_a=0.0,  k_a=1.6,
         assessor_b='Human',     error_b=0.0, bribe_b=0.0,  k_b=1.6),

    # (2) m0: same human, FAIR bill (so m1 is inert), clean vs a bribe whose
    #     NET saving (=bribe*(K-1)) sits at the m0 prior centre (~3% of liability
    #     = Rs 600) for maximum information. bribe 5% (Rs 1,000), K=1.6.
    #     "Correct Rs 20,000 bill. Pay it, or pay Rs 1,000 chai-pani, bill
    #      recorded at Rs 18,400 -> Rs 19,400 out of pocket (saves Rs 600)."
    dict(assessor_a='Human', error_a=0.0, bribe_a=0.0, k_a=2,
         assessor_b='Human', error_b=0.0, bribe_b=15.0, k_b=1.8),

    # (3) m1 (slope): two human BRIBE options, money held EQUAL, differing only
    #     in over-assessment (over_share 0 vs 1). beta cancels (both human),
    #     m0 cancels (both bribe). Only the "I'm owed it" erosion survives.
    #     A: correct bill, bribe 10% (Rs 2,000), K=1.5 -> Rs 19,000 out of pocket
    #     B: over-assessed 15% (Rs 24,000), bribe 20% (Rs 5,000), K=2.0 -> Rs 19,000
    dict(assessor_a='Human', error_a=0.0,  bribe_a=10.0, k_a=1.5,
         assessor_b='Human', error_b=15.0, bribe_b=20.0, k_b=2.0),

    # (4) m1 (slope, same-bribe variant): identical logic to (3) -- two human
    #     bribe options, money held EQUAL, only over-assessment differs -- but
    #     here the BRIBE ITSELF is held equal (25%) across options, and the
    #     trade-off instead comes from a bigger K (bigger bill-reduction per
    #     rupee bribed) on the over-assessed side. A second, independent read
    #     on the m1 slope via a different design mechanism than anchor (3).
    #     NOTE: PI's original rupee example (Rs1,000 bribe, 20% over-assessment
    #     to match pockets) needs K=6.0, far outside K_MIN/K_MAX=[1.2,2.0], and
    #     20% error also exceeds the current ERROR_MAX=15. Rescaled to the
    #     largest bribe on-grid (25%) so the required K-gap (0.6) fits inside
    #     the model's available K spread (0.8). Verified: P(B) moves only with
    #     m1, flat in beta_satellite and m0.
    #     A: correct bill, bribe 25% (Rs 5,000), K=1.3 -> Rs 18,500 out of pocket
    #     B: over-assessed 15% (Rs 23,000), bribe 25% (Rs 5,000, SAME), K=1.9 -> Rs 18,500
    dict(assessor_a='Human', error_a=0.0,  bribe_a=15.0, k_a=1.333,
         assessor_b='Human', error_b=10.0, bribe_b=15.0, k_b=2),
]


# -----------------------------------------------------------------------------
# 4. LIKELIHOOD
#      U = -(money out of pocket)              # numeraire, coef fixed at -1
#          + beta_satellite * 1{satellite}
#          - moral_cost     * 1{this option used a bribe}
#      moral_cost = m0 - m1 * over_share,  over_share = max(0, error)/ERROR_MAX in [0,1]
# -----------------------------------------------------------------------------
def likelihood_pdf(answer, thetas, design, profile=None):
    def get_utility(s):
        is_human    = 1.0 if design[f'assessor_{s}'] == 'Human' else 0.0
        bribe_pct   = design[f'bribe_{s}'] * is_human         # 0 under Satellite
        takes_bribe = 1.0 if bribe_pct > 0 else 0.0
        error       = design[f'error_{s}']

        # Money: new bill = anchor + error; bribe deal nets (1-K)*bribe (negative = pay less)
        new_bill    = LIABILITY_BASE + error
        net_cash    = bribe_pct * (1.0 - design[f'k_{s}'])
        money_out   = new_bill + net_cash

        # Moral excuse only from OVER-assessment; under-assessment gives no cover (keeps full m0)
        over_share  = max(0.0, error) / ERROR_MAX
        moral_cost  = thetas['m0'] - thetas['m1'] * over_share

        u  = -1.0 * money_out                                # MONEY NUMERAIRE
        u += thetas['beta_satellite'] * (1.0 - is_human)     # 1 for Satellite, 0 for Human
        u -= moral_cost * takes_bribe                        # subtract: bigger m0/m1 = more averse = more moral
        return u

    diff = get_utility('b') - get_utility('a')
    likelihood = 1.0 / (1.0 + np.exp(-1.0 * thetas['mu'] * diff))
    eps = 1e-10
    likelihood = np.clip(likelihood, eps, 1 - eps)
    return likelihood if str(answer) == '1' else 1 - likelihood

# OPTIONAL: if you want a "bothered by a wrong bill BEYOND the rupees" (procedural
# fairness) term, add e.g.  u -= thetas['gamma'] * over_share  OUTSIDE takes_bribe.
# Check first whether plain money aversion already covers it, or it fights the numeraire.