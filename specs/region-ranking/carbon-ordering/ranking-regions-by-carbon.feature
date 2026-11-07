@domain:region-ranking @area:carbon-ordering @from:carbon-region-picker/carbon-region-picker
Feature: Ranking cloud regions by grid carbon intensity
  Serves engineers choosing where to deploy, by listing a provider's regions from the cleanest grid to the dirtiest.

  Background:
    Giventhe bundled yearly-average grid intensities are in use

  @id:region-ranking.carbon-ordering.001 @rule:region-ranking.carbon-ordering.cleanest-first @verified @source:carbon_region_picker.py#rank @test:tests/test_carbon_region_picker.py#test_rank_sorts_by_intensity @test:tests/test_carbon_region_picker.py#test_gcp_and_azure_region_sets
  Scenario Outline: Regions are listed from cleanest to dirtiest grid
    Given no latency cap is set
    When the operator ranks regions for provider <provider>
    Then every one of the <count> bundled <provider> regions is listed
    And the regions are listed in ascending gCO2e/kWh
    And the first region is <cleanest> at <intensity> gCO2e/kWh

    Examples:
      | provider | count | cleanest      | intensity |
      | aws      | 9     | eu-north-1    | 25.0      |
      | gcp      | 7     | us-west1      | 90.0      |
      | azure    | 7     | westus2       | 90.0      |

  @id:region-ranking.carbon-ordering.002 @rule:command-line.options-validation.provider-choices @verified @source:carbon_region_picker.py#build_parser @test:tests/test_carbon_region_picker.py#test_unknown_provider_rejected
  Scenario Outline: Only supported providers, vantage points and whole-number latency caps are accepted
    When the operator runs the tool with <option> <value>
    Then the tool prints a usage error saying "<error>"
    And it exits with status 2
    And no ranking is printed

    Examples:
      | option           | value | error             |
      | --provider       | oci   | invalid choice    |
      | --near           | apac  | invalid choice    |
      | --max-latency-ms | fast  | invalid int value |
