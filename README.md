# Citizen Property-Tax BACE Survey

A Bayesian Adaptive Choice Experiment (BACE) implementation designed to elicit
citizens' preferences over automated (satellite) vs. human inspector property tax
assessment, and their willingness to bribe an assessor to lower their tax bill. This includes whether
the willingness to bribe increases when the bill is wrongly assessed as too high.

Built on top of the [BACE framework](<https://github.com/tt-econ/bace>) developed by
Drake, Payró, Thakral & Tô (2025), *"Bayesian Adaptive Choice Experiments"*.
The underlying adaptive-design engine is the authors', and this repo documents the survey design,
utility model, and identification work built on top of it for a specific
applied research question.

<img width="722" height="734" alt="reference" src="https://github.com/user-attachments/assets/b92c2345-795e-4b3d-b232-333bdb72029c" />

An example screen of the Conjoint Survey Experiment


## What I designed and implemented

**Utility model.** Implemented an adaptive conjoint choice model over property tax assessments, where each option is defined by who
assesses the property (human inspector vs. satellite), an assessment
error (over- or under-assessment of the tax bill, as a % of total tax liability), and an optional
informal payment ("bribe") that can reduce the recorded bill for a price.
Money enters as the utility numeraire so all preference parameters are
denominated in %-of-liability terms and comparable across respondents with
different tax liabilities.

**Moral-cost decomposition.** Split bribery aversion into two structural
parameters: `m0`, the moral cost of bribing a *correctly* assessed bill (pure
willingness to cheat), and `m1`, how much that moral cost of bribing decreases when the bill was wrongly over-assessed (we hypothesize that if the bill was wrongly over-assessed, citizens will feel wronged, and giving a bribe to bring the bill back to the correct amount will not feel like cheating; hence, a "corrective bribery" motive). This separates the people who won't cheat a fair
system from those who will pay to correct an unfair bill as distinct, independently
estimable traits, rather than a single conflated bribery-aversion score.

**Identification diagnostics and fix.** Using initial test runs and a pilot, I found that the framework's fully adaptive design rarely showed respondents the scenario needed to measure their intrinsic preference for automation: a satellite versus a bribe-free human, at the same final tax bill. Instead, most adaptive screens compared a bribe-free satellite against a bribing human, so a respondent's choice couldn't be cleanly attributed to liking automation versus simply disliking bribery, since both would produce the same answer. To fix this, I designed three fixed anchor screens, shown to every respondent before the adaptive options show. Each one is constructed so that, algebraically, two of the three preference terms in the choice model cancel out, leaving only the one parameter it's meant to isolate. I verified this by simulating the choice model directly and confirming each screen's predicted response moves only with its target parameter and stays flat with respect to the other two.

**Respondent-facing display logic.** Implemented rounding of on-screen
rupee amounts to the nearest 100 for display, while keeping the underlying
continuous design values used for estimation untouched, with derived
totals (e.g. bribe + reduced bill) computed from the already-rounded
components so every number a respondent sees is internally consistent.

**Field validation.** Iteratively validated the design end-to-end: verified
the likelihood function reproduces the on-screen numbers exactly, confirmed
each seed screen's isolation property numerically, and used pilot data to
recalibrate priors before full fielding.  

## Original framework

- Paper: Drake, Payró, Thakral & Tô (2025), *Bayesian Adaptive Choice Experiments*
- Original repository: `https://github.com/tt-econ/bace`

## License
AGPLv3
 
