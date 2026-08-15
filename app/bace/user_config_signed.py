import scipy.stats
import numpy as np
import csv
import os

author       = 'Citizens Choice Experiment - v7 Asymmetric'
size_thetas  = 2500
max_opt_time = 5

conf_dict = dict(
    domain_size    = 1500,
    initial_random = 1,
    num_iteration  = 15,
)

answers = [0, 1]   # 0 = chose A, 1 = chose B

# ============================================================================
# WHAT CHANGED vs v6
# ----------------------------------------------------------------------------
# * Moral costs are now split into three asymmetric states:
#   m_c: Moral cost when bill is CORRECT (error == 0)
#   m_o: Moral cost when OVER-charged (error > 0, victim)
#   m_u: Moral cost when UNDER-charged (error < 0, accomplice)
# * Added Recourse Terms:
#   r_o: Non-monetary penalty of an OVER-charged bill under a satellite
#   r_u: Non-monetary penalty of an UNDER-charged bill under a satellite
# ============================================================================

K_MIN = 1.2
K_MAX = 2.5
LIABILITY_BASE = 100.0

# -----------------------------------------------------------------------------
# 1. LOAD PARAMETER RANGES / PRIORS FROM CSV
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

def grid(lo, hi, gran):
    vals = np.arange(lo, hi + gran, gran)
    return [float(v) for v in vals if v <= hi + 1e-9]

ERROR_VALUES = grid(BACE_CONFIG['error']['min'], BACE_CONFIG['error']['max'], BACE_CONFIG['error']['granularity'])
BRIBE_VALUES = grid(BACE_CONFIG['bribe']['min'], BACE_CONFIG['bribe']['max'], BACE_CONFIG['bribe']['granularity'])

# -----------------------------------------------------------------------------
# 2. PRIORS (THETAS) — money is the numeraire (coef -1)
# -----------------------------------------------------------------------------
# Note: Ensure your 'bace_parameters_citizen.csv' is updated to include these new variable names, 
# or hardcode the loc and scale below based on your pilot estimates.
theta_params = dict(
    beta_satellite = scipy.stats.norm(loc=BACE_CONFIG['satellite']['theta_mean'], scale=BACE_CONFIG['satellite']['theta_sd']),
    m_c            = scipy.stats.norm(loc=1, scale=4.0),   # Moral cost, correct
    m_o            = scipy.stats.norm(loc=1, scale=3.0),   # Moral cost, over-charged
    m_u            = scipy.stats.norm(loc=1, scale=3.0),   # Moral cost, under-charged
    r_o            = scipy.stats.norm(loc=-1.0, scale=2.0),   # Recourse penalty, over-charged
    r_u            = scipy.stats.norm(loc=0.0,  scale=1.0),   # Recourse penalty, under-charged (likely ~0)
    mu             = scipy.stats.uniform(loc=1, scale=1.0) # Choice consistency
)

# -----------------------------------------------------------------------------
# 3. DESIGN PARAMETERS
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
# SEED ANCHORS
# ---------------------------------------------------------------------------
SEED_DESIGNS = [
    # (1) beta_satellite: satellite vs CLEAN human, identical correct bill
    dict(assessor_a='Satellite', error_a=0.0, bribe_a=0.0,  k_a=1.6,
         assessor_b='Human',     error_b=0.0, bribe_b=0.0,  k_b=1.6),

    # (2) m_c: same human, correct bill, clean vs bribe
    dict(assessor_a='Human', error_a=0.0, bribe_a=0.0, k_a=2.0,
         assessor_b='Human', error_b=0.0, bribe_b=15.0, k_b=1.8),

    # (3) m_o & r_o: Satellite vs Human, both OVER-charged, Human offers a deal
    dict(assessor_a='Satellite', error_a=15.0, bribe_a=0.0,  k_a=1.5,
         assessor_b='Human',     error_b=15.0, bribe_b=20.0, k_b=2.0),
         
    # (4) m_u & r_u: Satellite vs Human, both UNDER-charged, Human offers a deal
    dict(assessor_a='Satellite', error_a=-10.0, bribe_a=0.0,  k_a=1.5,
         assessor_b='Human',     error_b=-10.0, bribe_b=15.0, k_b=1.5),
]

# -----------------------------------------------------------------------------
# 4. LIKELIHOOD
# -----------------------------------------------------------------------------
def likelihood_pdf(answer, thetas, design, profile=None):
    def get_utility(s):
        is_human    = 1.0 if design[f'assessor_{s}'] == 'Human' else 0.0
        is_sat      = 1.0 - is_human
        bribe_pct   = design[f'bribe_{s}'] * is_human         
        takes_bribe = 1.0 if bribe_pct > 0 else 0.0
        error       = design[f'error_{s}']

        # Define the Signed States
        is_over    = 1.0 if error > 0 else 0.0
        is_under   = 1.0 if error < 0 else 0.0
        is_correct = 1.0 if error == 0 else 0.0

        # Money Out of Pocket
        new_bill    = LIABILITY_BASE + error
        net_cash    = bribe_pct * (1.0 - design[f'k_{s}'])
        money_out   = new_bill + net_cash

        # The Utility Equation
        u  = -1.0 * money_out                                        
        u += thetas['beta_satellite'] * is_sat                       
        
        # The Asymmetric Moral Costs
        u -= thetas['m_c'] * takes_bribe * is_correct                
        u -= thetas['m_o'] * takes_bribe * is_over                   
        u -= thetas['m_u'] * takes_bribe * is_under                  
        
        # The Recourse Terms (Cost of carrying error under a machine)
        u += thetas['r_o'] * is_over * is_sat                        
        u += thetas['r_u'] * is_under * is_sat                       
        
        return u

    diff = get_utility('b') - get_utility('a')
    likelihood = 1.0 / (1.0 + np.exp(-1.0 * thetas['mu'] * diff))
    eps = 1e-10
    likelihood = np.clip(likelihood, eps, 1 - eps)
    
    return likelihood if str(answer) == '1' else 1 - likelihood

