# Bayesian Adaptive Choice Experiments (BACE)

*Acknowledgment: Support from NSF grants SES-2149414 and SES-2149371 is gratefully acknowledged.*

## Introduction

This package helps researchers implement and run their own Bayesian Adaptive Choice Experiment (BACE). BACE allows researchers to elicit preferences quickly and efficiently using a dynamic experimental framework. Researchers specify a model that they want to estimate, prior beliefs over the model's parameters, and questions (or "designs") that can be shown to respondents. 

At each stage, BACE selects the maximally informative question according to the mutual information criterion. This question is shown to a survey respondent. Based on the respondent's answer, the posterior likelihood of the individual's preference parameters is updated using Bayes' rule and Monte Carlo techniques. After incorporating this new information, the next question is chosen, and the process repeats.

![BACE steps](https://linh.to/files/misc/bace_steps.png)

Computing the most informative question in real-time is computationally intensive. BACE helps you set up a back-end server to handle computation remotely, allowing BACE to handle many questions and respondents at once and scale to situations where respondents may have poor computing resources. You can then set up your favorite front-end survey interface (e.g. Qualtrics or SurveyMonkey) to query your BACE application, display designs to survey respondents, and record individuals' responses.

## Outline of Wiki

For more information on how to set up and run your own BACE application, please see the [BACE WiKi](https://github.com/tt-econ/bace/wiki).

Section 2 walks through an example of how BACE might be used and configured. Within the context of a simple discrete choice example, this section describes how to think through the key model components that a user must specify. Users new to adaptive experimentation can read through this section to understand how a researcher can model a discrete choice experiment using a set of questions or `designs`, prior beliefs over model parameters `thetas`, and a likelihood function that governs how individuals make choices `likelihood_pdf`.

Section 3 provides a walkthrough of how to set up your own BACE application.

* 3a) Clone and Deploy Application - This section describes how to clone BACE from GitHub and deploy your BACE application to a Heroku server. 
* 3b) Configure BACE - This section describes the key model components that must be changed in order to set up BACE for your specific experiment.
* 3c) Querying Your Application - This section describes how to perform simple API queries to your application.
* 3d) Perform Simulations - This section describes how to run a simulated experiment.
* 3e) Deploying at Scale - This section describes issues to consider prior to deploying at scale. In particular, we discuss how to manage computational power through the number and type of dynos and perform load testing ahead of a full-scale experiment.
* 3f) Managing Heroku Postgres - This section describes how to manage Heroku Postgres, the database that will record information for users. In particular, we discuss how to think through choosing a Postgres tier and how to change tiers ahead of a full-scale survey if more storage is needed.

Section 4 walks through setting up a survey in Qualtrics that queries your BACE application. 

## References

### Methodology

Drake, Payró, Thakral, and Tô (2022): Bayesian Adaptive Choice Experiments.

### Applications

Drake, Thakral, and Tô (2022): Wage Differentials and the Price of Workplace Flexibility.
