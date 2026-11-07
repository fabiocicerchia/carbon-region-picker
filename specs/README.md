# Specifications of carbon-region-picker

What this code does, one atomic Gherkin scenario per behaviour, read from the code by code-atlas.
Tags: `@verified` a test asserts it · `@inferred` read from the code only · `@gap` an entry point no test covers · `@human` written or amended by a person, never rewritten.

## Command-line experience
How users invoke the tool and receive its results.

- **JSON output**: [Machine-readable ranking](command-line/json-output/json-output.feature) (2)
- **Options and validation**: [Refusing live-only options without live data](command-line/options-validation/live-only-options.feature) (1)
- **Table report**: [Reading the ranking report](command-line/table-report/ranking-report.feature) (4)

## Installation and distribution
Getting the tool onto a user's machine or into a container.

- **Container image**: [Running the tool from a container image](distribution/container-image/container-image.feature) (2)
- **One-line installer**: [Installing with the one-line installer](distribution/one-line-installer/one-line-installer.feature) (2)

## Documentation site
The look and feel of the project's published documentation.

- **Theme and palette**: [Presenting the documentation in the project's own palette](documentation-site/theme-palette/docs-look-and-feel.feature) (4)

## Latency constraints
Keeping recommendations within an acceptable network distance of the user.

- **Latency cap**: [Constraining regions by latency](latency/latency-cap/latency-cap.feature) (2)
- **Live latency probing**: [Probing real latency to regions](latency/live-probing/live-latency-probing.feature) (2)

## Live grid data
Using Electricity Maps for real-time and forecast carbon intensity instead of bundled averages.

- **API credentials**: [Supplying the Electricity Maps token](live-grid-data/api-credentials/em-token.feature) (2)
- **Cleanest-hour forecast**: [Suggesting the cleanest hour to run](live-grid-data/cleanest-hour-forecast/cleanest-hour.feature) (2)
- **Real-time intensity**: [Ranking on live grid intensity](live-grid-data/real-time-intensity/live-grid-intensity.feature) (4)

## Region ranking
Ordering a cloud provider's regions from cleanest to dirtiest grid under the user's constraints.

- **Carbon ordering**: [Ranking cloud regions by grid carbon intensity](region-ranking/carbon-ordering/ranking-regions-by-carbon.feature) (2)
