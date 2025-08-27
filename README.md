# Climate Data Pipeline Overview

## General information

### Getting started

Run `pip install -r requirements.txt` to install the required dependencies. If you're using Python 3, you can replace `pip` with `pip3`.

### Example calculation

A Google Doc with example calculations for the emissions in Skövde municipality can be found [here](https://docs.google.com/document/d/1MihysUkfunbV0LjwSUCiGSqWQSo5U03K0RMbRsVBL7U/edit#heading=h.oqnz3ereclbn). The calculations for each step are described in words (in Swedish) and, where possible, an explicit and simple calculation is presented. NOTE: The calculations are done for 2024 year's budget and the document is intended as method desciption for non-coders and people that are new to the source code. The document is open and editable and may therefore be updated over time.

### Data Sources

We obtain our information from multiple providers including SMHI, SCB, Trafa, and PowerCircle. Some of this information is stored directly in our repository, while other datasets are dynamically pulled from their original locations.

### Data Transformation

We utilize Python libraries such as Pandas and NumPy to perform various calculations on the collected data. This allows us to tailor the data into a format that is easier to understand and display on our website.

### Repository Structure

This repository contains both the datasets we host and the Python scripts for calculations.
 - `climate_data_calculations.py`: Execute this Python script to run all the calculations and generate updated data.
- `/output:` This is where the processed data gets saved.
    - `climate-data.json`: This JSON file serves as the core output, containing all the calculated climate data.
- `/tests:` Unit tests for data calculations. To run all tests:

    ```
    python3 -m unittest discover -s tests
    ```

    To run a specific test file:

    ```
    python3 -m unittest tests/{filename}.py
    ```

    where you replace *filename* with the name of the actual test file.
    
    If you notice any test failing, please submit a ticket about it.

### Performance profiling

Requires Graphwiz installed on the OS https://www.graphviz.org/download/
```sh
py.test tests --profile-svg && open prof/combined.svg
```

### How to Update Data on Site

To recalculate and refresh the site's data, execute the following command:

`python3 climate_data_calculations.py`

The results will be saved in the `/output` folder, primarily in the `climate-data.json` file.

#### Handling Data Inconsistencies for Municipalities

Given that Klimatkollen focuses on data related to municipalities, it's often necessary to standardize the naming conventions for Swedish municipalities as they can vary across different datasets. The following are known cases:

- Falun: also called Falu kommun.
- Gotland: also called Region Gotland or Region Gotland (kommun).
- Upplands Väsby: alternate spelling includes Upplands-Väsby.
- Stockholm: also called Stockholms stad.
- Malmö: also called Malmö stad.

In the list, the term appearing before the colon (:) is the standardized name that we use in the repository. Any alternative names listed after "also known as" should be converted to this standard version when incorporating new data sets.

## Detailed explanations

### Emission Calculations 

The folder `/kpis/emissions` contains files with functions to perform calculations related to CO2 emissions for municipalities, based on SMHI emission data and Carbon Law. Each function serves a specific purpose such as preprocessing data or future trends. Their order of execution is specified in `/kpis/emissions/emission_data_calculations.py`.

#### Constants 

The most important constants in the module are `CEMENT_DEDUCTION`, `LAST_YEAR_WITH_SMHI_DATA` and `CURRENT_YEAR` as they determine the baseline and scope of the calculations.

* `CEMENT_DEDUCTION`: Represents the total CO2 emissions from cement production in municipalities with cement plants that were operational in 2015 or later.
* `LAST_YEAR_WITH_SMHI_DATA`: Represents the last year for which the [National Emission database](https://nationellaemissionsdatabasen.smhi.se/) has data.
* `CURRENT_YEAR`: Represents the year which is to be handled as current year.

#### Functions

Here's a summary of what the functions do, in order of execution in `/kpis/emissions/emission_data_calculations.py`:

1. `get_n_prep_data_from_smhi`: Downloads data from SMHI and preprocess it into a pandas dataframe.

2. `deduct_cement`: Deducts cement emissions from specified municipalities.

3. `calculate_trend_coefficients`: Calculates linear trend coefficients for each municipailty based on SMHI data from 2015 onwards. This is done by fitting a straight line to the data using least square fit.

4. `calculate_approximated_historical`: Calculates approximated historical data values for years passed since the last year with SMHI data. This is done by interpolation using previously calculated linear trend coefficients.

5. `calculate_trend`: Calculates trend line for future years up to 2050. This is done by interpolation using previously calculated linear trend coefficients

6. `calculate_historical_change_percent`: Calculates the average historical yearly emission change in percent based on SMHI data from 2015 onwards.

7. `calculate_carbon_law_total`: Calculates total emissions from carbon law reduction path for municipalities.

## Contributing

The idea behind Klimatkollen is to give citizens access to the climate data we need to meet the goals of the Paris Agreement – and save our own future.

Do you have an idea for a feature you think should be added to the project? Before jumping into the code, it's a good idea to discuss your idea in the Discord server. That way you can find out if someone is already planning work in that area, or if your suggestion aligns with other people's thoughts. You can always submit an issue explaining your suggestion. We try to review the issues as soon as possible, but be aware that the team is at times very busy. Again, feel free to ask for a review on Discord!

Looking for ideas on what needs to be done? We appreciate help on existing issues very much. If you pick one up, remember to leave a comment saying you're working on it, and roughly when you expect to report progress. This helps others avoid double work and know what to expect.

Testing, bug fixes, typos or fact checking of our data is highly appreciated.

