@domain:live-grid-data @area:real-time-intensity @from:carbon-region-picker/carbon-region-picker
Feature: Ranking on live grid intensity
  Serves engineers who want today's grid rather than a yearly average, by pulling current intensities from Electricity Maps.

  Background:
    Given Given the operator has a valid Electricity Maps token
    And And asks for live data

  @id:live-grid-data.real-time-intensity.001 @rule:live-grid-data.real-time-intensity.live-replaces-bundled @verified @source:carbon_region_picker.py#rank @test:tests/test_carbon_region_picker.py#test_live_overrides_bundled_values
  Scenario: A zone's live intensity replaces its bundled average in the ranking
    Given Electricity Maps reports 90 gCO2e/kWh for zone DE
    When the operator ranks aws regions near eu
    Then eu-central-1 is listed at 90.0 gCO2e/kWh
    And eu-central-1 is marked 🌱
    And the order reflects the live value

  @id:live-grid-data.real-time-intensity.002 @rule:live-grid-data.real-time-intensity.fallback-to-bundled @verified @source:carbon_region_picker.py#fetch_live @test:tests/test_carbon_region_picker.py#test_live_ignores_unknown_zone @questionable
  Scenario Outline: Zones without a live answer silently keep their bundled average
    Given Electricity Maps <answer> for zone <zone>
    When the operator ranks aws regions near eu
    Then <region> is listed at its bundled <bundled> gCO2e/kWh
    And nothing in the output says the value is not live

    Examples:
      | answer               | zone  | region     | bundled |
      | refuses the request  | US-OR | us-west-2  | 120.0   |
      | returns no intensity | IN-WE | ap-south-1 | 650.0   |

  @id:live-grid-data.real-time-intensity.003 @rule:live-grid-data.marginal-intensity.rank-by-marginal @verified @source:carbon_region_picker.py#fetch_live @test:tests/test_carbon_region_picker.py#test_fetch_live_marginal_hits_marginal_endpoint
  Scenario: Ranking can use marginal instead of average live intensity
    Given Electricity Maps reports a marginal intensity of 42 gCO2e/kWh for zone SE
    When the operator ranks aws regions near eu using marginal intensity
    Then eu-north-1 is listed at 42.0 gCO2e/kWh

  @id:live-grid-data.real-time-intensity.004 @rule:live-grid-data.real-time-intensity.unreachable-service-crashes @inferred @source:carbon_region_picker.py#_em_get @questionable
  Scenario: An unreachable Electricity Maps service aborts the run
    Given Electricity Maps cannot be reached over the network
    When the operator ranks aws regions near eu
    Then the tool prints a Python traceback
    And it exits with a non-zero status
    And no ranking is printed
