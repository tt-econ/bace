# Bayesian Adaptive Choice Experiments (BACE)

*Acknowledgment: Support from NSF grants SES-2149414 and SES-2149371 is gratefully acknowledged.*

<p align="center">
  <img src="/misc/bace_logo.png" width="720">
</p>

Reference: Bayesian Adaptive Choice Experiments, 2023 (Drake, Payró, Thakral, and Tô).

## Introduction

This package helps researchers implement and run their own Bayesian Adaptive Choice Experiment (BACE). BACE allows researchers to elicit preferences quickly and efficiently using a dynamic experimental framework. Researchers specify a model that they want to estimate, prior beliefs over the model's parameters, and questions (or "designs") that can be shown to respondents.

At each stage, BACE selects the maximally informative question according to the mutual information criterion. This question is shown to a survey respondent. Based on the respondent's answer, the posterior likelihood of the individual's preference parameters is updated using Bayes' rule and Monte Carlo techniques. After incorporating this new information, the next question is chosen, and the process repeats.

![BACE steps](/misc/bace_steps.png)

Computing the most informative question in real-time is computationally intensive. BACE helps you set up a back-end server to handle computation remotely, allowing BACE to handle many questions and respondents at once and scale to situations where respondents may have poor computing resources. You can then set up your favorite front-end survey interface (e.g., Qualtrics, SurveyMonkey, or SurveyCTO) to query your BACE application, display designs to survey respondents, and record individuals' responses.

## Requirements

1. Install [Python 3.9 or greater](https://www.python.org/downloads/).
2. Complete the [AWS Serverless Application Model (SAM) Prerequisites](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/prerequisites.html). Note: When creating an access key (Step 3), you should select the box that says "I understand creating a root user access key is not a best practice, but I still want to create one".
3. Install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). This page has instructions for Linux, macOS, and Windows distributions.
4. [Install Docker to use with AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-docker.html).

Interested users can follow the [tutorial for deploying a Hello World application](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html) to become familiar with the interface.

### Install Python Requirements (Local Testing)

To run simulations and test the application locally, you must install the required Python packages on your local computer. We recommend creating a virtual environment prior to installing `requirements.txt`. A virtual environment is not required but is useful for managing different versions of Python packages. Follow the instructions for [installing and using pip and virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) to do so.

Install requirements locally. This step may take a few minutes.

```sh
python -m pip install -r requirements.txt
```

## Create a BACE Application: A Summary

### Initialize SAM (Serverless Application Model) using the BACE template

To initialize navigate to the folder that you plan to store information on your computer.

Initialize a new application, run `sam init`.

Select `2 - Custom Template Location` and paste the URL for the BACE git repo: `https://github.com/tt-econ/bace.git`.

Open the folder in VS Code (`code .`) or your preferred code editor.

```
sam init

You can preselect a particular runtime or package type when using the `sam init` experience.
Call `sam init --help` to learn more.

Which template source would you like to use?
        1 - AWS Quick Start Templates
        2 - Custom Template Location
Choice: 2

Template location (git, mercurial, http(s), zip, path): https://github.com/tt-econ/bace.git

```

### Build and Deploy Application

From the root of your project directory, run `sam build` to create a Docker container that houses your application. Make sure that Docker is running on your computer.

Next, run `sam deploy --guided` to deploy your application to AWS.

The following provides example output. Please note that, when prompted, you should indicate that it is okay ('y') that the BaceFunction may not have authorization defined.

```
sam deploy --guided

Configuring SAM deploy
======================

        Looking for config file [samconfig.toml] :  Found
        Reading default arguments  :  Success

        Setting default arguments for 'sam deploy'
        =========================================
        Stack Name [sam-app]: ENTER
        AWS Region [us-east-2]: ENTER
        #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
        Confirm changes before deploy [Y/n]: ENTER
        #SAM needs permission to be able to create roles to connect to the resources in your template
        Allow SAM CLI IAM role creation [Y/n]: ENTER
        #Preserves the state of previously provisioned resources when an operation fails
        Disable rollback [y/N]: ENTER
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        BaceFunction may not have authorization defined, Is this okay? [y/N]: y
        Save arguments to configuration file [Y/n]: ENTER
        SAM configuration file [samconfig.toml]: ENTER
        SAM configuration environment [default]: ENTER
```

This process may take a few moments. You will see the URL that you can use to access your application once the process completes.

### Update Application

The above steps start up an application using the provided template in this repo `https://github.com/tt-econ/bace.git` which implements a simple choice experiment example, explained in the package's [Wiki](https://github.com/tt-econ/bace/wiki).

You will then make changes to your application based on your specific choice experiment. Further instructions are in the package's [Wiki](https://github.com/tt-econ/bace/wiki).

After making changes to your application locally, you need to deploy these changes so that your API is updated. To update your application, run `sam build` and then run `sam deploy`. (You only need to run `sam deploy --guided` when you are creating the initial application.)

## Further Detailed Instructions from the Wiki

For more detailed instructions, BACE users are referred to the package's [Wiki](https://github.com/tt-econ/bace/wiki).

The [Wiki](https://github.com/tt-econ/bace/wiki) covers the following sections:

- Section 1 walks through an example of how BACE might be used and configured. This is also the example used in the initial setup of the application.
- Section 2 explains how to set up your own BACE application which goes through the above steps in more detail.
- Section 3 explains how to deploy your BACE application at scale and collect experimental output data.
- Section 4 provides instructions for front-end integration (front-end surveys on Qualtrics and other similar platforms) to query and display information from the back-end server API.
- Section 5 includes helpful commands, answers common questions, provides development roadmap, references, and a list of applications.

***
We welcome any comments about the [Wiki](https://github.com/tt-econ/bace/wiki), the package, or interests in contributing to further [develop the package](https://github.com/tt-econ/bace/wiki/5c.-Development-Roadmap). Please contact:
- Marshall Drake (mhdrake@bu.edu)
- [Linh Tô](https://linh.to) (linhto@bu.edu)
- [Neil Thakral](https://neilthakral.github.io/) (neil_thakral@brown.edu)
- [Fernando Payró](https://sites.google.com/site/ferpayrochew/home) (fernando.payro@bse.eu)

Please also contact us if you use BACE to be listed in the List of Applications.
