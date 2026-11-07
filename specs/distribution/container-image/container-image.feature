@domain:distribution @area:container-image @from:carbon-region-picker/dockerfile
Feature: Running the tool from a container image
  Lets operators run carbon-region-picker without a local Python install, in an image that runs unprivileged and carries no local secrets.

  Background:
    Given the operator has built the carbon-region-picker container image from the repository

  @id:distribution.container-image.001 @rule:distribution.container-image.runs-cli-with-given-arguments @inferred @source:Dockerfile#ENTRYPOINT
  Scenario Outline: Running the image runs the CLI with the operator's arguments
    When the operator runs the image with the arguments "<arguments>"
    Then carbon-region-picker runs with exactly "<arguments>"
    And the CLI's output is what the container prints

    Examples:
      | arguments                     |
      | --near eu --max-latency-ms 60 |
      | --help                        |

  @id:distribution.container-image.002 @rule:distribution.container-image.runs-as-non-root @inferred @source:Dockerfile#USER
  Scenario: The container runs the tool as an unprivileged user
    When the operator runs the image
    Then the tool runs as user "app" with uid 10001
    And the tool does not run as root
